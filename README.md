# Agent MCP

Servidor [MCP (Model Context Protocol)](https://modelcontextprotocol.io) em Python, construído com o SDK oficial `mcp` (versão 2.x).

O servidor expõe a ferramenta `minha_primeira_ferramenta_mcp`, que retorna `"Olá, mundo!"`.

## Estrutura

```
Agent MCP/
├── mcp-servers/
│   ├── mcp_server.py      # Servidor MCP e suas ferramentas
│   └── requirements.txt   # Dependências Python
└── README.md
```

## Pré-requisitos

- [Python](https://www.python.org/downloads/) 3.10 ou superior
- [Node.js](https://nodejs.org/), necessário para o MCP Inspector (aberto pelo `mcp dev` via `npx`)

## Instalação

Os comandos abaixo são para PowerShell (Windows) e devem ser executados na raiz do projeto.

1. Crie o ambiente virtual:

   ```powershell
   python -m venv .venv
   ```

2. Ative o ambiente virtual:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   O prompt passa a começar com `(.venv)`. Se o PowerShell bloquear o script por política de execução, rode uma vez:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

3. Instale as dependências:

   ```powershell
   pip install -r .\mcp-servers\requirements.txt
   ```

   Isso instala o `mcp[cli]`, que fornece o comando `mcp`, e o `uv`, usado pelo `mcp dev` para executar o servidor.

## Como rodar

Com o ambiente virtual ativado:

### Modo de desenvolvimento (com MCP Inspector)

```powershell
mcp dev .\mcp-servers\mcp_server.py
```

Na primeira execução, o `npx` pede confirmação para instalar o `@modelcontextprotocol/inspector`; responda `y`. O Inspector abre no navegador (por padrão em `http://127.0.0.1:6274`), onde é possível listar e testar as ferramentas do servidor.

Para encerrar, pressione `Ctrl+C` no terminal.

### Execução direta (stdio)

```powershell
python .\mcp-servers\mcp_server.py
```

Nesse modo o servidor se comunica por entrada/saída padrão e fica aguardando um cliente MCP; nada é exibido no terminal.

## Adicionando novas ferramentas

Basta decorar uma função com `@mcp.tool()` em `mcp-servers/mcp_server.py`. A docstring vira a descrição da ferramenta, e as anotações de tipo definem os parâmetros:

```python
@mcp.tool()
def somar(a: int, b: int) -> int:
    """Soma dois números inteiros"""
    return a + b
```

## Problemas comuns

- **`mcp` não é reconhecido como comando**: o ambiente virtual não está ativado ou as dependências não foram instaladas. Refaça os passos 2 e 3 da instalação.
- **`No module named 'mcp.server.fastmcp'`**: código escrito para o SDK 1.x. Na versão 2, use `from mcp.server.mcpserver import MCPServer` no lugar de `FastMCP`, ou fixe `mcp[cli]<2` no `requirements.txt`.
- **Instalação muito lenta no Windows**: o Windows Defender verifica cada arquivo instalado. Adicionar a pasta do projeto às exclusões do Defender acelera bastante.
