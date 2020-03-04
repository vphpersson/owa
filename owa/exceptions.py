from typing import Optional
from aiohttp import ClientResponse


class OWAError(Exception):
    pass


class MissingCanaryError(OWAError):
    def __init__(self):
        super().__init__('No X-OWA-Canary cookie could be found.')


class OWAAuthenticationError(OWAError):
    def __init__(self, msg: str, username: str, password: str, response_time: Optional[float] = None):
        super().__init__(msg)
        self.username: str = username
        self.password: str = password
        self.response_time: Optional[float] = response_time


class ExpiredPasswordError(OWAAuthenticationError):
    def __init__(self, username: str, password: str, response_time: float):
        super().__init__(
            msg=f'The provided password for {username} has expired.',
            username=username,
            password=password,
            response_time=response_time
        )


class ExternalDomainError(OWAAuthenticationError):
    def __init__(self, username: str, password: str, response_time: float):
        super().__init__(
            msg=f'The login page for {username} redirects to an external service (Likely to Office365).',
            username=username,
            password=password,
            response_time=response_time
        )


class IncorrectLoginCredentials(OWAAuthenticationError):
    def __init__(self, username: str, password: str, response_time: float):
        super().__init__(
            msg='The provided login credentials are incorrect.',
            username=username,
            password=password,
            response_time=response_time
        )


class BadReasonError(OWAAuthenticationError):
    def __init__(self, username: str, password: str, reason_number: int, response_time: float):
        super().__init__(
            msg=f'The OWA returned an unexpected reason number: {reason_number}',
            username=username,
            password=password,
            response_time=response_time
        )
        self.reason_number = reason_number


class UnknownLoginError(OWAAuthenticationError):
    def __init__(self, username: str, password: str, response_time: float, response: ClientResponse):
        super().__init__(
            msg=f'The login attempt using {username} - {password} failed due to an unknown error',
            username=username,
            password=password,
            response_time=response_time
        )
        self.response = response
