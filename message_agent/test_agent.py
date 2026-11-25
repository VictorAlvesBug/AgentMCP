import asyncio

from message_agent.agents import create_agent


async def main():
    agent = create_agent()
    await agent.initialize()

    print("supabase__get_notes:")
    print(await agent.call_visible_tool("supabase__get_notes", {}))
    
    print("notion__API-delete-a-block:")
    print(await agent.call_visible_tool("notion__API-delete-a-block", {}))
    
    await agent.terminate()


asyncio.run(main())