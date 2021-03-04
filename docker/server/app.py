from flask import Flask
from peloton import refresh, Analysis

app = Flask(__name__)


@app.route('/')
def get_personal_stats():
    refresh()
    analysis = Analysis()
    return f'You have exercised {analysis.accumulated_minutes:,} minutes so far this year.\n'\
           f'We estimate you will complete {int(analysis.eoy_estimate):,} minutes this year.\n'\
           f'Current daily streak is {analysis.current_daily_streak:,} days.\n'\
           f'Current weekly streak is {analysis.current_weekly_streak:,} weeks.\n'


if __name__ == '__main__':
    app.run()
