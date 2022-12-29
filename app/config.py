# nhl_goal_alert configuration 
# Team ID from https://github.com/JayBlackedOut/hass-nhlapi/blob/master/teams.md
# Blues = 19, Canes = 12, Stars = 25
team_id = 19
# Homeassistant (HA) host name or IP address and port:
ha_host = "homeassistant"
ha_port = 8123
# HA webhook invoked upon goal-scored. Mine presses an HA helper button, which an automation monitors:
webhook_id = "press_nhl_goal_button"
# LOG_LEVEL can be DEBUG, INFO, WARNING, ERROR, CRITICAL.
#   DEBUG will display DEBUG and all "higher" messages; INFO will display INFO and all higher, etc.
log_level = "INFO"
