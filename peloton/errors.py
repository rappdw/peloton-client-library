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
