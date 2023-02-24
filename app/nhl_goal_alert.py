# nhl_goal_alert.py, Walt Lillyman, 12/29/22
# Detect when a goal is scored and tell Home Assistant via webhook.

import config  # Configuration values defined in file, config.py
import logging
import socket    # Validate hosts are reachable
import requests  # Make API calls via HTTP(S)
import time  # Sleep
from pathlib import Path  # Log file definition

def main():
    # Set numeric equivalent of log level:
    match config.log_level:
        case 'DEBUG':
            config.log_level = 10
        case 'INFO':
            config.log_level = 20
        case 'WARNING':
            config.log_level = 30
        case 'ERROR':
            config.log_level = 40
        case 'CRITICAL':
            config.log_level = 50
        case _:
            config.log_level = 10

    # Log to file, appending log messages. DEBUG level will also reveal statements from the requests library:
    logging.basicConfig(filename=Path(__file__).stem+'.log', filemode='a', format='%(asctime)s %(module)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=config.log_level)

    logging.info(f"STARTING with team ID={config.team_id}, HA host:port={config.ha_host}:{config.ha_port}, webhook ID={config.webhook_id}")

    # NHL API:
    nhl_base = "https://statsapi.web.nhl.com/api/v1/"
    score_endpoint = f"schedule?teamId={config.team_id}&hydrate=scoringplays"
    score_url = nhl_base + score_endpoint

    # Home Assistant webhook API:
    goal_notify_url=f"http://{config.ha_host}:{config.ha_port}/api/webhook/{config.webhook_id}"

    # Validate connectivity to NHL host:
    try:
        socket.create_connection(('statsapi.web.nhl.com', 443), timeout=4)
    except Exception as e:
        message = f"Can't connect to NHL API at {nhl_base}: {e}"
        logging.error(message)
        raise SystemExit(message)

    # Validate connectivity to Home Assistant host:
    try:
        socket.create_connection((config.ha_host, config.ha_port), timeout=2)
    except Exception as e:
        message = f"Can't connect to homeassistant at {goal_notify_url}: {e}"
        logging.error(message)
        raise SystemExit(message)

    # Call the NHL API, and exit if it failed:
    try:
        response = requests.get(score_url, timeout=5)
    # except requests.exceptions.RequestException as e:
    except requests.Timeout as e:
        message = f'First API call to NHL threw an exception: {e}.  Exiting.'
        logging.error(message)
        raise SystemExit(message)

    # Update data only for a valid response:
    if response.status_code == 200:
        data = response.json()
    else:
        message = f'First API call to NHL returned non-OK status: {response.status_code}.  Exiting.'
        logging.error(message)
        raise SystemExit(message)

    # Verify game info is available, else exit:
    if len(data['dates']) == 0:
        message = 'Game info is not yet available from the NHL API.  Exiting.'
        logging.info(message)
        raise SystemExit(message)

    # Set home or away value for this game:
    home_or_away = 'home' if data['dates'][0]['games'][0]['teams']['home']['team']['id'] == config.team_id else 'away'

    # Prevent false-alerting when app is started during a game in progress that has a non-zero score:
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
                    logging.info(f"{status}.") # Log "in-progress" the first time we see it.
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

                # Save the current score for comparison next time. Do this every time thru to handle when a goal gets called back.
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
            response = requests.get(score_url, timeout=5)
        # except requests.exceptions.RequestException as e:
        except requests.Timeout as e:
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