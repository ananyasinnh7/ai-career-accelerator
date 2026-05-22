
"""
app/core/exceptions.py
───────────────────────
Domain-specific exception hierarchy used across the application.
FastAPI exception handlers are wired up in main.py.
"""
 
 
class CareerAcceleratorError(Exception):
    """Base exception for the platform."""
 
 
class PDFExtractionError(CareerAcceleratorError):
    """Raised when text cannot be extracted from a PDF."""
 
 
class PDFTooLargeError(CareerAcceleratorError):
    """Raised when the uploaded PDF exceeds the configured size limit."""
 
 
class EmptyPDFError(CareerAcceleratorError):
    """Raised when a PDF yields no extractable text."""
 
 
class GeminiAPIError(CareerAcceleratorError):
    """Raised when the Gemini API call fails or returns an unexpected payload."""
 
 
class GeminiParseError(CareerAcceleratorError):
    """Raised when the Gemini response cannot be parsed into the expected schema."""
 