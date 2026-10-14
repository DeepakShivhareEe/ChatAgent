"""
Custom exception classes for the application.
"""

# Sent to the client for any 5xx-class failure. Internal messages (upstream
# provider text, file paths, parser errors) must not leave the server.
GENERIC_ERROR_MESSAGE = "An unexpected server error occurred. Please try again."


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    @property
    def client_message(self) -> str:
        """Message that is safe to return to the client.

        Client errors (4xx) are written for the user and stay as they are;
        server errors (5xx) are replaced with a generic message and logged in
        full, server-side only.
        """
        if self.status_code >= 500:
            return GENERIC_ERROR_MESSAGE
        return self.message


class ProviderError(AppException):
    """Raised when an LLM provider encounters an error."""

    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(f"[{provider}] {message}", status_code=502)


class ProviderNotFoundError(AppException):
    """Raised when the configured provider is not supported."""

    def __init__(self, provider: str):
        super().__init__(
            f"Unsupported AI provider: '{provider}'. "
            f"Supported: openai, anthropic, gemini, groq, openrouter",
            status_code=400,
        )


class InjectionDetectedError(AppException):
    """Raised when a prompt injection attempt is detected."""

    def __init__(self, message: str = "Potentially harmful input detected."):
        super().__init__(message, status_code=400)


class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=429)


class IngestionError(AppException):
    """Raised when document ingestion fails."""

    def __init__(self, message: str):
        super().__init__(f"Ingestion error: {message}", status_code=500)


class VectorDBError(AppException):
    """Raised when vector database operations fail."""

    def __init__(self, message: str):
        super().__init__(f"Vector DB error: {message}", status_code=500)


class DocumentLoadError(AppException):
    """Raised when a document fails to load."""

    def __init__(self, filepath: str, reason: str):
        super().__init__(
            f"Failed to load '{filepath}': {reason}",
            status_code=500,
        )
