from fastapi import HTTPException, status


class CloudBoxError(Exception):
    """Base application error."""

    def __init__(self, message: str, *, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ProviderNotConfiguredError(CloudBoxError):
    def __init__(self, provider: str):
        super().__init__(
            f"Provider '{provider}' is not configured. Add credentials to .env",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ProviderNotImplementedError(CloudBoxError):
    def __init__(self, provider: str):
        super().__init__(
            f"Provider '{provider}' is not implemented yet",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
        )


class ProviderAPIError(CloudBoxError):
    def __init__(self, provider: str, message: str, *, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(f"{provider}: {message}", status_code=status_code)


def to_http_exception(exc: CloudBoxError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)
