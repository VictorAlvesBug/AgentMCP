from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Meu Servidor MCP")

@mcp.tool()
def minha_primeira_ferramenta_mcp() -> str:
    """Ferramenta de teste que retorna uma saudação fixa.

    Não recebe parâmetros. Use para verificar se o servidor MCP está
    respondendo corretamente.

    Retorna: o texto "Olá, mundo!".
    """
    return "Olá, mundo!"

#mcp.register("minha_primeira_ferramenta_mcp", minha_primeira_ferramenta_mcp)

if __name__ == "__main__":
    mcp.run()