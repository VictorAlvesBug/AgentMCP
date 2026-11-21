from message_agent.memory import Memory

from contextlib import AsyncExitStack

from google import genai
from google.genai import types as genai_types
from mcp import ClientSession, stdio_client
from mcp import types as mcp_types

from message_agent import config

from abc import ABC, abstractmethod

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
        self.memory = Memory(config.MAX_HISTORY_MESSAGES)

    async def initialize(self):
        await self.hub.connect()

    async def terminate(self):
        await self.hub.close()

    @abstractmethod
    async def answer(self, chat_id, text):
        pass


class GeminiAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.client = genai.Client(http_options=genai_types.HttpOptions(timeout=30_000))
    
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