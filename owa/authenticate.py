from http.cookies import BaseCookie
from urllib.parse import urlparse, parse_qs

from aiohttp import ClientSession
from aiohttp.cookiejar import URL

from owa.exceptions import ExpiredPasswordError, ExternalDomainError, IncorrectLoginCredentials, UnknownLoginError, \
    BadReasonError


# TODO: Might as well return the response, and a response time?
async def authenticate_session(session: ClientSession, origin: str, username: str, password: str, **kwargs) -> None:
    """
    Attempt to authenticate the provided session to OWA given the provided authentication details.

    In case the authentication is unsuccessful, an appropriate exception is raised.

    :param session: The session to be authenticated.
    :param origin: The origin of the HTTP endpoint of the OWA which to authenticate with.
    :param username: The username to authenticate with.
    :param password: The password to authenticate with.
    :param kwargs: Extra options passed to `ClientSession.post`.
    :return: None
    """

    # Have the logon page response set a session id cookie with the `Set-Cookie` header.
    # TODO: Required by OWA 2010 -- not tested with others.
    async with session.get(url=f'{origin}/owa/auth/logon.aspx'):
        pass

    # TODO: `PBack=0` is required by OWA 2010 -- not tested with others.
    session.cookie_jar.update_cookies(
        cookies=BaseCookie({'PBack': '0'}),
        response_url=URL(origin)
    )

    request_options = dict(
        url=f'{origin}/owa/auth.owa',
        headers={'Connection': 'Keep-Alive'},
        data=dict(
            destination=f'{origin}/owa/',
            flags='0',
            forcedownlevel='0',
            trusted='0',
            username=username,
            password=password,
            isUtf8='1'
        ),
        verify_ssl=False,
        **kwargs
    )

    async with session.post(**request_options) as response:

        if 'expiredpassword' in str(response.url):
            raise ExpiredPasswordError(username, password)

        # TODO: Use `query_attribute_to_value`.
        if 'extDomain' in parse_qs(urlparse(str(response.url)).query):
            raise ExternalDomainError(username, password)

        query_attribute_to_value = parse_qs(response.url.query_string)
        if 'reason' in query_attribute_to_value:
            # TODO: Reconsider safeness.
            reason = int(next(iter(query_attribute_to_value['reason'])))
            if reason == 2:
                raise IncorrectLoginCredentials(username, password)
            else:
                raise BadReasonError(user=username, password=password, reason_number=reason)

        if str(response.status).startswith('5') or response.status == 404:
            raise UnknownLoginError
