"""
app/core/exceptions.py
───────────────────────
Domain-specific exception hierarchy used across the application.
"""

class CareerAcceleratorError(Exception):
    """Base exception for the platform."""

# ── PDF ────────────────────────────────────────────────────────────────────────
class PDFExtractionError(CareerAcceleratorError):
    """Raised when text cannot be extracted from a PDF."""

class PDFTooLargeError(CareerAcceleratorError):
    """Raised when the uploaded PDF exceeds the configured size limit."""

class EmptyPDFError(CareerAcceleratorError):
    """Raised when a PDF yields no extractable text."""

# ── Gemini ─────────────────────────────────────────────────────────────────────
class GeminiAPIError(CareerAcceleratorError):
    """Raised when the Gemini API call fails or returns an unexpected payload."""

class GeminiParseError(CareerAcceleratorError):
    """Raised when the Gemini response cannot be parsed into the expected schema."""

# ── Auth (Phase 2) ─────────────────────────────────────────────────────────────
class AuthError(CareerAcceleratorError):
    """Base authentication / authorisation error."""

class InvalidCredentialsError(AuthError):
    """Raised when email/password do not match."""

class UserAlreadyExistsError(AuthError):
    """Raised when registering with an email that is already taken."""

class InvalidTokenError(AuthError):
    """Raised when a JWT is missing, malformed, or expired."""

class InsufficientPermissionsError(AuthError):
    """Raised when a user attempts an action their role does not allow."""