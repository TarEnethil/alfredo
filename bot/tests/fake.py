class FakeBot:
    def __init__(self, token):
        self.token = token
        self.handlers = {}
        self.message_id = 0
        self.raise_exception = False

    def set_my_commands(self, commands):
        self.commands = commands

    def register_message_handler(self, func, commands):
        for cmd in commands:
            assert cmd not in self.handlers.keys()
            self.handlers[cmd] = func

    def send_message(self, chat_id, text, **kwargs):
        if self.raise_exception:
            self.raise_exception = False
            raise Exception("Fake API Error")

        self.last_message_chat_id = chat_id
        self.last_message_text = text

    def send_poll(self, chat_id, question, **kwargs):
        if self.raise_exception:
            self.raise_exception = False
            raise Exception("Fake API Error")

        self.last_poll_chat_id = chat_id
        self.last_poll_text = question

        self.message_id += 1
        return FakePoll(self.message_id)

    def reply_to(self, message, text, **kwargs):
        if self.raise_exception:
            self.raise_exception = False
            raise Exception("Fake API Error")

        self.last_reply_text = text

    def infinity_polling(self):
        self.is_polling = True

    def raise_on_next_action(self):
        self.raise_exception = True

    def handle_command(self, cmd, msg):
        assert cmd in self.handlers.keys()

        self.handlers[cmd](msg)


class FakeMessage:
    def __init__(self, user=None, chat_type=None, text=None):
        self.from_user = user
        self.chat = FakeChat(chat_type)
        self.text = text


class FakeChat:
    def __init__(self, chat_type):
        self.type = chat_type


class FakeUser:
    def __init__(self, id_):
        self.id = id_


class FakePoll:
    def __init__(self, message_id):
        self.message_id = message_id
