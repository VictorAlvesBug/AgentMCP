import asyncio

from message_agent.agents import GeminiAgent

async def main():
    agent = GeminiAgent()
    print("Conectando aos servidores MCP...")
    await agent.initialize()

    print("Ferramentas disponíveis:")
    for name in agent.hub.routes:
        print(f"- {name}")
    print("Digite 'sair' para encerrar.\n")

    try:
        while True:
            text = (await asyncio.to_thread(input, "Você: ")).strip()
            if not text:
                continue
            if text.lower() == "sair":
                break
            
            try:
                response = await agent.answer("terminal", text)
            except Exception as e:
                response = f"[Erro] {type(e).__name__}: {e}"
            print(f"BugChatAI: {response}\n")
    finally:
        await agent.terminate()

if __name__ == "__main__":
    asyncio.run(main())