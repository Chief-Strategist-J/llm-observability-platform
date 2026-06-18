class SloBurnError(Exception):
    """Base error class for SLO Burn Rate Worker"""
    pass

class ValidationError(SloBurnError):
    """Configuration or contract validation failure"""
    pass
