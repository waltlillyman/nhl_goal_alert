# nhl_goal_alert.py, Walt Lillyman, 12/15/22
# Detect when a goal is scored and tell HA via webhook.

import logging
import requests
import time
from os import getenv
from pathlib import Path

# Global defaults:
default_team_id = 19
default_webhook_id = 'press_nhl_goal_button'
default_log_level = 'DEBUG'
default_ha_host = 'homeassistant'

def main():
    # When an env var is not set at all, its value is "None". When it's set with no value, it's value is ''. 
    # Malke sure to cast numeric environment variable values as int for later comparison. Set defaults if not defined:
    team_id = int(getenv('TEAM_ID')) if (getenv('TEAM_ID') != None and getenv('TEAM_ID') != '') else default_team_id
    ha_host = getenv('HA_HOST') if (getenv('HA_HOST') != None and getenv('HA_HOST') != '') else default_ha_host
    webhook_id = getenv('WEBHOOK_ID') if (getenv('WEBHOOK_ID') != None and getenv('WEBHOOK_ID') != '') else default_webhook_id
    log_level = getenv('LOG_LEVEL') if (getenv('LOG_LEVEL') != None and getenv('LOG_LEVEL') != '') else default_log_level
    # Set numeric equivalent of log level:
    match log_level:
        case 'DEBUG':
            log_level = 10
        case 'INFO':
            log_level = 20
        case 'WARNING':
            log_level = 30
        case 'ERROR':
            log_level = 40
        case 'CRITICAL':
            log_level = 50
        case _:
            log_level = 10

    # Log to this_script.log, appending log messages. DEBUG level will also reveal statements from the requests library:
    logging.basicConfig(filename=Path(__file__).stem+'.log', filemode='a', format='%(asctime)s %(module)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=log_level)

    logging.info(f"STARTING with Team ID: {team_id}, Webhook ID: {webhook_id}")

    # NHL API:
    nhl_base = "https://statsapi.web.nhl.com/api/v1/"
    score_endpoint = f"schedule?teamId={team_id}&hydrate=scoringplays"
    score_url = nhl_base + score_endpoint

    # Home Assistant webhook API:
    goal_notify_url=f"http://{ha_host}:8123/api/webhook/{webhook_id}"

    # Initialize score for comparison:
    score = 0

    # Call the API, and log but continue if it failed:
    try:
        response = requests.get(score_url, timeout=7)
    except:
        logging.error('First call to the API threw an exception.  Exiting.')
        raise SystemExit(0)

    # Update data only for a valid response:
    if response.status_code == 200:
        data = response.json()
    else:
        logging.error('First call to the API returned non-OK status.  Exiting.')
        raise SystemExit(0)

    # Verify game info is available, else exit:
    if len(data['dates']) == 0:
        logging.info('Game info is not yet available from the NHL API.  Exiting.')
        raise SystemExit(0)

    # Set home or away value for this game:
    home_or_away = 'home' if data['dates'][0]['games'][0]['teams']['home']['team']['id'] == team_id else 'away'

    while(1):
        # Get the current game state, "Scheduled", "Pre-Game", "In Progress", "Final"...
        status = data['dates'][0]['games'][0]['status']['detailedState']

        match status:
            case 'Scheduled':
                logging.info(f"{status}.")
                interval = 40
            case 'Pre-Game':
                logging.info(f"{status}.")
                interval = 10
            case 'In Progress' | 'In Progress - Critical':
                interval = 3
                new_score = data['dates'][0]['games'][0]['teams'][home_or_away]['score']
                if new_score > score:
                    # Notify Home Assistant about the goal via webhook:
                    response = requests.post(goal_notify_url, json="{}")
                    logging.info(f"Goal number {new_score}!")
                    # Save the current score for comparison next time:
                    score = new_score
            case 'Game Over' | 'Final' | 'No Game Scheduled':
                logging.info(f"{status}.")
                break
            case _:
                logging.info(f"Unexpected game status, {status}")
                break

        # Snooze:
        time.sleep(interval)

        # Call the API, and log but continue if it failed:
        try:
            response = requests.get(score_url, timeout=7)
        except:
            logging.error(f"API call threw an exception.")
        # Update data only for a valid response:
        if response.status_code == 200:
            data = response.json()

    logging.info('DONE.')

if __name__ == "__main__":
    main()