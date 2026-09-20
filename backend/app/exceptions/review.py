class ReviewNotAllowedException(Exception):
    def __init__(self, message: str = "当前无法评价该课程"):
        self.message = message
        super().__init__(message)
