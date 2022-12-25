# nhl_goal_alert.py, Walt Lillyman, 12/24/22
# Detect when a goal is scored and tell HA via webhook.

import logging
import socket    # Validate hosts are reachable
import requests  # Make API calls via HTTP(S)
import time  # Sleep
from os import getenv  # Environment variables
from pathlib import Path  # Log file definition

# Global defaults:
default_team_id = 19
default_ha_host = 'homeassistant'
default_ha_port = 8123
default_webhook_id = 'press_nhl_goal_button'
default_log_level = 'DEBUG'


def main():
    # When an env var is not set at all, its value is "None". When it's set with no value, it's value is ''. 
    # Malke sure to cast numeric environment variable values as int for later comparison. Set defaults if not defined:
    team_id = int(getenv('TEAM_ID')) if (getenv('TEAM_ID') != None and getenv('TEAM_ID') != '') else default_team_id
    ha_host = getenv('HA_HOST') if (getenv('HA_HOST') != None and getenv('HA_HOST') != '') else default_ha_host
    ha_port = int(getenv('HA_PORT')) if (getenv('HA_PORT') != None and getenv('HA_PORT') != '') else default_ha_port
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

    logging.info(f"STARTING with team ID={team_id}, HA host:port={ha_host}:{ha_port}, webhook ID={webhook_id}")

    # NHL API:
    nhl_base = "https://statsapi.web.nhl.com/api/v1/"
    score_endpoint = f"schedule?teamId={team_id}&hydrate=scoringplays"
    score_url = nhl_base + score_endpoint

    # Home Assistant webhook API:
    goal_notify_url=f"http://{ha_host}:{ha_port}/api/webhook/{webhook_id}"

    # Validate connectivity to NHL host:
    try:
        socket.create_connection(('statsapi.web.nhl.com', 443), timeout=4)
    except Exception as e:
        message = f"Can't connect to NHL API at {nhl_base}: {e}"
        logging.error(message)
        raise SystemExit(message)

    # Validate connectivity to Home Assistant host:
    try:
        socket.create_connection((ha_host, ha_port), timeout=2)
    except Exception as e:
        message = f"Can't connect to homeassistant at {goal_notify_url}: {e}"
        logging.error(message)
        raise SystemExit(message)

    # Call the NHL API, and exit if it failed:
    try:
        response = requests.get(score_url, timeout=7)
    except requests.exceptions.RequestException as e:
        message = f'First call to the API threw an exception: {e}.  Exiting.'
        logging.error(message)
        raise SystemExit(message)

    # Update data only for a valid response:
    if response.status_code == 200:
        data = response.json()
    else:
        message = f'First call to the API returned non-OK status: {response.status_code}.  Exiting.'
        logging.error(message)
        raise SystemExit(message)

    # Verify game info is available, else exit:
    if len(data['dates']) == 0:
        message = 'Game info is not yet available from the NHL API.  Exiting.'
        logging.info(message)
        raise SystemExit(message)

    # Set home or away value for this game:
    home_or_away = 'home' if data['dates'][0]['games'][0]['teams']['home']['team']['id'] == team_id else 'away'

    # Prevent false-triggering when app starts during game in progress that has a non-zero score:
    first_time_thru = True
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
                # Initialize score to current value the first time thru:
                if first_time_thru:
                    score = new_score
                    first_time_thru = False
                # If a goal was scored since last time checked:
                if new_score > score:
                    # Notify Home Assistant about the goal via webhook:
                    try:
                        response = requests.post(goal_notify_url, timeout=4, json="{}")
                    except requests.exceptions.RequestException as e:
                        message = f'API call to homeassistant threw an exception: {e}. Ignoring.'
                        logging.warning(message)

                    logging.info(f"Goal number {new_score}!")
                    # Save the current score for comparison next time:
                    score = new_score

            case 'Game Over' | 'Final':
                # If it was overtime, the status could have gone to "Game Over" in the same breath as our team scored the winning goal. Check for that goal and notify before exiting:
                new_score = data['dates'][0]['games'][0]['teams'][home_or_away]['score']
                # If a goal was scored since last time checked:
                if new_score > score:
                    # Notify Home Assistant about the goal via webhook:
                    try:
                        response = requests.post(goal_notify_url, timeout=4, json="{}")
                    except requests.exceptions.RequestException as e:
                        message = f'API call to homeassistant threw an exception: {e}. Ignoring.'
                        logging.warning(message)

                    logging.info(f"Goal number {new_score}!")

                # Game over, we're done here:
                logging.info(f"{status}.")
                break

            case 'No Game Scheduled':
                logging.info(f"{status}.")
                break

            case _:
                logging.error(f"Unexpected game status, {status}")
                break

        # Snooze:
        time.sleep(interval)

        # Call the NHL API, and log but continue if it failed:
        try:
            response = requests.get(score_url, timeout=7)
        except requests.exceptions.RequestException as e:
            message = f'API call to NHL threw an exception: {e}.  Ignoring.'
            logging.warning(message)

        # Update data only for a valid response:
        if response.status_code == 200:
            data = response.json()
        else:
            message = f'API call to NHL returned non-OK status: {response.status_code}.  Ignoring.'
            logging.warning(message)

    logging.info('DONE.')

if __name__ == "__main__":
    main()