# nhl_goal_alert

## Description
Stand-alone python script to poll the unofficial NHL API for changes to the score of a game in progress.
When [my team](https://www.nhl.com/blues/) scores a goal, invoke a webhook in my [Home Assistant](https://www.home-assistant.io/) to do something, (like, announce the goal on a voice assistant, flash a light, and/or notify my phone.)

## Why
I wrote this to help me troubleshoot a problem with the excellent [NHL API integration for HACS on Home Assistant](https://github.com/JayBlackedOut/hass-nhlapi), by [@JayBlackedOut](https://github.com/JayBlackedOut).
The symptom I'm troubleshooting is that the HA sensor stops updating during a game, sometimes for 20 minutes or longer.
If I restart HA, the sensor resumes updating. Until it stops again. My Home Assistant has no other connectivity or performance symptoms.

Culprits could be many, including 
1. slow DNS server responses
1. congested home network or ISP
1. misconfigured home network, VM host, VM guest and/or HA
1. non-responsive NHL API endpoint
1. too-long or non-existent [timeout](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts) in the call to `requests.get()` (or equivalent)
1. limited or non-existent error-handling in the call to `requests.get()` (or equivalent), masking the root cause.

## Method
Trying to eliminate one or more of these, I wrote this simple script that runs in a docker container on my same home network, but on a different computer, (virtual or real).
I've added a timeout to `requests.get()`, and rudimentary exception handling, to log and continue if an exception is thrown.

## Observations
In the first few runs of this script in a VM guest on the same host as my Home Assistant VM, it never stops updating.
This script is, so far, about as timely as my third, independent "observer", [theScore](https://get.thescore.com/) app on my iPhone.

## To do
- [ ] Figure out how to detect & log when `requests.get()` [times out](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts).
- [ ] Figure out how to log the text of the exception that happened when an exception is thrown.
- [ ] Nice-to-have: Make the API call at the top of the polling loop instead of the bottom, to handle when an overtime game ends, going "FINAL", before the goal score increment was detected.
