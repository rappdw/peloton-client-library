from flask import Flask
from peloton import refresh, Analysis

app = Flask(__name__)


@app.route('/')
def get_personal_stats():
    refresh()
    analysis = Analysis()
    return f'<!DOCTYPE html>' \
           f'<html>' \
           f'<body>You have exercised {analysis.accumulated_minutes:,} minutes so far this year.<br/>'\
           f'We estimate you will complete {int(analysis.eoy_estimate):,} minutes this year.<br/><br/>'\
           f'Current daily streak is {analysis.current_daily_streak:,} days.<br/>'\
           f'Current weekly streak is {analysis.current_weekly_streak:,} weeks.<br/>'\
            '</body></html>'


if __name__ == '__main__':
    app.run()
