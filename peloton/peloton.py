#! /usr/bin/env python3.6
# -*- coding: latin-1 -*-

import requests
import decimal
import json

from datetime import datetime
from datetime import timezone
from datetime import date
from typing import Dict
from pytz import timezone

from .version import __version__
from .config import Config, get_logger

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


class NotLoaded:
    """ In an effort to avoid pissing Peloton off, we lazy load as often
        as possible. This class is utitilzed frequently within this module
        to indicate when data can be retrieved, as requested
    """
    pass


class DataMissing:
    """ Used to indicate that data is missing (eg: no h/r monitor used)
    """
    pass


class PelotonException(Exception):
    """ This is our base exception class, that all other
        exceptions inherit from
    """
    pass


class PelotonClientError(PelotonException):
    """ Client exception class
    """

    def __init__(self, message, response):
        super(PelotonException, self).__init__(self, message)
        self.message = message
        self.response = response


class PelotonServerError(PelotonException):
    """ Server exception class
    """

    def __init__(self, message, response):
        super(PelotonException, self).__init__(self, message)
        self.message = message
        self.response = response


class PelotonRedirectError(PelotonException):
    """ Maybe we'll see weird unexpected redirects?
    """

    def __init__(self, message, response):
        super(PelotonException, self).__init__(self, message)
        self.message = message
        self.response = response


class PelotonObject:
    """ Base class for all Peloton data
    """

    def serialize(self, depth=1, load_all=True):
        """Ensures that everything has a .serialize() method
           so that all data is serializable

        Args:
            depth: level of nesting to include when serializing
            load_all: whether or not to include lazy loaded
                      data (eg: NotLoaded() instances)
        """

        # Dict to hold our returnable data
        ret = {}

        # Dict to hold the attributes of $.this object
        obj_attrs = {}

        # If we hit our depth limit, return
        if depth == 0:
            return None

        # List of keys that we will not be included in our serializable
        # output based on load_all
        dont_load = []

        # Load our NotLoaded() (lazy loading) instances if we're
        # requesting to do so
        for k in self.__dict__:
            if load_all:
                obj_attrs[k] = getattr(self, k)
                continue

            # Don't include lazy loaded attrs
            raw_value = super(PelotonObject, self).__getattribute__(k)
            if isinstance(raw_value, NotLoaded):
                dont_load.append(k)

        # We've gone through our pre-flight prep, now lets actually
        # serialize our data
        for k, v in obj_attrs.items():

            # Ignore this key if it's in our dont_load list or is private
            if k.startswith('_') or k in dont_load:
                continue

            if isinstance(v, PelotonObject):
                if depth > 1:
                    ret[k] = v.serialize(depth=depth - 1)

            elif isinstance(v, list):
                serialized_list = []

                for val in v:
                    if isinstance(val, PelotonObject):
                        if depth > 1:
                            serialized_list.append(
                                val.serialize(depth=depth - 1))

                    elif isinstance(val, (datetime, date)):
                        serialized_list.append(val.isoformat())

                    elif isinstance(val, decimal.Decimal):
                        serialized_list.append("%.1f" % val)

                    elif isinstance(val, (str, int, dict)):
                        serialized_list.append(val)

                # Only add if we have data (this _can_ be an empty list
                # in the event that our list is noting but
                #   PelotonObject's and we're at/past our recursion depth)
                if serialized_list:
                    ret[k] = serialized_list

                # If v is empty, return an empty list
                elif not v:
                    ret[k] = []

            else:
                if isinstance(v, (datetime, date)):
                    ret[k] = v.isoformat()

                elif isinstance(v, decimal.Decimal):
                    ret[k] = "%.1f" % v

                else:
                    ret[k] = v

        # We've got a python dict now, so lets return it
        return ret


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

        cache_result('user', self.id, kwargs)


    def __str__(self):
        return self.username

    @classmethod
    def me(cls):
        return PelotonUserFactory.me()



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
        self.ride = NotLoaded()
        if kwargs.get('ride') is not None:
            self.ride = PelotonRide(timezone=tz, **kwargs.get('ride'))
            # as creating the PelotonRide object will have cached the ride, don't double cache it
            # replace the "ride" in the json results with the ride id
            kwargs['ride'] = self.ride.id

        cache_result('workout', self.id, kwargs)

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
        self.metrics = kwargs.get('metrics', NotLoaded())

        # Leaderboard stats need to call PelotonWorkoutFactory to get
        # these two bits
        self.leaderboard_rank = kwargs.get('leaderboard_rank', NotLoaded())
        self.leaderboard_users = kwargs.get(
            'total_leaderboard_users', NotLoaded())
        self.personal_record = kwargs.get(
            'is_total_work_personal_record', NotLoaded())

        # List of achievements that were obtained during this workout
        achievements = kwargs.get('achievement_templates', NotLoaded())
        if not isinstance(achievements, NotLoaded):
            self.achievements = []
            for achievement in achievements:
                self.achievements.append(
                    PelotonWorkoutAchievement(**achievement))

    def __str__(self):
        return self.fitness_discipline

    def __getattribute__(self, attr):

        value = object.__getattribute__(self, attr)

        # Handle accessing NotLoaded attributes (yay lazy loading)
        #   TODO: Handle ride laoding if its NotLoaded()
        if attr in ['leaderboard_rank', 'leaderboard_users',
                    'achievements', 'metrics'] and type(value) is NotLoaded:

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
        """ Returns the lastest workout object
        """
        return PelotonWorkoutFactory.latest()


class PelotonRide(PelotonObject):
    """ A read-only class that defines a ride (workout class)

    This class should never be invoked directly!
    """

    def __init__(self, timezone, **kwargs):
        '''
        create a Peloton Ride from the JSON returned by the API

        :param timezone: the timezone of the workout from which the Ride was taken
        '''

        self.title = kwargs.get('title')
        self.id = kwargs.get('id')
        self.description = kwargs.get('description')
        self.duration = kwargs.get('duration')
        self.difficulty_rating_avg = kwargs.get('difficulty_rating_avg')
        self.difficulty_rating_count = kwargs.get('difficulty_rating_count')
        self.difficulty_estimate = kwargs.get('difficulty_estimate')
        self.difficulty_level = kwargs.get('difficulty_level')
        self.fitness_discipline = kwargs.get('fitness_discipline')
        self.original_air_time = datetime.fromtimestamp(kwargs.get('original_air_time', 0), timezone)
        self.title = kwargs.get('title')

        # When we make this Ride call from the workout factory, there
        # is no instructor data
        if kwargs.get('instructor') is not None:
            self.instructor = PelotonInstructor(**kwargs.get('instructor'))
            # as creating the PelotonInstructor object will have cached the instructor, don't double cache it
            # replace the "instructor" in the json results with the instructor id
            kwargs['instructor'] = self.instructor.id

        cache_result('ride', self.id, kwargs)

    def __str__(self):
        return self.title

    @classmethod
    def get(cls, ride_id):
        raise NotImplementedError()


class PelotonMetric(PelotonObject):
    """ A read-only class that outlines some simple metric information
        about the workout
    """

    def __init__(self, **kwargs):

        self.values = kwargs.get('values')
        self.average = kwargs.get('average_value')
        self.name = kwargs.get('display_name')
        self.unit = kwargs.get('display_unit')
        self.max = kwargs.get('max_value')
        self.slug = kwargs.get('slug')

    def __str__(self):
        return "{} ({})".format(self.name, self.unit)


class PelotonMetricSummary(PelotonObject):
    """ An object that describes a summary of a metric set
    """

    def __init__(self, **kwargs):

        self.name = kwargs.get('display_name')
        self.value = kwargs.get('value')
        self.unit = kwargs.get('display_unit')
        self.slug = kwargs.get('slug')

    def __str__(self):
        return "{} ({})".format(self.name, self.unit)


class PelotonWorkoutMetrics(PelotonObject):
    """ An object that describes all of the metrics of a given workout
    """

    def __init__(self, **kwargs):
        """ Take a metrics set and objectify it
        :param id: the id of the workout for which these metrics are associated
        """

        cache_result('metrics', kwargs.get('id'), kwargs)

        self.workout_duration = kwargs.get('duration')
        self.fitness_discipline = kwargs.get('segment_list')[0]['metrics_type'] if len(
            kwargs.get('segment_list')) else ''

        # Build summary attributes
        metric_summaries = ['total_output', 'distance', 'calories']
        for metric in kwargs.get('summaries'):
            if metric['slug'] not in metric_summaries:
                get_logger().warning(
                    "Unknown metric summary {} found".format(metric['slug']))
                continue

            attr_name = metric['slug'] + '_summary'
            if metric['slug'] == "total_output":
                attr_name = "output_summary"

            setattr(self, attr_name, PelotonMetricSummary(**metric))

        # Build metric details
        metric_categories = [
            'output', 'cadence', 'resistance', 'speed', 'heart_rate']
        for metric in kwargs.get('metrics'):

            if metric['slug'] not in metric_categories:
                get_logger().warning(
                    "Unknown metric category {} found".format(metric['slug']))
                continue

            setattr(self, metric['slug'], PelotonMetric(**metric))

    def __str__(self):
        return self.fitness_discipline


class PelotonInstructor(PelotonObject):
    """ A read-only class that outlines instructor details

    This class should never be invoked directly"""

    def __init__(self, **kwargs):

        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.music_bio = kwargs.get('music_bio')
        self.spotify_playlist_uri = kwargs.get('spotify_playlist_uri')
        self.bio = kwargs.get('bio')
        self.quote = kwargs.get('quote')
        self.background = kwargs.get('background')
        self.short_bio = kwargs.get('short_bio')

        cache_result('instructor', self.id, kwargs)


    def __str__(self):
        return self.name


class PelotonWorkoutSegment(PelotonObject):
    """ A read-only class that outlines instructor details

        This class should never be invoked directly"""

    def __init__(self):
        raise NotImplementedError()


class PelotonWorkoutAchievement(PelotonObject):
    """ Class that represents a single achievement that a user
        earned during the workout
    """

    def __init__(self, **kwargs):

        self.slug = kwargs.get('slug')
        self.description = kwargs.get('description')
        self.image_url = kwargs.get('image_url')
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')


class PelotonWorkoutFactory(PelotonAPI):
    """ Class that handles fetching data and instantiating objects

    See PelotonWorkout for details
    """

    @classmethod
    def check_for_last_id(cls, workouts, last_id):
        '''
        checks to see if the terminal id is in the workout block
        :return index to halt iteration (or len of workout block if id not found)
        '''
        if last_id:
            for idx, workout in enumerate(workouts):
                if workout['id'] == last_id:
                    return idx - 1
        return len(workouts)

    @classmethod
    def list(cls, last_id=None, results_per_page=10):
        """ Return a list of PelotonWorkout instances that describe
            each workout

            :param last_id: if this isn't None, then the id of the workout not to iterate past when paging through results
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

