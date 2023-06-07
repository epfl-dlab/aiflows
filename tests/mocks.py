class MockChatOpenAI:

    def __init__(self, num_fails=2, *args, **kwargs):
        self.fail_count = 0
        self.num_fails = num_fails

    def __call__(self, *args, **kwargs):
        if self.fail_count < self.num_fails:
            self.fail_count += 1
            raise Exception("mockery")
        else:
            return MockResponse()


class MockResponse:
    content = "hello"


class MockTemplate:
    def __init__(self, content):
        self.content = content
        self.input_variables = []

    def format(self, *args, **kwargs):
        return self.content

    def to_string(self, *args, **kwargs):
        return self.content
