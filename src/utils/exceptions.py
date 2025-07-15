"""Custom exceptions for the application."""

class BotError(Exception):
    """Base exception for all bot errors."""
    pass


class ConfigError(BotError):
    """Configuration related errors."""
    pass


class DatabaseError(BotError):
    """Database related errors."""
    pass


class APIError(BotError):
    """API related errors."""
    pass


class ServiceError(BotError):
    """Base class for service related errors."""
    pass


class AlertServiceError(ServiceError):
    """Alert service related errors."""
    pass


class OutputServiceError(ServiceError):
    """Output service related errors."""
    pass


class AIServiceError(ServiceError):
    """AI service related errors."""
    pass


class RiskAssessmentError(ServiceError):
    """Risk assessment service related errors."""
    pass


class TokenServiceError(ServiceError):
    """Token service related errors."""
    pass


class ValidationError(BotError):
    """Data validation errors."""
    pass


class AuthenticationError(BotError):
    """Authentication related errors."""
    pass


class RateLimitError(BotError):
    """Rate limit related errors."""
    pass


class NetworkError(BotError):
    """Network related errors."""
    pass


class ExternalServiceError(BotError):
    """External service related errors."""
    pass
