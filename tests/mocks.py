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

class MockAnnotator:
    def __init__(self, key, *args, **kwargs):
        self.key=key

    def __call__(self, data, *args, **kwargs):
        return {self.key : data}

class MockMessage:
    def __init__(self, flow_run_id, message_creator):
        self.flow_run_id = flow_run_id
        self.message_creator = message_creator
