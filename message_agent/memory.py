class Memory:
    def __init__(self, max_history_messages: int = 30):
        self.max_history_messages = max_history_messages
        self.conversation = {}

    def get_conversation(self, chat_id):
        if chat_id not in self.conversation:
            self.conversation[chat_id] = []
        # Retorna a lista de mensagens do chat por referência, permitindo modificações pelo agente
        return self.conversation[chat_id]

    def trim_conversation(self, chat_id):
        history = self.get_conversation(chat_id)
        if len(history) <= self.max_history_messages:
            return

        start = len(history) - self.max_history_messages
        # Evita excluir mensagem retida mais antiga, caso seja do usuário, mantendo
        # a mensagem mais antiga do histórico como sendo uma mensagem do usuário
        while start < len(history) and not self._is_user_message(history[start]):
            start += 1
        # Exclui as mensagens desde o início até a variável start, mantendo as mensagens mais recentes
        del history[:start]

    @staticmethod
    def _is_user_message(message):
        return message.role == "user" and any(part.text for part in message.parts or [])