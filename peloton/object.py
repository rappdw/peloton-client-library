import decimal
import json

from .api import config
from typing import Dict
from datetime import date, datetime


class PelotonObject:
    """ Base class for all Peloton data
    """

    class NotLoaded:
        """ In an effort to avoid pissing Peloton off, we lazy load as often
            as possible. This class is utilized frequently within this module
            to indicate when data can be retrieved, as requested
        """
        pass

    class DataMissing:
        """ Used to indicate that data is missing (eg: no h/r monitor used)
        """
        pass

    @staticmethod
    def cache_result(obj_type: str, obj_id: str, result: Dict):
        """
        if a data cache directory exists, writhe the json out for th
        """
        if config.DATA_CACHE_DIR:
            cache_dir = config.DATA_CACHE_DIR / obj_type
            cache_dir.mkdir(parents=True, exist_ok=True)
            file = cache_dir / f'{obj_id}.json'
            with open(file, 'w') as fp:
                json.dump(result, fp, indent=2, sort_keys=True)

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
            if isinstance(raw_value, self.NotLoaded):
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
