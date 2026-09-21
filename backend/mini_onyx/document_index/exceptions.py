class StorageConfigurationError(RuntimeError):
    """Raised when the local object store is not configured."""


class DocumentValidationError(ValueError):
    """Raised when an uploaded document is not supported."""


class DocumentTooLargeError(DocumentValidationError):
    """Raised when an uploaded document exceeds the size limit."""
