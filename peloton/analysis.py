import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from .config import Config


def _retrieve(directory, id = None):
    objs = {}
    for file in directory.iterdir():
        if id is None or file.stem == id:
            with open(file, 'r') as fp:
                objs[file.stem] = json.load(fp)
    return objs


class Analysis:

    # for some reason, my calculation of workout time for the year is 6 minutes greater than Peloton's, allow a
    # fudge_factor to reconcile this
    def __init__(self, cache_dir: Path = None, fudge_factor: int = -5):
        if cache_dir is None:
            cache_dir = Config().DATA_CACHE_DIR

        self.workouts = _retrieve(cache_dir / 'workout')
        # self.instructors = _retrieve(cache_dir / 'instructor')
        # self.rides = _retrieve(cache_dir / 'ride')
        self.users = _retrieve(cache_dir / 'user')
        # self.metrics = _retrieve(cache_dir / 'metrics')
        self.annual_challenge = _retrieve(cache_dir / 'challenge', '4ee56696ffcb442592607af5004503e3')

        self.wdf = self._update_workouts(pd.DataFrame(self.workouts.values()))
        # self.rdf = pd.DataFrame(self.rides.values())
        # self.idf = pd.DataFrame(self.instructors.values())

        self.current_daily_streak = self._get_current_streak_in_days()
        user = next(iter(self.users.values()))
        self.current_weekly_streak = user['streaks']['current_weekly']

        now = datetime.now()
        day_of_year = now.timetuple().tm_yday
        days_in_year = datetime(now.year, 12, 31, 0, 0).timetuple().tm_yday

        # pdf = self.get_printable_dataframe(self.wdf, self.rdf, self.idf)
        # pdf = pdf.loc[f'{now.year}'].sort_index(ascending=False)
        #
        # self.accumulated_minutes = (pdf.duration.sum() // 60) + fudge_factor
        self.accumulated_minutes = self.annual_challenge['4ee56696ffcb442592607af5004503e3']['progress']['metric_value']
        self.eoy_estimate = self.accumulated_minutes / day_of_year * days_in_year

    def get_printable_workouts(self):
        return self.get_printable_dataframe(self.wdf, self.rdf, self.idf)

    @staticmethod
    def _update_workouts(df):
        # add/update columns to provide basis of interesting calculations, e.g. streaks, progress towards yearly
        # achievement, etc.
        # convert unix timestamp to datetime
        df['created'] = pd.to_datetime(df.created, unit='s', utc=True)
        df['device_time_created_at'] = pd.to_datetime(df.device_time_created_at, unit='s', utc=True)
        # calculate duration of workout (in seconds)
        df['duration'] = df.end_time - df.start_time
        return df

    # see: https://stackoverflow.com/questions/40775982/pandas-count-consecutive-dates-in-a-row-from-start-position
    def _get_current_streak_in_days(self):
        # TODO: if the latest work out isn't today or yesterday, streak should be 0 or 1
        d = pd.Timedelta(1, 'D')
        stretch = self.wdf.sort_values(
            'device_time_created_at',
            ascending=False,
            ignore_index=True
        )[['device_time_created_at']]
        stretch['date'] = stretch.device_time_created_at.dt.date
        consecutive = stretch.date.diff().abs().le(d)[1:].idxmin(axis=1)
        return (datetime.now().date() - stretch[consecutive - 1:consecutive].date.iloc[0]).days + 1

    @staticmethod
    def get_printable_dataframe(df, rdf, idf, df_fields=None, rdf_fields=None, idf_fields=None):
        if df_fields is None:
            df_fields = ['id', 'ride', 'duration', 'device_time_created_at']
        if rdf_fields is None:
            rdf_fields = ['ride', 'instructor_id', 'title']
        if idf_fields is None:
            idf_fields = ['instructor_id', 'name']

        rdf = rdf.rename({'id': 'ride'}, axis=1)
        idf = idf.rename({'id': 'instructor_id'}, axis=1)
        pdf = pd.merge(df[df_fields],
                       rdf[rdf_fields],
                       on='ride')
        pdf = pd.merge(pdf, idf[idf_fields], on='instructor_id')
        pdf = pdf.drop(['ride', 'instructor_id'], axis=1)
        pdf = pdf.set_index(['device_time_created_at'])

        pdf['mins'] = pdf.duration // 60
        pdf['mins2'] = pdf.duration / 60
        return pdf
