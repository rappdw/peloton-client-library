import panel as pn # see: https://discourse.bokeh.org/t/custom-model-not-found-when-used-with-bokeh-client-pull-session/6266/3
from flask import Flask, render_template
from peloton import refresh, Analysis
from bokeh.client import pull_session
from bokeh.embed import server_session


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def get_personal_stats():
    refresh()
    analysis = Analysis()
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
    with pull_session(url="http://localhost:5006/") as session:
        # generate a script to load the customized session
        script = server_session(session_id=session.id, url='http://localhost:5006')
        # use the script in the rendered page
        return render_template("projection.html", script=script, template="Flask")

if __name__ == '__main__':
    app.run()
