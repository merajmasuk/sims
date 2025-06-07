from enum import Enum


class ResponseCodes(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    CREATED = "CREATED"
