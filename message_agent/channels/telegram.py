import asyncio
import httpx
from helpers.cli_helpers import info, warning, error, success

from message_agent import config
from message_agent.agents import create_agent

# O tamanho máximo de uma mensagem no Telegram é de 4096 caracteres
MAX_MESSAGE_LENGTH = 4000

def api_url(method: str):
    return f"{config.TELEGRAM_BASE_URL}{config.TELEGRAM_BOT_TOKEN}/{method}"

async def call_api(client, method, **payload):
    response = await client.post(api_url(method), json=payload)
    data = response.json()
    if not data.get("ok"):
        description = data.get("description") or f"HTTP {response.status_code}"
        raise RuntimeError(description)
    return data.get("result")

async def send_message(client, chat_id, text):
    if not text:
        text = "(sem resposta)"
    for start in range(0, len(text), MAX_MESSAGE_LENGTH):
        piece = text[start:start + MAX_MESSAGE_LENGTH]
        await call_api(client, "sendMessage", chat_id=chat_id, text=piece)

async def main():
    if not config.TELEGRAM_BOT_TOKEN:
        print(error("Erro: TELEGRAM_BOT_TOKEN não configurado no arquivo message_agent/.env"))
        return
    
    agent = create_agent()
    print(info(f"Iniciando LLM {agent.who_am_i()} e conectando aos servidores MCP...\n"))
    await agent.initialize()

    print(info("Ferramentas disponíveis:"))
    for name in agent.hub.routes:
        print(f"- {name}")
    print(info("\nBot ligado. Mande uma mensagem no Telegram. Ctrl+C para encerrar.\n"))

    # O getUpdates espera até 30s. O cliente HTTO precisa aguentar um pouco mais.
    timeout = httpx.Timeout(40.0, connect=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            me = await call_api(client, "getMe")
            print(info(f"Bot conectado como {me.get('username', 'bot')}.\n"))

            offset = None

            while True:
                payload = {"timeout": 30, "allowed_updates": ["message"]}
                if offset is not None:
                    payload["offset"] = offset

                updates = await call_api(client, "getUpdates", **payload)

                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message") or {}
                    chat = message.get("chat") or {}
                    chat_id = chat.get("id")
                    text = (message.get("text") or "").strip()

                    if chat_id is None or not text:
                        continue

                    sender = (message.get("from") or {}).get("first_name") or "(anônimo)"
                    print(f"{success(sender + ':')} {text}")

                    try: 
                        reply = await agent.answer(str(chat_id), text)
                    except Exception as exc:
                        reply = f"[Erro] {type(exc).__name__}: {exc}"

                    print(f"{warning('BugChatAI:')} {reply}\n")
                    await send_message(client, chat_id, reply)
    finally:
        await agent.terminate()

if __name__ == "__main__":
    asyncio.run(main())