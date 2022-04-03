from typing import Any


class NoImportantParameter(Exception):
    def __init__(self):
        pass

class OperationOnlyForOneCountry(Exception):
    def __init__(self):
        pass


class CantTransact(Exception):
    def __init__(self, reason: str|dict[str, Any]):
        self.reason = reason
