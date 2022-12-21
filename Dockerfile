# syntax=docker/dockerfile:1
# Walt Lillyman, 12/15/22

# Build a container starting from python, adding the requests module. 
# When instanciated, it will run the python script:

FROM python:3.10-slim-bullseye
RUN pip install requests
WORKDIR /usr/src/app
CMD python nhl_goal_alert.py
