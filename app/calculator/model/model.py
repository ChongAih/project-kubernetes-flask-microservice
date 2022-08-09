class CommonResponse(object):
    def __init__(self, retcode: int = None, status: str = None, message: str = None):
        self.retcode = retcode
        self.status = status
        self.message = message

    def __repr__(self):
        return f"CommonResponse({self.retcode},{self.status},{repr(self.message)})"


class Response(object):
    def __init__(self, task_id: str = None, response: CommonResponse = None):
        self.task_id = task_id
        self.response = response

    def __repr__(self):
        return f"Response({self.task_id},{repr(self.response)})"


class Result(object):
    def __init__(self, task_id: str = None, response: CommonResponse = None, output: float = None):
        self.task_id = task_id
        self.response = response
        self.output = output

    def __repr__(self):
        return f"Result({self.task_id},{repr(self.response)},{repr(self.output)})"
