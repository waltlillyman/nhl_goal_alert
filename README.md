# nhl_goal_alert

## Description
Python 3.10 script that polls the unofficial NHL API for changes in the score of one team for a game in progress.
When [my team](https://www.nhl.com/blues/) scores a goal, invoke a webhook trigger in my [Home Assistant](https://www.home-assistant.io/) (HA) instance to do something, (like, announce the goal on a voice assistant, flash a light, and/or notify my phone.)

## Requirements
- An interest in one or more NHL teams.
- A working Home Assistant instance.
- A real or virtual Linux machine with python 3.10 and optionally Docker. (This will probably run on Windows, but I haven't tried that, myself.)

I run this python script inside a docker container. The Dockerfile, build and run scripts are included here. You could skip docker and just invoke the python script, `nhl_goal_alert.py`, by itself.  

## Usage
1. Edit `app/config.py`:  
    1. Set the [team ID](https://github.com/JayBlackedOut/hass-nhlapi/blob/master/teams.md) of the team for which you care to monitor goals scored.  
    1. Set the name or IP address of your [Home Assistant](https://www.home-assistant.io/) (HA) instance.  
    1. Set the port of your HA instance.  
    1. Set the ID of the HA [webhook trigger](https://www.home-assistant.io/docs/automation/trigger/#webhook-trigger) that the script will invoke when your team scores a goal.  
    1. Set the [log level](https://docs.python.org/3/library/logging.html#logging-levels) of messages to be written to the script's log file.  

#### If you're using Docker on Linux:
1. Edit `run.sh`:  
    1. Set your [timezone (TZ)](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for the log file output, i.e.: `-e TZ=America/Chicago`  

    1. Replace the first part of the docker bind-volume argument with the path to where you're running this script. The final `app` sub-folder is the working folder containing the python script, config file and log file:  
        `-v /path/to/your/nhl_goal_alert/app:/usr/src/app`
1. Make the two shell script files executable:  
    `# chmod a+x *.sh`
1. Execute `build.sh` to build the docker file image based on `python:slim`
1. Execute `run.sh` to run an instance of this docker image in a container that will terminate when it's complete. It will write its log file to the `app` sub-directory containing the python script and config file.



## Why
I wrote this to help me troubleshoot a problem with the excellent [NHL API integration for HACS on Home Assistant](https://github.com/JayBlackedOut/hass-nhlapi), by [@JayBlackedOut](https://github.com/JayBlackedOut).
The symptom I'm troubleshooting is that the HA sensor stops updating during a game, sometimes for 20 minutes or longer.
If I restart HA, the sensor resumes updating, until it stops, again. My Home Assistant instance has no other connectivity or performance symptoms.

Possible culprits are many, including:
1. slow DNS server response
1. congested home network or ISP
1. misconfigured home network, VM host, VM guest and/or HA
1. non-responsive NHL API endpoint
1. too-long or non-existent [timeout](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts) in the call to `requests.get()` (or equivalent), causing a long stall
1. limited or non-existent error-handling in the call to `requests.get()` (or equivalent), masking the root cause.

## Method
Trying to eliminate one or more of these, I wrote this script that runs in a docker container on my same home network, but on a different computer, (virtual or real).
I've added a timeout to `requests.get()`, and rudimentary exception handling, to log and continue if an exception is thrown.

## Observations
In the first few runs of this script in a VM guest on the same host as my Home Assistant VM, it never exhibits behavior like the HA integration, which frequently just stops updating (for me).
This script is, so far, about as timely as my third, independent "observer", [theScore](https://get.thescore.com/) app, on my iPhone.

Subsequent observations indicate the NHL API request occasionally times out, for me, after the value I specified, 7 seconds. This script catches that exception, (any any others thrown by the `requests()` call to the NHL API), logs the exception message, and carries on. An occasional failed API call is acceptable, as is a relatively short timeout, in my opinion.  

#### Log excerpt:
```
12/27/2022 08:17:40 PM nhl_goal_alert INFO: Goal number 3!
12/27/2022 08:32:22 PM nhl_goal_alert WARNING: API call to NHL threw an exception: HTTPSConnectionPool(host='statsapi.web.nhl.com', port=443): Read timed out. (read timeout=7).  Ignoring.
12/27/2022 09:02:47 PM nhl_goal_alert INFO: Goal number 4!
```
