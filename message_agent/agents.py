# Bibliotecas padrão
from message_agent import config
from message_agent.memory import Memory
from contextlib import AsyncExitStack
from mcp import ClientSession, stdio_client
from mcp import types as mcp_types
from abc import ABC, abstractmethod
import json
from helpers.cli_helpers import warning

# Google Gemini
from google import genai
from google.genai import types as genai_types

# Groq
import os
from openai import AsyncOpenAI

# Como funciona uma chamada de ferramenta?
# 1. Eu pergunto: "Quais são as minhas notas?"
# 2. O modelo não responde com texto. Ele responde: "quero chamar a ferramenta supabase__get_notes com os argumentos {}".
# 3. O código executa a ferramenta pelo McpHub e devolve o resultado ao modelo.
# 4. O modelo lê o resultado e agora sim escreve a resposta em texto.
# OBS.: Os passos 2 e 3 podem se repetir várias vezes, o que limita essa quantidade de vezes é o MAX_ITERATIONS.

SEPARATOR = "__"

class McpHub:
    def __init__(self, servers):
        self.servers = servers
        self.stack = AsyncExitStack()
        self.routes = {}
        self.tools = []

    async def connect(self):
        for prefix, parameters in self.servers.items():
            reader, writer = await self.stack.enter_async_context(stdio_client(parameters))
            session = await self.stack.enter_async_context(ClientSession(reader, writer))
            await session.initialize()

            result = await session.list_tools()
            for tool in result.tools:
                name = f"{prefix}{SEPARATOR}{tool.name}"
                self.routes[name] = (session, tool.name)
                self.tools.append({
                    "name": name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                })

    async def call(self, name, arguments):
        if name not in self.routes:
            return {"error": f"Ferramenta {name} não encontrada"}
        
        session, original_name = self.routes[name]

        try:
            result = await session.call_tool(original_name, arguments)
        except Exception as e:
            return {"error": f"Erro ao chamar a ferramenta {original_name}: ({type(e).__name__}) {e}"}
        
        if result.structured_content is not None:
            content = result.structured_content
        else:
            texts = [block.text for block in result.content if isinstance(block, mcp_types.TextContent)]
            content = "\n".join(texts)

        if result.is_error:
            return {"error": content}

        return {"result": content}

    async def close(self):
        await self.stack.aclose()


class BaseAgent(ABC):
    def __init__(self):
        self.hub = McpHub(config.MCP_SERVERS)
        self.memory = Memory(is_user_message=self.is_user_message, max_history_messages=config.MAX_HISTORY_MESSAGES)

    async def initialize(self):
        await self.hub.connect()

    async def terminate(self):
        await self.hub.close()

    @abstractmethod
    async def answer(self, chat_id, text):
        pass

    @abstractmethod
    def is_user_message(self, message):
        pass

    @abstractmethod
    def who_am_i(self):
        pass


class GeminiAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.client = genai.Client(
            http_options=genai_types.HttpOptions(timeout=30_000) # 30 segundos
        )

    async def answer(self, chat_id, text):
        history = self.memory.get_conversation(chat_id)
        history.append(genai_types.Content(role="user", parts=[genai_types.Part.from_text(text=text)]))

        configuration = genai_types.GenerateContentConfig(
            system_instruction=config.SYSTEM_PROMPT,
            tools=self.gemini_tools(),
        )

        for _ in range(config.MAX_ITERATIONS):
            response = await self.client.aio.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=history,
                config=configuration,
            )
            history.append(response.candidates[0].content)

            if not response.function_calls:
                self.memory.trim_conversation(chat_id)
                return response.text or "(sem resposta)"

            parts = []
            for call in response.function_calls:
                arguments = dict(call.args or {})
                print(f"[ferramenta] {call.name} com os argumentos: {arguments}")
                result = await self.hub.call(call.name, arguments)
                parts.append(genai_types.Part.from_function_response(name=call.name, response=result))

            history.append(genai_types.Content(role="user", parts=parts))

        return "Desculpe, não consegui concluir sua solicitação (limite de etapas atingido)"

    def is_user_message(self, message):
        return message.role == "user" and any(part.text for part in message.parts or [])
    
    def gemini_tools(self):
        declarations = []
        for tool in self.hub.tools:
            declarations.append(
                genai_types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters_json_schema=tool["parameters"],
                )
            )
        return [genai_types.Tool(function_declarations=declarations)]
    
    def who_am_i(self):
        return "GeminiAgent"

class GroqAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=config.GROQ_BASE_URL,
            timeout=30, # 30 segundos
        )

    async def answer(self, chat_id, text):
        history = self.memory.get_conversation(chat_id)
        history.append({"role": "user", "content": text})

        for _ in range(config.MAX_ITERATIONS):
            messages = [{"role": "system", "content": config.SYSTEM_PROMPT}] + history

            response = await self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=messages,
                tools=self.groq_tools(),
            )

            message = response.choices[0].message

            if not message.tool_calls:
                history.append({"role": "assistant", "content": message.content})
                self.memory.trim_conversation(chat_id)
                return message.content or "(sem resposta)"

            history.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            })

            for call in message.tool_calls:
                arguments = json.loads(call.function.arguments or "{}")
                print(f"[ferramenta] {call.function.name} com os argumentos: {arguments}")
                result = await self.hub.call(call.function.name, arguments)
                history.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
        
        return "Desculpe, não consegui concluir sua solicitação (limite de etapas atingido)"

    def is_user_message(self, message):
        return message["role"] == "user"

    def groq_tools(self):
        declarations = []
        for tool in self.hub.tools:
            declarations.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                }
            })
        return declarations
    
    def who_am_i(self):
        return "GroqAgent"

def create_agent():
    if config.PROVIDER == "gemini":
        return GeminiAgent()
    
    if config.PROVIDER == "groq":
        return GroqAgent()
    
    raise ValueError(f"Provider {config.PROVIDER} não suportado. Use 'gemini' ou 'groq'.")