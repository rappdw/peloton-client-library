from datetime import datetime, timezone
from pytz import timezone

from .achievement import PelotonWorkoutAchievement
from .api import PelotonAPI
from .object import PelotonObject
from .metrics import PelotonWorkoutMetrics
from .ride import PelotonRide


class PelotonWorkout(PelotonObject):
    """ A read-only class that defines a workout instance/object

    This class should never be instantiated directly!
    """

    def __init__(self, **kwargs):
        """ This class is instantiated by
        PelotonWorkout.get()
        PelotonWorkout.list()
        """
        self.id = kwargs.get('id')

        # get timezone of workout
        tz = timezone(kwargs.get('timezone'))

        # This is a bit weird, we can only get ride details if they
        # come up from a users workout list via a join
        self.ride = self.NotLoaded()
        if kwargs.get('ride') is not None:
            self.ride = PelotonRide(tz=tz, **kwargs.get('ride'))
            # as creating the PelotonRide object will have cached the ride, don't double cache it
            # replace the "ride" in the json results with the ride id
            kwargs['ride'] = self.ride.id

        PelotonObject.cache_result('workout', self.id, kwargs)

        # Not entirely certain what the difference is between these two fields
        self.created = datetime.fromtimestamp(kwargs.get('created', 0), tz)
        self.created_at = datetime.fromtimestamp(kwargs.get('created_at', 0), tz)

        # Time duration of this ride
        self.start_time = datetime.fromtimestamp(kwargs.get('start_time', 0), tz)
        self.end_time = datetime.fromtimestamp(int(kwargs.get('end_time', 0) or 0), tz)

        # What exercise type is this?
        self.fitness_discipline = kwargs.get('fitness_discipline')

        # Workout status (complete, in progress, etc)
        self.status = kwargs.get('status')

        # Load up our metrics (since we're joining for them anyway)
        self.metrics_type = kwargs.get('metrics_type')
        self.metrics = kwargs.get('metrics', self.NotLoaded())

        # Leaderboard stats need to call PelotonWorkoutFactory to get
        # these two bits
        self.leaderboard_rank = kwargs.get('leaderboard_rank', self.NotLoaded())
        self.leaderboard_users = kwargs.get(
            'total_leaderboard_users', self.NotLoaded())
        self.personal_record = kwargs.get(
            'is_total_work_personal_record', self.NotLoaded())

        # List of achievements that were obtained during this workout
        achievements = kwargs.get('achievement_templates', self.NotLoaded())
        if not isinstance(achievements, self.NotLoaded):
            self.achievements = []
            for achievement in achievements:
                self.achievements.append(
                    PelotonWorkoutAchievement(**achievement))

    def __str__(self):
        return self.fitness_discipline

    def __getattribute__(self, attr):

        value = object.__getattribute__(self, attr)

        # Handle accessing NotLoaded attributes (yay lazy loading)
        #   TODO: Handle ride loading if its NotLoaded()
        if attr in ['leaderboard_rank', 'leaderboard_users',
                    'achievements', 'metrics'] and type(value) is self.NotLoaded:

            if attr.startswith('leaderboard_') or attr == 'achievements':\

                # Yes, this gets a bunch of duplicate data, but the
                # endpoints don't return consistent info!
                workout = PelotonWorkoutFactory.get(self.id)

                # Load leaderboard stats
                self.leaderboard_rank = workout.leaderboard_rank
                self.leaderboard_users = workout.leaderboard_users
                self.personal_record = workout.personal_record

                # Load our achievements
                self.achievements = workout.achievements

                # Return the value of the requested attribute
                return getattr(self, attr)

            # Metrics gets a dedicated conditional because it's a
            # different endpoint
            elif attr == "metrics":
                metrics = PelotonWorkoutMetricsFactory.get(self.id)
                self.metrics = metrics
                return metrics

        return value

    @classmethod
    def get(cls, workout_id):
        """ Get a specific workout
        """
        return PelotonWorkoutFactory.get(workout_id)

    @classmethod
    def list(cls, last_id=None):
        """ Return a list of all workouts

        :param last_id: if this isn't None, then the id of the workout not to iterate past when paging through results
        """
        return PelotonWorkoutFactory.list(last_id=last_id)

    @classmethod
    def latest(cls):
        """ Returns the latest workout object
        """
        return PelotonWorkoutFactory.latest()


class PelotonWorkoutFactory(PelotonAPI):
    """ Class that handles fetching data and instantiating objects

    See PelotonWorkout for details
    """

    @classmethod
    def check_for_last_id(cls, workouts, last_id):
        """
        checks to see if the terminal id is in the workout block
        :return index to halt iteration (or len of workout block if id not found)
        """
        if last_id:
            for idx, workout in enumerate(workouts):
                if workout['id'] == last_id:
                    return idx - 1
        return len(workouts)

    @classmethod
    def list(cls, last_id=None, results_per_page=10):
        """ Return a list of PelotonWorkout instances that describe
            each workout

            :param last_id: if this isn't None, then the id of the workout not to iterate past when paging
            through results
            :param results_per_page: number of results in a page
        """

        # We need a user ID to list all workouts. @pelotoncycle, please
        # don't do this :(
        if cls.user_id is None:
            cls._create_api_session()

        uri = '/api/user/{}/workouts'.format(cls.user_id)
        params = {
            'page': 0,
            'limit': results_per_page,
            'joins': 'ride,ride.instructor'
        }

        # Get our first page, which includes number of successive pages
        res = cls._api_request(uri, params).json()
        max_idx = cls.check_for_last_id(res['data'], last_id=last_id)

        # Add this pages data to our return list
        ret = [PelotonWorkout(**workout) for i, workout in enumerate(res['data']) if i <= max_idx]

        # We've got page 0, so start with page 1
        for i in range(1, res['page_count']):
            if max_idx != len(res['data']):
                break
            params['page'] += 1
            res = cls._api_request(uri, params).json()
            max_idx = cls.check_for_last_id(res['data'], last_id=last_id)
            [ret.append(PelotonWorkout(**workout)) for i, workout in enumerate(res['data']) if i <= max_idx]

        return ret

    @classmethod
    def get(cls, workout_id):
        """ Get workout details by workout_id
        """

        uri = '/api/workout/{}'.format(workout_id)
        workout = PelotonAPI._api_request(uri).json()
        return PelotonWorkout(**workout)

    @classmethod
    def latest(cls):
        """ Returns an instance of PelotonWorkout that represents
            the latest workout
        """

        # We need a user ID to list all workouts. @pelotoncycle, please
        # don't do this :(
        if cls.user_id is None:
            cls._create_api_session()

        uri = '/api/user/{}/workouts'.format(cls.user_id)
        params = {
            'page': 0,
            'limit': 1,
            'joins': 'ride,ride.instructor'
        }

        # Get our first page, which includes number of successive pages
        res = cls._api_request(uri, params).json()

        # Return our single workout, without having to get a bunch of
        # extra data from the API
        return PelotonWorkout(**res['data'][0])


class PelotonWorkoutMetricsFactory(PelotonAPI):
    """ Class to handle fetching and transformation of metric data
    """

    @classmethod
    def get(cls, workout_id):
        """ Returns a list of PelotonMetric instances for each metric type
        """

        uri = '/api/workout/{}/performance_graph'.format(workout_id)
        params = {
            'every_n': 1
        }

        res = cls._api_request(uri, params).json()
        res['id'] = workout_id
        return PelotonWorkoutMetrics(**res)
