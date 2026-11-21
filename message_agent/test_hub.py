import asyncio

from message_agent import config
from message_agent.agents import McpHub

async def main():
    hub = McpHub(config.MCP_SERVERS)
    await hub.connect()
    print("Tools available:", list(hub.routes))
    print(await hub.call("supabase__insert_note", {"title": "Testando via MCP Hub"}))
    print(await hub.call("supabase__get_notes", {}))
    await hub.close()

asyncio.run(main())