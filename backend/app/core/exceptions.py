"""Application-level exception hierarchy."""


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, *, error_code: str = "app_error", status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str, *, error_code: str = "not_found") -> None:
        super().__init__(message, error_code=error_code, status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str, *, error_code: str = "validation_error") -> None:
        super().__init__(message, error_code=error_code, status_code=422)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str, *, error_code: str = "service_unavailable") -> None:
        super().__init__(message, error_code=error_code, status_code=503)
