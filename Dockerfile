# syntax=docker/dockerfile:1
# Walt Lillyman, 12/15/22

# Build an image starting from python, adding the module(s) in requirements.txt. 
# When instanciated, the container will run the python script and terminate when the script finishes:

FROM python:slim
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /usr/src/app
CMD [ "python",  "./nhl_goal_alert.py" ]
