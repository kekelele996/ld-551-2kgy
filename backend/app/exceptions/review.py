class ReviewPermissionException(Exception):
    def __init__(self, message: str = "当前账号不能提交课程评价"):
        self.message = message
        super().__init__(message)
