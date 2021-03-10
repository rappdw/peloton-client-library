import requests
import json

from typing import Dict

from .config import Config, get_logger
from .errors import PelotonRedirectError, PelotonClientError, PelotonServerError
from .version import __version__

# Set our base URL location
_BASE_URL = 'https://api.onepeloton.com'

# Being friendly, let Peloton know who we are (eg: not the web ui)
_USER_AGENT = "peloton-client-library/{}".format(__version__)

config = Config()

def find_last_workout():
    '''
    if a data cache directory exists, find the most recent workout for which there exists cached data
    '''
    id = None
    if config.DATA_CACHE_DIR:
        cache = config.DATA_CACHE_DIR / 'workout'
        most_resent = 0
        for file in cache.glob('**/*.json'):
            with open(file, 'r') as fp:
                workout = json.load(fp)
                if workout['created'] > most_resent:
                    most_resent = workout['created']
                    id = workout['id']
    return id


def cache_result(type:str, id:str, result:Dict):
    '''
    if a data cache directory exists, writhe the json out for th
    '''
    if config.DATA_CACHE_DIR:
        dir = config.DATA_CACHE_DIR / type
        dir.mkdir(parents=True, exist_ok=True)
        file = dir / f'{id}.json'
        with open(file, 'w') as fp:
            json.dump(result, fp, indent=2, sort_keys=True)


class PelotonAPI:
    """ Base class that factory classes within this module inherit from.
    This class is _not_ meant to be utilized directly, so don't do it.

    Core "working" class of the Peolton API Module
    """

    peloton_username = None
    peloton_password = None

    # Hold a request.Session instance that we're going to
    # rely on to make API calls
    peloton_session = None

    # Being friendly (by default), use the same page size
    # that the Peloton website uses
    page_size = 10

    # Hold our user ID (pulled when we authenticate to the API)
    user_id = None

    # Headers we'll be using for each request
    headers = {
        "Content-Type": "application/json",
        "User-Agent": _USER_AGENT
    }

    @classmethod
    def _api_request(cls, uri, params=None):
        """ Base function that everything will use under the hood to
            interact with the API

        Returns a requests response instance, or raises an exception on error
        """

        if params is None:
            params = {}

        # Create a session if we don't have one yet
        if cls.peloton_session is None:
            cls._create_api_session()

        get_logger().debug("Request {} [{}]".format(_BASE_URL + uri, params))
        resp = cls.peloton_session.get(
            _BASE_URL + uri, headers=cls.headers, params=params)
        get_logger().debug("Response {}: [{}]".format(
            resp.status_code, resp._content))

        # If we don't have a 200 code
        if not (200 >= resp.status_code < 300):

            message = resp._content

            if 300 <= resp.status_code < 400:
                raise PelotonRedirectError("Unexpected Redirect", resp)

            elif 400 <= resp.status_code < 500:
                raise PelotonClientError(message, resp)

            elif 500 <= resp.status_code < 600:
                raise PelotonServerError(message, resp)

        return resp

    @classmethod
    def _create_api_session(cls):
        """ Create a session instance for communicating with the API
        """

        if cls.peloton_username is None:
            cls.peloton_username = config.PELOTON_USERNAME

        if cls.peloton_password is None:
            cls.peloton_password = config.PELOTON_PASSWORD

        if cls.peloton_username is None or cls.peloton_password is None:
            raise PelotonClientError(
                "The Peloton Client Library requires a `username` "
                "and `password` be set in "
                "`/.config/peloton, under section `peloton`", None)

        payload = {
            'username_or_email': cls.peloton_username,
            'password': cls.peloton_password
        }

        cls.peloton_session = requests.Session()
        resp = cls.peloton_session.post(
            _BASE_URL + '/auth/login', json=payload, headers=cls.headers)
        message = resp._content

        if 300 <= resp.status_code < 400:
            raise PelotonRedirectError("Unexpected Redirect", resp)

        elif 400 <= resp.status_code < 500:
            raise PelotonClientError(message, resp)

        elif 500 <= resp.status_code < 600:
            raise PelotonServerError(message, resp)

        # Set our User ID on our class
        cls.user_id = resp.json()['user_id']