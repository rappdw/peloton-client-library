from .api import PelotonAPI
from .object import PelotonObject


class PelotonChallenge(PelotonObject):
    """ Class that represents a single achievement that a user
        earned during the workout
    """

    def __init__(self, **kwargs):

        self.id = kwargs.get('challenge_summary').get('id')

        PelotonObject.cache_result('challenge', self.id, kwargs)

        self.progress_metric = kwargs.get('progress').get('metric_value')
        # TODO: flesh out


class PelotonChallengeFactory(PelotonAPI):
    """ Class that handles fetching data and instantiating objects

    See PelotonChallenge for details
    """

    @classmethod
    def list(cls):
        """ Return a list of PelotonChallenge instances that describe
            each Challenge
        """

        # We need a user ID to list challenges
        if cls.user_id is None:
            cls._create_api_session()

        uri = '/api/user/{}/challenges/current?has_joined=true'.format(cls.user_id)

        # Get our first page, which includes number of successive pages
        res = cls._api_request(uri).json()

        # Add this pages data to our return list
        ret = [PelotonChallenge(**challenge) for i, challenge in enumerate(res['challenges'])]

        return ret

    @classmethod
    def get(cls, challenge_id):
        """ Get challenge details by challenge_id
        """

        # We need a user ID to list challenges
        if cls.user_id is None:
            cls._create_api_session()

        uri = '/api/user/{}/challenge/{}'.format(cls.user_id, challenge_id)
        challenge = PelotonAPI._api_request(uri).json()
        return PelotonChallenge(**challenge)
