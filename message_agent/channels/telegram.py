import asyncio

import httpx

from helpers.cli_helpers import error, info, success, warning
from mcp_servers.supabase_tools.telegram_users_type import TelegramUser
from message_agent import config
from message_agent.agents import create_agent

# O tamanho máximo de uma mensagem no Telegram é de 4096 caracteres
MAX_MESSAGE_LENGTH = 4000

ADMIN_COMMANDS = { 
    "/grant_access": {
        "parameters": "<user_id> [<username>]",
        "description": "Concede acesso a um usuário",
        "access": "admin",
    },
    "/revoke_access": {
        "parameters": "<user_id>", 
        "description": "Revoga acesso a um usuário",
        "access": "admin",
    },
    "/list_access": {
        "parameters": None,
        "description": "Lista todos os usuários com acesso",
        "access": "admin",
    },
    "/help": {
        "parameters": None,
        "description": "Mostra esta mensagem de ajuda",
        "access": "user",
    }
}

def api_url(method: str):
    return f"{config.TELEGRAM_BASE_URL}{config.TELEGRAM_BOT_TOKEN}/{method}"

async def call_api(client, method, **payload):
    response = await client.post(api_url(method), json=payload)
    data = response.json()
    if not data.get("ok"):
        description = data.get("description") or f"HTTP {response.status_code}"
        raise RuntimeError(description)
    return data.get("result")

async def send_bot_message(client, chat_id, text):
    if not text:
        text = "(sem resposta)"
    for start in range(0, len(text), MAX_MESSAGE_LENGTH):
        piece = text[start:start + MAX_MESSAGE_LENGTH]
        await call_api(client, "sendMessage", chat_id=chat_id, text=piece)

def help_text(is_admin: bool) -> str:
    help_list = ["Sou um assistente de IA. Gerencie suas notas comigo."]
    
    for command, props in ADMIN_COMMANDS.items():
        if props['access'] != "admin" or is_admin:
            help_list.append(f"{command} {props['parameters'] + ' ' if props['parameters'] else ''}- {props['description']}")

    return "\n".join(help_list)

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

def parse_command(text: str) -> tuple[str | None, list[str]]:
    if not text.startswith("/"):
        return None, []
    parts_splitted_by_space = text.split()
    command_kind, *_ = [part.lower() for part in parts_splitted_by_space[0].split("@")]
    command_args = parts_splitted_by_space[1:]
    return command_kind, command_args

def get_command(command_kind: str) -> tuple[bool, str | None]:
    is_valid = command_kind in ADMIN_COMMANDS
    role = ADMIN_COMMANDS.get(command_kind, {}).get("access") if is_valid else None
    return is_valid, role

async def execute_command(agent, command_kind: str, command_args: list[str], is_admin: bool) -> str:
    if command_kind == "/grant_access":
        return await grant_access(agent, command_args)
    elif command_kind == "/revoke_access":
        return await revoke_access(agent, command_args)
    elif command_kind == "/list_access":
        return await list_access(agent, command_args)
    elif command_kind == "/help":
        return help_text(is_admin)
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
        user_error_message = "Erro ao listar usuários com acesso"
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

                    command_kind, command_args = parse_command(text)

                    access = await check_access(agent, user_id)

                    if access == "error":
                        error_message = f"Ocorreu um erro ao verificar acesso para o usuário {user_id} ({username})."
                        print(f"{error(error_message)}\n")
                        await send_bot_message(client, chat_id, error_message)
                        continue

                    if access == "denied":
                        access_denied_message_list = ["Acesso negado."]
                        access_denied_message_list.append("Solicite acesso ao administrador do bot, informando seu id e username")
                        access_denied_message_list.append(f"id: {user_id}")
                        access_denied_message_list.append(f"username: {username}")
                        access_denied_message_list.append("@victoralvesbug")
                        access_denied_message = "\n".join(access_denied_message_list)
                        print(f"{warning(access_denied_message)}\n")
                        await send_bot_message(client, chat_id, access_denied_message)
                        continue

                    if access != "allowed":
                        unknown_error_message = f"Ocorreu um erro desconhecido ao verificar acesso para o usuário {user_id} ({username})."
                        print(f"{error(unknown_error_message)}\n")
                        await send_bot_message(client, chat_id, unknown_error_message)
                        continue

                    is_valid_command, command_role = get_command(command_kind)

                    is_admin_user = user_id == config.TELEGRAM_ADMIN_ID
                    is_user_command = command_role != "admin"
                    is_admin_command_and_admin_user = command_role == "admin" and is_admin_user
                    
                    if is_valid_command:
                        if is_user_command or is_admin_command_and_admin_user:
                            command_result = await execute_command(agent, command_kind, command_args, is_admin_user)
                            print(f"{info('Gerenciador de Comandos:')} {command_result}")
                            await send_bot_message(client, chat_id, command_result)
                            continue
                        
                        command_result = "Comando restrito ao administrador do bot."
                        print(f"{info('Gerenciador de Comandos:')} {command_result}")
                        await send_bot_message(client, chat_id, command_result)
                        continue

                    if command_kind is not None:
                        command_result = "Comando desconhecido."
                        print(f"{info('Gerenciador de Comandos:')} {command_result}")
                        await send_bot_message(client, chat_id, command_result)
                        continue

                    print(f"{success(username + ':')} {text}")
                    try: 
                        reply = await agent.answer(str(chat_id), text)
                    except Exception as e:
                        print(f"[Erro] {type(e).__name__}: {e}")
                        reply = "Tive um problema para responder agora. Tente de novo em instantes."
                    print(f"{warning('BugChatAI:')} {reply}\n")
                    await send_bot_message(client, chat_id, reply)
    finally:
        await agent.terminate()

if __name__ == "__main__":
    asyncio.run(main())