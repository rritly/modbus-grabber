from enum import Enum


class ReadActionType(Enum):
    READ_ALL = "READ_ALL"
    READ_INPUTS = "READ_INPUTS"
    READ_HOLDINGS = "READ_HOLDINGS"

class ControllerException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message
