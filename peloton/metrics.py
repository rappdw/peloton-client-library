from .config import get_logger
from .object import PelotonObject


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


class PelotonWorkoutMetrics(PelotonObject):
    """ An object that describes all of the metrics of a given workout
    """

    def __init__(self, **kwargs):
        """ Take a metrics set and objectify it
        :param id: the id of the workout for which these metrics are associated
        """

        PelotonObject.cache_result('metrics', kwargs.get('id'), kwargs)

        self.workout_duration = kwargs.get('duration')
        self.fitness_discipline = kwargs.get('segment_list')[0]['metrics_type'] if len(
            kwargs.get('segment_list')) else ''

        # Build summary attributes
        metric_summaries = ['total_output', 'distance', 'calories', 'elevation']
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
            'output', 'cadence', 'resistance', 'speed', 'heart_rate', 'pace', 'incline', 'altitude']
        for metric in kwargs.get('metrics'):

            if metric['slug'] not in metric_categories:
                get_logger().warning(
                    "Unknown metric category {} found".format(metric['slug']))
                continue

            setattr(self, metric['slug'], PelotonMetric(**metric))

    def __str__(self):
        return self.fitness_discipline


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
