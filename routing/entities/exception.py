
class InvalidPenaltyTypeError(ValueError):
    def __init__(self, message):
        super().__init__(message)


class InvalidSolutionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class LocationNameError(KeyError):
    def __init__(self, message):
        super().__init__(message)
