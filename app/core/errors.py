# app/core/errors.py
class APIError(Exception):
    """Base exception for API errors."""
    status_code = 500
    message = "An unknown error occurred."
    
    def __init__(self, message=None, status_code=None, payload=None):
        super().__init__(message or self.message)
        self.message = message or self.message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['status'] = 'error'
        rv['message'] = self.message
        return rv

class BadRequestError(APIError):
    """400 Bad Request Error."""
    status_code = 400
    message = "Bad request."

class UnauthorizedError(APIError):
    """401 Unauthorized Error."""
    status_code = 401
    message = "Authentication required."

class ForbiddenError(APIError):
    """403 Forbidden Error."""
    status_code = 403
    message = "Permission denied."

class NotFoundError(APIError):
    """404 Not Found Error."""
    status_code = 404
    message = "Resource not found."

class ConflictError(APIError):
    """409 Conflict Error."""
    status_code = 409
    message = "Resource conflict."