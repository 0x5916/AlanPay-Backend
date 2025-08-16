from fastapi import HTTPException, status


class UserException(HTTPException):
    def __init__(self, status_code, detail: str):
        super().__init__(
            status_code=status_code,
            detail=detail
        )

class UserNotFoundException(UserException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )
