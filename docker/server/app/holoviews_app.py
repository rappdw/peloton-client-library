#! /usr/bin/env python3

import holoviews as hv
import panel as pn
import pandas as pd

from datetime import datetime
from peloton import Analysis
from holoviews import opts

hv.extension('bokeh')

def yearly_projection():
    analysis = Analysis()
    now = datetime.now()
    current_year = now.year
    days_in_year = datetime(now.year, 12, 31, 0, 0).timetuple().tm_yday

    workouts_for_year = analysis.get_printable_workouts().loc[f'{current_year}'].sort_index(ascending=True)

    series = workouts_for_year.mins2.cumsum()
    series = pd.DataFrame(series)
    series.reset_index(inplace=True)
    series['doy'] = series.device_time_created_at.dt.dayofyear
    series.device_time_created_at = series.device_time_created_at.dt.date
    series = series.drop_duplicates(subset=['device_time_created_at'], keep='last')
    series['eoy_estimate'] = ((series.mins2 / series.doy * days_in_year).round()).astype(int)

    curve = hv.Curve(series, ('doy', 'Day of Year'), ('eoy_estimate', 'Projection'))
    goal = hv.HLine(15000).opts(opts.HLine(color='green', line_width=1))
    goal1 = hv.HLine(14000).opts(opts.HLine(color='orange', line_width=1))
    goal2 = hv.HLine(13000).opts(opts.HLine(color='red', line_width=1))
    plot = (curve * goal * goal1 * goal2)
    return plot

if __name__ == '__main__':
    # https://bokeh.pydata.org/en/latest/docs/user_guide/server.html#embedding-bokeh-server-as-a-library
    plot = yearly_projection()
    pn.serve(plot, port=8889, allow_websocket_origin=["*"], show=False)
