#!/usr/bin/bash
# Walt Lillyman, 12/19/22

# Delete any existing container:
echo Stopping and deleting any existing container...
docker stop nhl_goal_alert > /dev/null 2>&1
docker container rm -f nhl_goal_alert > /dev/null 2>&1
echo Starting container...
# Run it as a detached daemon, it will terminate when it terminates. Don't auto-restart it:
docker run -d --name=nhl_goal_alert -v /home/walt/nhl_goal_alert:/usr/src/app --env-file ./envvars.txt nhl_goal_alert
