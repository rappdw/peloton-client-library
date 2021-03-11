from datetime import datetime
from .instructor import PelotonInstructor
from .object import PelotonObject


class PelotonRide(PelotonObject):
    """ A read-only class that defines a ride (workout class)

    This class should never be invoked directly!
    """

    def __init__(self, tz, **kwargs):
        """
        create a Peloton Ride from the JSON returned by the API

        :param tz: the timezone of the workout from which the Ride was taken
        """

        self.title = kwargs.get('title')
        self.id = kwargs.get('id')
        self.description = kwargs.get('description')
        self.duration = kwargs.get('duration')
        self.difficulty_rating_avg = kwargs.get('difficulty_rating_avg')
        self.difficulty_rating_count = kwargs.get('difficulty_rating_count')
        self.difficulty_estimate = kwargs.get('difficulty_estimate')
        self.difficulty_level = kwargs.get('difficulty_level')
        self.fitness_discipline = kwargs.get('fitness_discipline')
        self.original_air_time = datetime.fromtimestamp(kwargs.get('original_air_time', 0), tz)
        self.title = kwargs.get('title')

        # When we make this Ride call from the workout factory, there
        # is no instructor data
        if kwargs.get('instructor') is not None:
            self.instructor = PelotonInstructor(**kwargs.get('instructor'))
            # as creating the PelotonInstructor object will have cached the instructor, don't double cache it
            # replace the "instructor" in the json results with the instructor id
            kwargs['instructor'] = self.instructor.id

        PelotonObject.cache_result('ride', self.id, kwargs)

    def __str__(self):
        return self.title

    @classmethod
    def get(cls, ride_id):
        raise NotImplementedError()
