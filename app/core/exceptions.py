class NotFoundError(Exception):
    pass


class UnauthorizedError(Exception):
    pass


class ValidationError(Exception):
    pass


class ServiceUnavailableError(Exception):
    pass


class MailDeliveryError(Exception):
    pass
