from .object import PelotonObject


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
