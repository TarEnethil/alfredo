from functools import wraps


def raise_exception_if_needed():
    def decorator(f):
        @wraps(f)
        def decorated_function(self, *args, **kwargs):
            skip = False
            if self.delay > 0:
                skip = True
                self.delay -= 1

            if skip is False and self.exceptions > 0:
                self.exceptions -= 1
                raise Exception("Fake API Error")

            return f(self, *args, **kwargs)
        return decorated_function
    return decorator


class FakeBot:
    def __init__(self, token):
        self.token = token
        self.handlers = {}
        self.message_id = 0
        self.delay = 0
        self.exceptions = 0
        self.polls = {}
        self.pinned_message_ids = []

    def set_my_commands(self, commands):
        self.commands = commands

    def register_message_handler(self, func, commands):
        for cmd in commands:
            assert cmd not in self.handlers.keys()
            self.handlers[cmd] = func

    @raise_exception_if_needed()
    def send_message(self, chat_id, text, **kwargs):
        self.last_message_chat_id = chat_id
        self.last_message_text = text

    @raise_exception_if_needed()
    def send_poll(self, chat_id, question, **kwargs):
        self.last_poll_chat_id = chat_id
        self.last_poll_text = question

        self.message_id += 1
        self.polls[self.message_id] = True
        return FakePoll(self.message_id)

    @raise_exception_if_needed()
    def stop_poll(self, chat_id, message_id):
        assert message_id in self.polls.keys()
        self.polls[message_id] = False

    @raise_exception_if_needed()
    def reply_to(self, message, text, **kwargs):
        self.last_reply_text = text

    @raise_exception_if_needed()
    def send_document(self, document, **kwargs):
        self.last_document = document

    @raise_exception_if_needed()
    def get_chat(self, chat_id):
        if len(self.pinned_message_ids) > 0:
            return FakeChat("group", pinned_message=FakeMessage(message_id=self.pinned_message_ids[-1]))

        return FakeChat("group")

    @raise_exception_if_needed()
    def pin_chat_message(self, message_id, **kwargs):
        self.pinned_message_ids.append(message_id)

    @raise_exception_if_needed()
    def unpin_chat_message(self, message_id, chat_id):
        assert message_id in self.pinned_message_ids
        self.pinned_message_ids.remove(message_id)

    def infinity_polling(self):
        self.is_polling = True

    def raise_on_next_action(self, n=1, delay_by=0):
        self.delay = delay_by
        self.exceptions = n

    def handle_command(self, cmd, msg):
        assert cmd in self.handlers.keys()

        self.handlers[cmd](msg)


class FakeMessage:
    def __init__(self, user=None, chat_type=None, text=None, message_id=None):
        self.from_user = user
        self.chat = FakeChat(chat_type)
        self.text = text
        self.message_id = message_id


class FakeChat:
    def __init__(self, chat_type, pinned_message=None):
        self.type = chat_type
        self.pinned_message = pinned_message


class FakeUser:
    def __init__(self, id_, first_name, username):
        self.id = id_
        self.first_name = first_name
        self.username = username


class FakePoll:
    def __init__(self, message_id):
        self.message_id = message_id
