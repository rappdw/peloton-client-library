from flask import Flask, render_template
from peloton import refresh, Analysis

app = Flask(__name__)


@app.route('/')
def get_personal_stats():
    refresh()
    analysis = Analysis()
    return render_template(
        'stats.html',
        yearly = {
           'accumulated_minutes': analysis.accumulated_minutes,
           'eoy_estimate': int(analysis.eoy_estimate)
        },
        streak = {
            'daily': analysis.current_daily_streak,
            'weekly': analysis.current_weekly_streak
        }
    )


if __name__ == '__main__':
    app.run()
