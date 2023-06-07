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


class MockBrokenChatOpenAI:

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        raise Exception("mockery")


class MockResponse:
    content = "hello"
