from aiohttp import ClientResponse


class OWAAuthenticationError(Exception):
    pass


# TODO: Reconsider `user` parameter.

class ExpiredPasswordError(OWAAuthenticationError):
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password
        super().__init__(f'The provided password for {user} has expired.')


class ExternalDomainError(OWAAuthenticationError):
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password
        super().__init__(f'The login page for {user} redirects to an external service (Likely to Office365).')


class MissingCanaryError(OWAAuthenticationError):
    def __init__(self):
        super().__init__('No X-OWA-Canary cookie could be found.')


class IncorrectLoginCredentials(OWAAuthenticationError):
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password
        self.reason_message = 'The user name or password you entered isn\'t correct. Try entering it again.'
        super().__init__('The login credentials ')


class BadReasonError(OWAAuthenticationError):
    def __init__(self, user: str, password: str, reason_number: int):
        self.user = user
        self.password = password
        self.reason_number = reason_number
        super().__init__(f'The OWA returned an unexpected reason number: {reason_number}')


class UnknownLoginError(Exception):
    def __init__(self, user: str, password: str, response: ClientResponse):
        self.user = user
        self.password = password
        self.response = response
        super().__init__(f'The login attempt using {user} - {password} failed due to an unknown error')