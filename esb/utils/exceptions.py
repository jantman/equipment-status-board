"""Domain exception hierarchy for ESB application.

All service-layer exceptions inherit from ESBError.
"""


class ESBError(Exception):
    """Base exception for all ESB errors."""


class EquipmentNotFound(ESBError):
    """Raised when equipment lookup fails."""


class RepairRecordNotFound(ESBError):
    """Raised when repair record lookup fails."""


class UnauthorizedAction(ESBError):
    """Raised when a user lacks permission for an action."""


class ValidationError(ESBError):
    """Raised when input validation fails."""
