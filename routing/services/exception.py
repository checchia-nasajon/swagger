class ExceptionBuilder:
    def __init__(self, exception, separator):
        self.messages = list()
        self.separator = separator
        self.exception = exception

    def add_message(self, message):
        self.messages.append(message)

    def set_messages(self, messages):
        self.messages = messages

    def get_exception_message(self):
        message = self.separator.join(self.messages)
        return message

    def has_exception(self):
        return len(self.messages) != 0

    def raise_exception_if_exist(self):
        if not self.has_exception():
            return
        message = self.get_exception_message(self)
        raise self.exception(message)
