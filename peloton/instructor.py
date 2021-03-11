from .object import PelotonObject


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

        PelotonObject.cache_result('instructor', self.id, kwargs)

    def __str__(self):
        return self.name
