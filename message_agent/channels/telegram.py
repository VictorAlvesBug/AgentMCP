import asyncio
import httpx
from helpers.cli_helpers import info, warning, error, success
from mcp_servers.supabase_tools.telegram_users_type import TelegramUser
from message_agent import config
from message_agent.agents import create_agent

# O tamanho máximo de uma mensagem no Telegram é de 4096 caracteres
MAX_MESSAGE_LENGTH = 4000

ADMIN_COMMANDS = { "/grant_access", "/revoke_access", "/list_access" }

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

def unwrap_response(response: dict) -> dict | list | None:
    if isinstance(response, dict) and "result" in response and isinstance(response["result"], dict) and "result" in response["result"]:
        return response["result"]["result"]
    return None

async def check_access(agent, user_id):
    try:
        if user_id == config.TELEGRAM_ADMIN_ID:
            return "allowed"

        response = await agent.hub.call("supabase__get_telegram_user", {"telegram_user_id": user_id})
        
        if (unwrap_response(response).get("telegram_user_id") == user_id):
            return "allowed"
        return "denied"
    except Exception as e:
        print(f"Erro ao verificar acesso: {e}")
        return "error"

def parse_command(text: str) -> tuple[bool, str | None, list[str] | None]:
    if not text.startswith("/"):
        return False, None, None
    parts_splitted_by_space = text.split()
    command_kind, *_ = [part.lower() for part in parts_splitted_by_space[0].split("@")]
    command_args = parts_splitted_by_space[1:]
    is_command = command_kind in ADMIN_COMMANDS
    return is_command, command_kind, command_args

async def execute_admin_command(agent, command_kind: str, command_args: list[str]) -> str:
    if command_kind == "/grant_access":
        return await grant_access(agent, command_args)
    elif command_kind == "/revoke_access":
        return await revoke_access(agent, command_args)
    elif command_kind == "/list_access":
        return await list_access(agent, command_args)
    else:
        return "Comando desconhecido."

async def grant_access(agent, command_args: list[str]) -> str:
    try:

        user_id = None
        username = None

        if len(command_args) >= 1:
            try:
                user_id = int(command_args[0])
            except ValueError:
                return "Erro: Argumento inválido. Use /grant_access <user_id> [<username>]."
        
        if len(command_args) == 2:
            username = command_args[1].lstrip("@")
        
        if len(command_args) not in [1, 2]:
            return "Erro: Argumentos inválidos. Use /grant_access <user_id> [<username>]."

        response = await agent.hub.call("supabase__create_telegram_user", {"telegram_user_id": user_id, "username": username})

        result = unwrap_response(response)

        if isinstance(result, dict) and "telegram_user_id" in result:
            return f"Acesso concedido para o usuário {user_id}."

        error_message = f"Erro ao conceder acesso para o usuário {user_id}" + "\n" + f"{result['erro']}"
        print(f"{error(error_message)}")
        return error_message

    except Exception as e:
        user_error_message = f"Erro ao conceder acesso com argumento(s) {command_args}" + "\n" + f"{type(e).__name__}: {e}"
        print(f"{error(user_error_message)}")
        return user_error_message

async def revoke_access(agent, command_args: list[str]) -> str:
    try:
        user_id = None

        if len(command_args) == 1:
            try:
                user_id = int(command_args[0])
            except ValueError:
                return "Erro: Argumento inválido. Use /revoke_access <user_id>."
        else:
            return "Erro: Argumentos inválidos. Use /revoke_access <user_id>."

        response = await agent.hub.call("supabase__remove_telegram_user", {"telegram_user_id": user_id})
    
        result = unwrap_response(response)

        if isinstance(result, dict) and "telegram_user_id" in result:
            return f"Acesso revogado para o usuário {user_id}."

        error_message = f"Erro ao revogar acesso para o usuário {user_id}" + "\n" + f"{result['erro']}"
        print(f"{error(error_message)}")
        return error_message

    except Exception as e:
        user_error_message = f"Erro ao revogar acesso com argumento(s) {command_args}" + "\n" + f"{type(e).__name__}: {e}"
        print(f"{error(user_error_message)}")
        return user_error_message

async def list_access(agent, command_args: list[str]) -> str:
    try:
        if len(command_args) > 0:
            return "Erro: Argumentos inválidos. Use /list_access."

        response = await agent.hub.call("supabase__list_telegram_users", {})
        users: list[TelegramUser] = unwrap_response(response)
        if users is None or len(users) == 0:
            return "Não há usuários com acesso.\nUse /grant_access <user_id> [<username>] para conceder acesso."
        users_formatted = [(f"{user['telegram_user_id']} - {user['username'] or '<username não definido>'}") for user in users]
        return "Usuários com acesso:\n" + "\n".join(users_formatted)
    except Exception as e:
        user_error_message = f"Erro ao listar usuários com acesso"
        print(f"{error(user_error_message)}: {type(e).__name__}: {e}")
        return user_error_message

async def main():
    if not config.TELEGRAM_BOT_TOKEN:
        print(error("Erro: TELEGRAM_BOT_TOKEN não configurado no arquivo message_agent/.env"))
        return

    if config.TELEGRAM_ADMIN_ID is None:
        print(error("Erro: TELEGRAM_ADMIN_ID não configurado no arquivo message_agent/.env"))
        return
    
    agent = create_agent()
    print(info(f"Iniciando LLM {agent.who_am_i()} e conectando aos servidores MCP...\n"))
    await agent.initialize()

    print(info("Ferramentas disponíveis:"))
    for name in agent.hub.routes:
        print(f"- {name}")
    print(info("\nBot ligado. Mande uma mensagem no Telegram. Ctrl+C para encerrar.\n"))

    # O getUpdates espera até 30s. O cliente HTTP precisa aguentar um pouco mais.
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
                    user_id = (message.get("from") or {}).get("id")
                    text = (message.get("text") or "").strip()

                    if chat_id is None or user_id is None or not text:
                        continue

                    username = (message.get("from") or {}).get("username") or "(anônimo)"

                    is_command, command_kind, command_args = parse_command(text)

                    if is_command:
                        if user_id != config.TELEGRAM_ADMIN_ID:
                            error_message = f"Este comando é restrito ao administrador do bot."
                            print(f"{error(error_message)}\n")
                            await send_message(client, chat_id, error_message)
                            continue

                        message_to_send = await execute_admin_command(agent, command_kind, command_args)
                        print(f"{success(username + ':')} {message_to_send}")
                        await send_message(client, chat_id, message_to_send)
                        continue

                    access = await check_access(agent, user_id)
                    if access == "allowed":
                        print(f"{success(username + ':')} {text}")
                        try: 
                            reply = await agent.answer(str(chat_id), text)
                        except Exception as e:
                            print(f"[Erro] {type(e).__name__}: {e}")
                            reply = "Tive um problema para responder agora. Tente de novo em instantes."
                        print(f"{warning('BugChatAI:')} {reply}\n")
                        await send_message(client, chat_id, reply)
                    elif access == "denied":
                        error_message = f"Acesso negado para o usuário {user_id} ({username})."
                        print(f"{error(error_message)}\n")
                        await send_message(client, chat_id, error_message)
                    elif access == "error":
                        error_message = f"Ocorreu um erro ao verificar acesso para o usuário {user_id} ({username})."
                        print(f"{error(error_message)}\n")
                        await send_message(client, chat_id, error_message)
                    else:
                        error_message = f"Ocorreu um erro desconhecido ao verificar acesso para o usuário {user_id} ({username})."
                        print(f"{error(error_message)}\n")
                        await send_message(client, chat_id, error_message)
    finally:
        await agent.terminate()

if __name__ == "__main__":
    asyncio.run(main())