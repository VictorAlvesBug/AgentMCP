import asyncio
import colorama
from helpers.cli_helpers import info, warning, error, success

from message_agent.agents import create_agent

async def main():
    agent = create_agent()
    print(info(f"Iniciando LLM {agent.who_am_i()} e conectando aos servidores MCP...\n"))
    await agent.initialize()

    print(info("Ferramentas disponíveis:"))
    for name in agent.hub.routes:
        print(f"- {name}")
    print(info("\nDigite 'sair' para encerrar.\n"))

    try:
        while True:
            text = (await asyncio.to_thread(input, success("Você: "))).strip()
            if not text:
                continue
            if text.lower() == "sair":
                break
            
            try:
                response = await agent.answer("terminal", text)
            except Exception as e:
                response = f"[Erro] {type(e).__name__}: {e}"
            print(f"{warning('BugChatAI:')}{response}\n")
    finally:
        await agent.terminate()

if __name__ == "__main__":
    asyncio.run(main())