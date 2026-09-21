class DatabaseError(RuntimeError):
    """Base error for Mini Onyx database operations."""


class DatabaseConfigurationError(DatabaseError):
    """Raised when database configuration is invalid."""


class DatabaseConnectionError(DatabaseError):
    """Raised when the database cannot be reached."""
