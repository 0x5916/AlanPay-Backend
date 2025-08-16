from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.exceptions.user import UnauthorizedException, UserException
from app.exceptions.payment import TransactionException
from fastapi import status
from app.utils.logging_config import logger
from app.constants.error_code import PAYMENT_ERROR, INTERNAL_ERROR, UNAUTHORIZED, USER_ERROR, VALIDATION_ERROR

import jwt


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(UnauthorizedException)
    async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
        logger.warning(f"Unauthorized access: {exc.detail} | Path: {request.url.path} | IP: {request.client.host if request.client else 'unknown'}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Unauthorized",
                "detail": exc.detail,
                "code": UNAUTHORIZED
            }
        )

    @app.exception_handler(jwt.ExpiredSignatureError)
    async def jwt_expired_exception_handler(request: Request, exc: jwt.ExpiredSignatureError):
        logger.warning(f"JWT expired: {str(exc)} | Path: {request.url.path} | IP: {request.client.host if request.client else 'unknown'}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Unauthorized",
                "detail": "Token has expired",
                "code": UNAUTHORIZED
            }
        )

    # Global exception handlers
    @app.exception_handler(TransactionException)
    async def payment_exception_handler(request: Request, exc: TransactionException):
        logger.warning(f"Payment error: {exc.detail} | Path: {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Payment Error",
                "detail": exc.detail,
                "code": PAYMENT_ERROR
            }
        )

    @app.exception_handler(UserException)
    async def user_not_found_exception_handler(request: Request, exc: UserException):
        logger.warning(f"User error: {exc.detail} | Path: {request.url.path}")
        headers = exc.headers or {}
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "User Error",
                "detail": exc.detail,
                "code": USER_ERROR
            }
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        logger.warning(f"Validation error: {exc.errors()} | Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": exc.errors(),
                "code": VALIDATION_ERROR
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)} | Path: {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred",
                "code": INTERNAL_ERROR
            }
        )
