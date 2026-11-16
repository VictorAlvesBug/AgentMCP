# Agent MCP

Servidores [MCP (Model Context Protocol)](https://modelcontextprotocol.io) em Python, construídos com o SDK oficial `mcp` (versão 2.x).

| Servidor | Arquivo | O que faz |
| --- | --- | --- |
| Meu Servidor MCP | `mcp-servers/my_first_mcp_server.py` | Exemplo mínimo com uma ferramenta que retorna `"Olá, mundo!"` |
| Supabase MCP Server | `mcp-servers/supabase_mcp_server.py` | CRUD em tabelas de um projeto [Supabase](https://supabase.com) |

## Estrutura

```
Agent MCP/
├── mcp-servers/
│   ├── my_first_mcp_server.py    # Servidor de exemplo
│   ├── supabase_mcp_server.py    # Servidor de CRUD no Supabase
│   ├── requirements.txt          # Dependências Python
│   └── .env                      # Credenciais do Supabase (não versionado)
└── README.md
```

## Pré-requisitos

- [Python](https://www.python.org/downloads/) 3.10 ou superior
- [Node.js](https://nodejs.org/), necessário para o MCP Inspector (aberto pelo `mcp dev` via `npx`)
- Um projeto no [Supabase](https://supabase.com), apenas para o servidor do Supabase

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
   python -m pip install -r .\mcp-servers\requirements.txt
   ```

   Isso instala o `mcp[cli]` (que fornece o comando `mcp`), o `uv` (usado pelo `mcp dev` para executar o servidor), o `supabase` e o `python-dotenv`.

   Prefira `python -m pip` a `pip`: assim a instalação vai garantidamente para o `.venv`, mesmo que o `pip` do terminal aponte para o Python global.

## Configuração do Supabase

Crie o arquivo `mcp-servers/.env` com as credenciais do projeto, encontradas em **Project Settings > API** no painel do Supabase:

```
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_KEY=sua-chave-aqui
```

Sobre a chave:

- **`service_role` / `secret`**: ignora o Row Level Security (RLS) e tem acesso total ao banco. Prática para testes locais; nunca a versione nem a exponha.
- **`anon` / `publishable`**: respeita o RLS. Tabelas com RLS ativado e sem políticas retornam listas vazias e recusam escritas.

### Criando uma tabela para teste

O servidor não cria tabelas. Crie-as pelo **Table Editor** ou pelo **SQL Editor** do Supabase, por exemplo:

```sql
create table public.clientes (
  id bigint generated always as identity primary key,
  nome text not null,
  email text,
  ativo boolean default true,
  criado_em timestamptz default now()
);

insert into public.clientes (nome, email) values
  ('Ana', 'ana@email.com'),
  ('Bruno', 'bruno@email.com');
```

## Como rodar

Com o ambiente virtual ativado:

### Modo de desenvolvimento (com MCP Inspector)

```powershell
mcp dev .\mcp-servers\supabase_mcp_server.py
```

Troque o arquivo por `.\mcp-servers\my_first_mcp_server.py` para rodar o servidor de exemplo.

Na primeira execução, o `npx` pede confirmação para instalar o `@modelcontextprotocol/inspector`; responda `y`. O Inspector abre no navegador (por padrão em `http://127.0.0.1:6274`), onde é possível listar e testar as ferramentas, recursos e prompts do servidor.

Para encerrar, pressione `Ctrl+C` no terminal.

### Execução direta (stdio)

```powershell
python .\mcp-servers\supabase_mcp_server.py
```

Nesse modo o servidor se comunica por entrada/saída padrão e fica aguardando um cliente MCP; nada é exibido no terminal.

## Servidor do Supabase

### Ferramentas

Todas as ferramentas usam filtros de igualdade combinados com AND, no formato `{"coluna": valor}`. Em caso de falha, retornam `{"erro": "<tipo>: <mensagem>"}` em vez de interromper a chamada.

| Ferramenta | Operação | Parâmetros | Exemplo |
| --- | --- | --- | --- |
| `get_from_table` | Read | `table`, `filter` | `{"table": "clientes", "filter": {}}` |
| `insert_into_table` | Create | `table`, `data` (lista de registros) | `{"table": "clientes", "data": [{"nome": "Carla"}]}` |
| `update_in_table` | Update | `table`, `filter`, `data` | `{"table": "clientes", "filter": {"id": 1}, "data": {"ativo": false}}` |
| `delete_from_table` | Delete | `table`, `filter` | `{"table": "clientes", "filter": {"id": 1}}` |

Em `get_from_table`, o filtro `{}` retorna todos os registros. Em `update_in_table` e `delete_from_table`, um filtro vazio afetaria a tabela inteira; prefira sempre filtrar pela chave primária.

### Recurso

- `config://app`: metadados do servidor (nome, versão, descrição e autor).

### Prompt

- `simple_echo(message)`: pede ao modelo que repita exatamente a mensagem recebida.

## Adicionando novas ferramentas

Basta decorar uma função com `@mcp.tool()`. A docstring vira a descrição da ferramenta, e as anotações de tipo definem os parâmetros:

```python
@mcp.tool()
def somar(a: int, b: int) -> int:
    """Soma dois números inteiros"""
    return a + b
```

Da mesma forma, `@mcp.resource("esquema://caminho")` expõe um recurso e `@mcp.prompt()` expõe um prompt.

## Problemas comuns

- **`mcp` não é reconhecido como comando**: o ambiente virtual não está ativado ou as dependências não foram instaladas. Refaça os passos 2 e 3 da instalação.
- **`No module named 'supabase'`**: as dependências foram instaladas no Python global, não no `.venv`. Rode `python -m pip install -r .\mcp-servers\requirements.txt` com o ambiente ativado.
- **`No module named 'mcp.server.fastmcp'`**: código escrito para o SDK 1.x. Na versão 2, use `from mcp.server.mcpserver import MCPServer` no lugar de `FastMCP`, ou fixe `mcp[cli]<2` no `requirements.txt`.
- **Consultas retornam lista vazia**: a tabela está vazia ou o RLS está bloqueando o acesso (comum com a chave `anon`).
- **Instalação muito lenta no Windows**: o Windows Defender verifica cada arquivo instalado. Adicionar a pasta do projeto às exclusões do Defender acelera bastante.
