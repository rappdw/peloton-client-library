# see: https://discourse.bokeh.org/t/custom-model-not-found-when-used-with-bokeh-client-pull-session/6266/3
# noinspection PyUnresolvedReferences
import panel as pn
import os
from flask import Flask, render_template
from peloton import refresh, Analysis
from bokeh.client import pull_session
from bokeh.embed import server_session


app = Flask(__name__)
server_ip = os.getenv("BOKEH_SERVER", "localhost")


@app.route('/')
def index():
    # noinspection PyUnresolvedReferences
    return render_template('index.html')


@app.route('/update')
def update():
    workouts = refresh()
    # noinspection PyUnresolvedReferences
    return render_template('update.html', workouts=workouts)


@app.route('/stats')
def get_personal_stats():
    analysis = Analysis()
    # noinspection PyUnresolvedReferences
    return render_template(
        'stats.html',
        yearly={
           'accumulated_minutes': int(analysis.accumulated_minutes),
           'eoy_estimate': int(analysis.eoy_estimate)
        },
        streak={
            'daily': analysis.current_daily_streak,
            'weekly': analysis.current_weekly_streak
        }
    )


@app.route('/projection')
def get_projection():
    print(f"communicating with Bokeh server via: {server_ip}")
    with pull_session(url=f"http://{server_ip}:8889/") as session:
        # generate a script to load the customized session
        script = server_session(session_id=session.id, url=f"http://{server_ip}:8889")
        # use the script in the rendered page
        # noinspection PyUnresolvedReferences
        return render_template("projection.html", script=script, template="Flask")


if __name__ == '__main__':
    app.run(port="8888")
