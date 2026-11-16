from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Meu Servidor MCP")

@mcp.tool()
def minha_primeira_ferramenta_mcp() -> str:
    """Essa é a descrição da minha primeira ferramenta MCP"""
    return "Olá, mundo!"

#mcp.register("minha_primeira_ferramenta_mcp", minha_primeira_ferramenta_mcp)

if __name__ == "__main__":
    mcp.run()