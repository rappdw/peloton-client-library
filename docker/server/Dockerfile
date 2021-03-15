FROM python:3.9.2-slim

RUN mkdir -p /peloton
RUN mkdir -p /Users/drapp/dev/peloton-data
RUN mkdir -p /peloton-server

COPY ./ /peloton/
COPY ./docker/server/app /peloton-server

RUN pip install \
        /peloton \
        flask \
        panel \
        holoviews \
        bokeh \
    ;

RUN apt-get update; \
    apt-get install -y \
        curl \
        less \
    ; \
    apt-get clean; \
    rm -rf /var/tmp/* /tmp/* /var/lib/apt/lists/*

WORKDIR /peloton-server
ENTRYPOINT ["/peloton-server/startup.sh"]

# see: https://stackoverflow.com/questions/30323224/deploying-a-minimal-flask-app-in-docker-server-connection-issues/43015007#43015007
