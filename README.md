# nhl_goal_alert

## Description
Python 3.10 script that polls the unofficial NHL API for changes in the score of one team for a game in progress.
When [my team](https://www.nhl.com/blues/) scores a goal, invoke a webhook trigger in my [Home Assistant](https://www.home-assistant.io/) (HA) instance to do something, (like, announce the goal on a voice assistant, flash a light, and/or notify my phone.)

## Requirements
- An interest in one or more NHL teams.
- A working Home Assistant instance.
- A linux box on which you can run docker and/or python 3.x, (this could likely also be run on Windows, but I haven't tried that, myself.)

I run this python script inside a docker container. The Dockerfile, build and run scripts are included here.  
I also set variables in the environment from a text file, `envvars.txt`, and invoke that file in the Docker run script.  
  
You could skip all the docker stuff, and just invoke the python script, `nhl_goal_alert.py`, by itself.  
You'll need to define those variables in your environment, manually, or edit the "Global default" variables in the python script.

## Usage
1. Edit `envvars.txt`:  
    a. Set your [timezone (TZ)](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for the log file output.  
    b. Set the [team ID](https://github.com/JayBlackedOut/hass-nhlapi/blob/master/teams.md) of the team for which you care to monitor goals scored.  
    c. Set the name or IP address of your [Home Assistant](https://www.home-assistant.io/) (HA) instance.  
    d. Set the port of your HA instance.  
    e. Set the ID of the HA [webhook trigger](https://www.home-assistant.io/docs/automation/trigger/#webhook-trigger) that the script will invoke when your team scores a goal.  
    f. Set the [log level](https://docs.python.org/3/library/logging.html#logging-levels) of messages to be written to the script's log file.
2. Edit `run.sh`:  
    a. Replace the first part of the docker bind-volume argument with the path to where you're running this script. The final `app` folder is the working folder containing the python script and log file:  
        `-v /path/to/your/nhl_goal_alert/app:/usr/src/app`
3. Make the two shell script files executable:  
    `# chmod a+x *.sh`
4. Execute `build.sh` to build the docker file image based on `python:slim`
5. Execute `run.sh` to run an instance of this docker image in a container that will terminate when it's complete. It will write its log file to the same directory containing the python script.



## Why
I wrote this to help me troubleshoot a problem with the excellent [NHL API integration for HACS on Home Assistant](https://github.com/JayBlackedOut/hass-nhlapi), by [@JayBlackedOut](https://github.com/JayBlackedOut).
The symptom I'm troubleshooting is that the HA sensor stops updating during a game, sometimes for 20 minutes or longer.
If I restart HA, the sensor resumes updating, until it stops, again. My Home Assistant instance has no other connectivity or performance symptoms.

Culprits could be many, including 
1. slow DNS server response
1. congested home network or ISP
1. misconfigured home network, VM host, VM guest and/or HA
1. non-responsive NHL API endpoint
1. too-long or non-existent [timeout](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts) in the call to `requests.get()` (or equivalent), causing a long stall
1. limited or non-existent error-handling in the call to `requests.get()` (or equivalent), masking the root cause.

## Method
Trying to eliminate one or more of these, I wrote this simple script that runs in a docker container on my same home network, but on a different computer, (virtual or real).
I've added a timeout to `requests.get()`, and rudimentary exception handling, to log and continue if an exception is thrown.

## Observations
In the first few runs of this script in a VM guest on the same host as my Home Assistant VM, it never stops updating.
This script is, so far, about as timely as my third, independent "observer", [theScore](https://get.thescore.com/) app on my iPhone.
