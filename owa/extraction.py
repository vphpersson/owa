from asyncio import gather as asyncio_gather
from json import loads as json_loads
from html import unescape as html_unescape
from typing import Dict, Set

from aiohttp import ClientSession
from esprima import parse as esprima_parse
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup

from owa.exceptions import MissingCanaryError


def get_canary_token_value_from_session(session: ClientSession) -> str:
    try:
        # TODO: Reconsider.
        return session.cookies.get('X-OWA-Canary')
    except KeyError as e:
        raise MissingCanaryError from e


async def get_people_filters(session: ClientSession, origin: str):
    """
    Perform the GetPeopleFilters EWS operation.

    (Not officially documented?)

    :param session: An authenticated `aiohttp.ClientSession`.
    :param origin: The origin part of the URL of the OWA.
    :return:
    """

    canary_cookie_value = get_canary_token_value_from_session(session=session)

    request_options = dict(
        url=f'{origin}/owa/service.svc?action=GetPeopleFilters',
        json={},
        headers={
            'X-OWA-Canary': canary_cookie_value,
            'Action': 'GetPeopleFilters'
        }
    )

    async with session.post(**request_options) as response:
        return response.json()


# TODO: "This operation was introduced in Exchange Server 2013."
async def find_people(
    session: ClientSession,
    origin: str,
    folder_id: int,
    query_string: str,
    offset: int = 0,
    max_entries_returned: int = 999999999
):
    """
    Perform the FindPeople EWS operation.

    "The FindPeople operation returns all persona objects from a specified Contacts folder or retrieves contacts that
    match a specified query string."

    https://docs.microsoft.com/en-us/exchange/client-developer/web-service-reference/findpeople-operation

    :param session: An authenticated `aiohttp.ClientSession`.
    :param origin: The origin part of the URL of the OWA.
    :param folder_id: The id of the contacts folder which to search.
    :param query_string: The search string.
    :param offset:
    :param max_entries_returned:
    :return:
    """

    canary_cookie_value = get_canary_token_value_from_session(session=session)

    request_options = dict(
        url=f'{origin}/owa/service.svc?action=FindPeople',
        json={
            '__type': 'FindPeopleJsonRequest:#Exchange',
            'Header': {
                '__type': 'JsonRequestHeaders:#Exchange',
                'RequestServerVersion': 'Exchange2013',
                'TimeZoneContext': {
                    '__type': 'TimeZoneContext:#Exchange',
                    'TimeZoneDefinition': {
                        '__type': 'TimeZoneDefinitionType:#Exchange',
                        'Id': 'Mountain Standard Time'
                    }
                }
            },
            'Body': {
                '__type': 'FindPeopleRequest:#Exchange',
                'IndexedPageItemView': {
                    '__type': 'IndexedPageView:#Exchange',
                    'BasePoint': 'Beginning',
                    'Offset': offset,
                    'MaxEntriesReturned': max_entries_returned
                },
                'QueryString': query_string or None,
                'ParentFolderId': {
                    '__type': 'TargetFolderId:#Exchange',
                    'BaseFolderId': {
                        '__type': 'AddressListId:#Exchange',
                        'Id': folder_id
                    }
                },
                'PersonaShape': {
                    '__type': 'PersonaResponseShape:#Exchange',
                    'BaseShape': 'Default'
                },
                'ShouldResolveOneOffEmailAddress': False
            }
        },
        headers={
            'X-OWA-Canary': canary_cookie_value,
            'Action': 'FindPeople'
        }
    )

    async with session.post(**request_options) as response:
        return response.json()


# TODO: "This operation was introduced in Exchange Server 2013."
async def get_persona(session: ClientSession, origin: str, persona_id: int):
    """
    Perform the GetPersona EWS operation.

    "The GetPersona operation returns a set of properties that are associated with a persona."

    https://docs.microsoft.com/en-us/exchange/client-developer/web-service-reference/getpersona-operation

    :param session: An authenticated `aiohttp.ClientSession`.
    :param origin: The origin part of the URL of the OWA.
    :param persona_id: The id of the persona about which to retrieve information.
    :return:
    """

    canary_cookie_value = get_canary_token_value_from_session(session=session)

    request_options = dict(
        url=f'{origin}/owa/service.svc?action=GetPersona',
        json={
            '__type': 'GetPersonaJsonRequest:#Exchange',
            'Header': {
                '__type': 'JsonRequestHeaders:#Exchange',
                'RequestServerVersion': 'Exchange2013',
            },
            'Body': {
                '__type': 'GetPersonaRequest:#Exchange',
                'PersonaId': {
                    '__type': 'ItemId:#Exchange',
                    'Id': persona_id
                }
            }
        },
        headers={
            'X-OWA-Canary': canary_cookie_value,
            'Action': 'GetPersona'
        }
    )

    async with session.post(**request_options) as response:
        return response.json()


async def get_days_until_password_expiration(session: ClientSession, origin: str) -> int:
    """

    :param session: An authenticated `aiohttp.ClientSession`.
    :param origin: The origin part of the URL of the OWA.
    :return:
    """

    canary_cookie_value = get_canary_token_value_from_session(session=session)

    request_options = dict(
        url=f'{origin}/owa/service.svc?action=GetDaysUntilPasswordExpiration',
        json={},
        headers={
            'X-OWA-Canary': canary_cookie_value,
            'Action': 'GetDaysUntilPasswordExpiration'
        }
    )

    # TODO: Consider return type.

    async with session.post(**request_options) as response:
        return await response.json()


# async def get_domain_username_from_ui(session: ClientSession, origin: str) -> Tuple[str, str]:
#     """
#
#     :return:
#     """
#
#     prefixed_domain_user_name = json_loads(
#         self.session.get(f'{origin}/ecp/PersonalSettings/Password.aspx').html
#             .find('#ResultPanePlaceHolder_ctl00_ctl02_ctl01_ChangePassword', first=True)
#             .attrs['vm-preloadresults'][5:]
#     )['Output'][0]['DomainUserName']
#
#     # TODO: Reverse?
#     return prefixed_domain_user_name.split('\\', maxsplit=1)


async def get_account_identity_from_ui(session: ClientSession, origin: str, **extra_request_keywords) -> Dict[str, str]:
    """

    :param session: An authenticated `aiohttp.ClientSession`.
    :param origin: The origin part of the URL of the OWA.
    :return:
    """

    # TODO: I would like something like Javascript Promises instead of this pattern.
    json_results = None

    def find_json_results(node, _) -> None:
        if node.type == 'Property' and node.key.value == 'JsonResults':
            nonlocal json_results
            json_results = json_loads(node.value.value)

    async with session.get(url=f'{origin}/ecp/PersonalSettings/HomePage.aspx', **extra_request_keywords) as response:
        data = (await response.content.read()).decode()
        esprima_parse(
            code=pq(html_unescape(data))('script[type="text/javascript"]')[-1].text,
            delegate=find_json_results
        )

    # TODO: Reconsider return value. Return `json_results` instead?
    return json_results['Output'][0]


async def get_owa2010_usernames_from_ui(session: ClientSession, origin: str, num_concurrent: int = 10) -> Set[str]:
    """
    Extract usernames from the OWA 2010 contacts interface.

    :param session: An authenticated `aiohttp.ClientSession`.
    :param origin: The origin part of the URL of the OWA.
    :param num_concurrent: The number of concurrent sessions to use.
    :return: A set of all usernames in the contact list of the account associated with the authenticated session.
    """

    async with session.get(url=f'{origin}/owa/?ae=Dialog&t=AddressBook&ctx=1') as response:
        data = (await response.content.read()).decode()

        parsed_html_bs = BeautifulSoup(
            markup=html_unescape(data),
            features='html.parser'
        )

        form_data = {
            input_elem.attrs['name']: input_elem['value']
            for input_elem in parsed_html_bs.select('form#frm > input')
        }

    all_names = set()

    # TODO: To limit the number of requests, go into options and choose to show 100 items per page rather than 20
    #   Also, don't forget to restore the original value.

    async def work(worker_id: int):
        i = 0
        async with ClientSession(cookie_jar=session.cookie_jar) as worker_session:
            while True:
                request_options = dict(
                    url=f'{origin}/owa/?ae=Dialog&t=AddressBook&ctx=1',
                    data={**form_data, 'hidpg': worker_id + i * num_concurrent},
                    headers={'Connection': 'Keep-Alive'}
                )

                async with worker_session.post(**request_options) as response:
                    data = (await response.content.read()).decode()

                parsed_html_bs: BeautifulSoup = BeautifulSoup(
                    markup=html_unescape(data),
                    features='html.parser'
                )

                page_names = {
                    td.text.rstrip()
                    for td in parsed_html_bs.select(selector='table.lvw > tr:nth-child(n+4) > td:nth-child(3)')
                    if td.text.rstrip()
                }

                if len(page_names) == 0:
                    break

                all_names.update(page_names)

                i += 1

    await asyncio_gather(*(work(worker_id) for worker_id in range(num_concurrent)))

    return all_names
