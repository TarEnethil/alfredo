class FakeBot:
    def __init__(self, token):
        self.token = token
        self.handlers = {}
        self.message_id = 0

    def set_my_commands(self, commands):
        self.commands = commands

    def register_message_handler(self, func, commands):
        for cmd in commands:
            assert cmd not in self.handlers.keys()
            self.handlers[cmd] = func

    def send_poll(self, **kwargs):
        if self.poll_fail:
            raise Exception("Fake API Error")

        self.message_id += 1
        return FakePoll(self.message_id)

    def reply_to(self, replymsg, msg, **kwagrs):
        self.last_reply = msg

    def infinity_polling(self):
        self.is_polling = True

    def send_poll_shall_fail(self, should):
        self.poll_fail = should

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
