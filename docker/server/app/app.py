# see: https://discourse.bokeh.org/t/custom-model-not-found-when-used-with-bokeh-client-pull-session/6266/3
# noinspection PyUnresolvedReferences
import panel as pn
import os
import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from peloton import refresh, Analysis
from bokeh.client import pull_session
from bokeh.embed import server_session


app = FastAPI()
server_ip = os.getenv("BOKEH_SERVER", "localhost")
templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    # noinspection PyUnresolvedReferences
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/update', response_class=HTMLResponse)
def update(request: Request):
    workouts = refresh()
    # noinspection PyUnresolvedReferences
    return templates.TemplateResponse('update.html', {"request": request, "workouts": workouts})


@app.get('/stats', response_class=HTMLResponse)
def get_personal_stats(request: Request):
    analysis = Analysis()
    # noinspection PyUnresolvedReferences
    return templates.TemplateResponse(
        'stats.html',
        {
            "request": request,
            "yearly": {
                'initial_ave_required': analysis.initial_average_required,
                'ave_to_date': analysis.average_to_date,
                'remaining_ave_required': analysis.remaining_average_required,
                'accumulated_minutes': int(analysis.accumulated_minutes),
                'remaining_minutes': analysis.remaining_minutes_required,
                'eoy_estimate': int(analysis.eoy_estimate)
            },
            "streak": {
                 'daily': analysis.current_daily_streak,
                 'weekly': analysis.current_weekly_streak
            }
        }
    )


@app.get('/projection', response_class=HTMLResponse)
def get_projection(request: Request):
    print(f"communicating with Bokeh server via: {server_ip}")
    with pull_session(url=f"http://{server_ip}:8889/") as session:
        # generate a script to load the customized session
        script = server_session(session_id=session.id, url=f"http://{server_ip}:8889")
        # use the script in the rendered page
        # noinspection PyUnresolvedReferences
        return templates.TemplateResponse("projection.html", {"request": request, "script": script})


if __name__ == '__main__':
#    app.run(port="8888")
    uvicorn.run("app:app", port="8888")
