#! /usr/bin/env python3

import holoviews as hv
import panel as pn
import numpy as np
import pandas as pd

from datetime import datetime
from peloton import Analysis
from holoviews import opts

hv.extension('bokeh')

def sine(frequency, phase, amplitude):
    xs = np.linspace(0, np.pi*4)
    return hv.Curve((xs, np.sin(frequency*xs+phase)*amplitude)).options(width=800)

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
    series.drop_duplicates('device_time_created_at', keep='last')
    series['eoy_estimate'] = ((series.mins2 / series.doy * days_in_year).round()).astype(int)

    curve = hv.Curve(series, ('doy', 'Day of Year'), ('eoy_estimate', 'Projection'))
    goal = hv.HLine(15000).opts(opts.HLine(color='green', line_width=1))
    goal1 = hv.HLine(14000).opts(opts.HLine(color='orange', line_width=1))
    goal2 = hv.HLine(13000).opts(opts.HLine(color='red', line_width=1))
    plot = (curve * goal * goal1 * goal2)
    return plot

if __name__ == '__main__':
    # ranges = dict(frequency=(1, 5), phase=(-np.pi, np.pi), amplitude=(-2, 2), y=(-2, 2))
    # dmap = hv.DynamicMap(sine, kdims=['frequency', 'phase', 'amplitude']).redim.range(**ranges)
    plot = yearly_projection()
    pn.serve(plot, port=5006, allow_websocket_origin=["localhost:5000"], show=False)
#    pn.serve(dmap, port=5006, show=False)
