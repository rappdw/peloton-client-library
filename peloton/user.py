from .api import PelotonAPI
from .object import PelotonObject


class PelotonUser(PelotonObject):
    """ Read-Only class that describes a Peloton User

    This class should never be invoked directly

    TODO: Flesh this out
    """

    def __init__(self, **kwargs):

        self.username = kwargs.get('username')
        self.id = kwargs.get('id')
        self.customized_max_heart_rate = kwargs.get('customized_max_heart_rate')
        self.estimated_cycling_ftp = kwargs.get('estimated_cycling_ftp')
        self.cycling_ftp = kwargs.get('cycling_ftp')
        self.cycling_workout_ftp = kwargs.get('cycling_workout_ftp')
        self.customized_heart_rate_zones = kwargs.get('customized_heart_rate_zones')
        self.default_heart_rate_zones = kwargs.get('default_heart_rate_zones')

        PelotonObject.cache_result('user', self.id, kwargs)

    def __str__(self):
        return self.username


class PelotonUserFactory(PelotonAPI):
    """ Class to handle fetching and transformation of metric data
    """

    @classmethod
    def me(cls):
        """ Get user details. This requires two calls as some of the data isn't present in either call, so
        merge the json results before initializing a PelotonUser
        """

        # get the user id for the first api call
        if cls.user_id is None:
            cls._create_api_session()

        uri = '/api/user/{}'.format(cls.user_id)
        user_results = cls._api_request(uri).json()

        uri = '/api/me'
        me_results = PelotonAPI._api_request(uri).json()
        return PelotonUser(**{**me_results, **user_results})
