#!/usr/bin/env python3
'''
Touch Portal Plugin Example
'''

import sys

# Load the TP Python API. Note that TouchPortalAPI must be installed (eg. with pip)
# _or_ be in a folder directly below this plugin file.
import TouchPortalAPI as TP
import time
from threading import Thread

# imports below are optional, to provide argument parsing and logging functionality
from argparse import ArgumentParser
from logging import (getLogger, Formatter, NullHandler, FileHandler, StreamHandler, DEBUG, INFO, WARNING)

# Version string of this plugin (in Python style).
__version__ = "1.0"

# The unique plugin ID string is used in multiple places.
# It also forms the base for all other ID strings (for states, actions, etc).
PLUGIN_ID = "gitago.cd.plugin"

## Start Python SDK declarations
# These will be used to generate the entry.tp file,
# and of course can also be used within this plugin's code.
# These could also live in a separate .py file which is then imported
# into your plugin's code, and be used directly to generate the entry.tp JSON.
#
# Some entries have default values (like "type" for a Setting),
# which are commented below and could technically be excluded from this code.
#
# Note that you may add any arbitrary keys/data to these dictionaries
# w/out breaking the generation routine. Only known TP SDK attributes
# (targeting the specified SDK version) will be used in the final entry.tp JSON.
##

# Basic plugin metadata
TP_PLUGIN_INFO = {
    'sdk': 3,
    'version': int(float(__version__) * 1),  # TP only recognizes integer version numbers
    'name': "Countdown / Stopwatch Plugin",
    'id': PLUGIN_ID,
    'configuration': {
        'colorDark': "#FF817E",
        'colorLight': "#676767"
    }
}

# Setting(s) for this plugin. These could be either for users to
# set, or to persist data between plugin runs (as read-only settings).
TP_PLUGIN_SETTINGS = {
    'example': {
        'name': "Example Setting",
        # "text" is the default type and could be omitted here
        'type': "text",
        'default': "Example value",
        'readOnly': False,  # this is also the default
        'value': None  # we can optionally use the settings struct to hold the current value
    },
}

# This example only uses one Category for actions/etc., but multiple categories are supported also.
TP_PLUGIN_CATEGORIES = {
    "stopwatch": {
        'id': PLUGIN_ID + ".stopwatch",
        'name': "Countdown / Stopwatch",
        'imagepath': "%TP_PLUGIN_FOLDER%Countdown Plugin/countdown_git.png"
    },
    "countdown": {
        'id': PLUGIN_ID + ".countdown",
        'name': "Countdown",
        'imagepath': "%TP_PLUGIN_FOLDER%Countdown Plugin/timer_git.png"
    }
}

# Action(s) which this plugin supports.
TP_PLUGIN_ACTIONS = {
    'action1': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "stopwatch",
        'id': PLUGIN_ID + ".act",
        'name': "Add/Subtract Time 2.0",
        'prefix': TP_PLUGIN_CATEGORIES['stopwatch']['name'],
        'type': "communicate",
        "tryInline": True,
        'format': "{$gitago.cd.plugin.act.time.add.remove$} (Hours){$gitago.cd.plugin.act.time.hours$}   (Minutes){$gitago.cd.plugin.act.time.minutes$}   (Seconds){$gitago.cd.plugin.act.time.seconds$}   to/from {$gitago.cd.plugin.act.pick.mode$}",
        'data': {
            'addremove': {
                'category': "countdown",
                'id': PLUGIN_ID + ".act.time.add.remove",
                'type': "choice",
                'label': "Add or Remove",
                'default': "Add",
                'valueChoices': ["Add", "Remove"]
            },
            'hours': {
                'category': "countdown",
                'id': PLUGIN_ID + ".act.time.hours",
                'type': "text",
                'label': "Hours",
                'default': "0",
            },
            'minutes': {
                'id': PLUGIN_ID + ".act.time.minutes",
                'type': "text",
                'label': "Minutes",
                'default': "0",
            },
            'seconds': {
                'id': PLUGIN_ID + ".act.time.seconds",
                'type': "text",
                'label': "Seconds",
                'default': "0",
            },
            'pickmode': {
                'id': PLUGIN_ID + ".act.pick.mode",
                'type': "choice",
                'label': "Stopwatch or Countdown",
                'default': "",
                'valueChoices': ["Countdown", "Stopwatch"]
            },
        }
    },
    'action2': {
        # 'category' is optional, if omitted then this action will be added to all, or the only, category(ies)
        'category': "stopwatch",
        'id': PLUGIN_ID + ".act.switch",
        'name': "Start/Stop/Reset",
        'prefix': TP_PLUGIN_CATEGORIES['stopwatch']['name'],
        'type': "communicate",
        "tryInline": True,
        'format': "{$gitago.cd.plugin.act.ssr$} the {$gitago.cd.plugin.act.pickmode.ssr$}",
        'data': {
            'ssr': {
                'id': PLUGIN_ID + ".act.ssr",
                'type': "choice",
                'label': "Start, Stop or Reset",
                'default': "",
                'valueChoices': ["Start", "Stop", "Reset"]
            },
            'ssrmode': {
                'id': PLUGIN_ID + ".act.pickmode.ssr",
                'type': "choice",
                'label': "Stopwatch or Countdown",
                'default': "Countdown",
                'valueChoices': ["Countdown", "Stopwatch"]
            },
        }
    },
}

# Plugin static state(s). These are listed in the entry.tp file,
# vs. dynamic states which would be created/removed at runtime.
TP_PLUGIN_STATES = {
    'countdown': {
        'category': "countdown",
        'id': PLUGIN_ID + "state.total.countdowns",
        'type': "text",
        'desc': "Total Active Countdowns",
        'default': "0"
    },
    'status': {
        'category': "countdown",
        'id': PLUGIN_ID + ".state.countdown.status",
        'type': "text",
        'desc': "Countdown - Status",
        'default': "Paused"
    },
    'totaltime': {
        'category': "countdown",
        'id': PLUGIN_ID + ".state.countdown.totaltime",
        'type': "text",
        'desc': "Countdown - Total Time",
        'default': "0"
    },
    'timeleft': {
        'category': "countdown",
        'id': PLUGIN_ID + ".state.countdown.timeleft",
        'type': "text",
        'desc': "Countdown - Time Left",
        'default': "0"
    },
    'stopwatchtotal': {
        'category': "stopwatch",
        'id': PLUGIN_ID + ".state.stopwatch.total",
        'type': "text",
        'desc': "Total Active Stopwatches",
        'default': "0"
    },
    'stopwatchstatus': {
        'category': "stopwatch",
        'id': PLUGIN_ID + ".state.stopwatch.status",
        'type': "text",
        'desc': "Stopwatch - Status",
        'default': "Paused"
    },
    'stopwatchelapsed': {
        'category': "stopwatch",
        'id': PLUGIN_ID + ".state.stopwatch.elapsedtime",
        'type': "text",
        'desc': "Total Time on Stopwatch",
        'default': "0"
    },
}

# Plugin Event(s).
TP_PLUGIN_EVENTS = {}

##
## End Python SDK declarations


# Create the Touch Portal API client.
try:
    TPClient = TP.Client(
        pluginId=PLUGIN_ID,  # required ID of this plugin
        sleepPeriod=0.05,  # allow more time than default for other processes
        autoClose=True,  # automatically disconnect when TP sends "closePlugin" message
        checkPluginId=True,  # validate destination of messages sent to this plugin
        maxWorkers=4,  # run up to 4 event handler threads
        updateStatesOnBroadcast=False,  # do not spam TP with state updates on every page change
    )
except Exception as e:
    sys.exit(f"Could not create TP Client, exiting. Error was:\n{repr(e)}")


def Stopwatch(Time):
    Time = int(Time)
    while Time > 0:
        TPClient.stateUpdate("gitago.cd.plugin.state.countdown.status", "Alive")
        Time = Time - 1
        time.sleep(1)
        TPClient.stateUpdate("gitago.cd.plugin.state.countdown.timeleft", str(Time))
    TPClient.stateUpdate("gitago.cd.plugin.state.countdown.status", "Finished")

seconds2 = 0
minutes2 = 0
hours2 = 0

def countdown(seconds, minutes, hours):
    TPClient.stateUpdate("gitago.cd.plugin.state.countdown.status", "Started")
    global stop
    global hours2
    global minutes2
    global seconds2
    hours2 = hours
    minutes2 = minutes
    seconds2 = seconds



    while seconds2 != 0 or minutes2 != 0 or hours2 != 0:
        if stop:
            stop = False
            TPClient.stateUpdate("gitago.cd.plugin.state.countdown.status", "Stopped")
            break
        if seconds2 > 0:
            seconds2 = seconds2 - 1
        elif minutes2 > 0:
            seconds2 = 59
            minutes2 = minutes2 - 1
        elif minutes2 == 0 and hours2 > 0:
            hours2 = hours2 - 1
            minutes2 = 59
        H_M_S_format = '{:02d}:{:02d}:{:02d}'.format(hours2, minutes2, seconds2)
        print(H_M_S_format)
        TPClient.stateUpdate("gitago.cd.plugin.state.countdown.timeleft", str(H_M_S_format))
        time.sleep(1)
    print("Paused")
    if hours2 == 0 and minutes2 == 0 and seconds2 == 0:
        TPClient.stateUpdate("gitago.cd.plugin.state.countdown.status", "Finished")
        print("Finished")


## TP Client event handler callbacks

# Initial connection handler
@TPClient.on(TP.TYPES.onConnect)
def onConnect(data):
    print(data)


# Settings handler
@TPClient.on(TP.TYPES.onSettingUpdate)
def onSettingUpdate(data):
    print(data)
stop = False
ssrcheck = 0

# Action handler
@TPClient.on(TP.TYPES.onAction)
def onAction(data):
    global hours2
    global minutes2
    global seconds2
    global t
    global stop
    global ssrcheck
    hours = TPClient.getActionDataValue(data.get("data"), "gitago.cd.plugin.act.time.hours")
    minutes = TPClient.getActionDataValue(data.get("data"), "gitago.cd.plugin.act.time.minutes")
    seconds = TPClient.getActionDataValue(data.get("data"), "gitago.cd.plugin.act.time.seconds")
    mode = TPClient.getActionDataValue(data.get("data"), "gitago.cd.plugin.act.pick.mode")
    addremove = TPClient.getActionDataValue(data.get("data"), "gitago.cd.plugin.act.time.add.remove")
    ssr = TPClient.getActionDataValue(data.get("data"), "gitago.cd.plugin.act.ssr")
    print(data)
    if data['actionId'] == "gitago.cd.plugin.act":
        t=Thread(target=countdown, args=(int(seconds), int(minutes), int(hours)))
    if data['actionId'] == "gitago.cd.plugin.act.switch":
        if ssr == "Start":
            t.start()
            ssrcheck = 0
        if ssr == "Reset":
                stop = True
                ssrcheck = 0
        if ssr == "Stop" and ssrcheck < 1:
            ssrcheck = 1
            t =Thread(target=countdown, args=(int(seconds2), int(minutes2), int(hours2)))
            stop = True



# Shutdown handler
@TPClient.on(TP.TYPES.onShutdown)
def onShutdown(data):
    print(data)


# Error handler
@TPClient.on(TP.TYPES.onError)
def onError(exc):
    print(exc)


TPClient.connect()

