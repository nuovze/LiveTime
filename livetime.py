#
# Author:   ShermanZero
# Version:  1.2
#

import obspython as obs
from pathlib import Path

version = "1.2"

class LiveTime:
    def __init__(self,source_name=None):
        self.source_name = source_name
        self.secondsLive = 0
        self.minutesLive = 0
        self.hoursLive = 0
        self.lastTimeLive = ""

    def reset_timer(self):
        self.secondsLive = 0
        self.minutesLive = 0
        self.hoursLive = 0
        self.update_text(True, False)

    def update_text(self, force=False, updateTime=True):
        source = obs.obs_get_source_by_name(self.source_name)
        if source is not None:
            if updateTime:
                self.secondsLive += 1

                if(self.secondsLive >= 60):
                    self.minutesLive += 1
                    self.secondsLive = 0
                    if(self.minutesLive >= 60):
                        self.hoursLive += 1
                        self.minutesLive = 0

            if(Data._visible_ and not Data._timerRunning_):
                timeLive = ""
            else:
                timeLive = self.get_formatted_time()

            #prevent more work being done than necessary
            if(timeLive == self.lastTimeLive and not force):
                return

            self.lastTimeLive = timeLive
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "text", timeLive)
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)

    def get_formatted_time(self):
        timeLive = Data._format_

        h = str(self.hoursLive)
        m = str(self.minutesLive)
        s = str(self.secondsLive)

        if "{h}" in Data._format_:
            timeLive = str.replace(timeLive, "{h}", h)
        if "{m}" in Data._format_:
            timeLive = str.replace(timeLive, "{m}", m)
        if "{s}" in Data._format_:
            timeLive = str.replace(timeLive, "{s}", s)

        #per feature request, additional formatting options specify ensuring double-digits at all times (for values less than 100)
        if "{hh}" in Data._format_:
            if (len(h) <= 1): h = "0" + h
            timeLive = str.replace(timeLive, "{hh}", h)
        if "{mm}" in Data._format_:
            if (len(m) <= 1): m = "0" + m
            timeLive = str.replace(timeLive, "{mm}", m)
        if "{ss}" in Data._format_:
            if (len(s) <= 1): s = "0" + s
            timeLive = str.replace(timeLive, "{ss}", s)

        return timeLive

class Data:
    _defaultFormat_ = "♦  UPTIME  »  {h}H  {m}M"
    _format_ = _defaultFormat_
    _autoStart_ = False
    _autoStop_ = False
    _recording_ = False
    _visible_ = False
    _timerRunning_ = False

liveTime = LiveTime()
callback = liveTime.update_text

# ---------------------------- helper methods --------------------------------------

def start_timer():
    stop_timer()
    Data._timerRunning_ = True
    obs.timer_add(callback, 1 * 1000)

def stop_timer():
    Data._timerRunning_ = False
    obs.timer_remove(callback)
    liveTime.reset_timer()



# --------------------------- callbacks ---------------------------------------------

def reset_pressed(props, prop):
    stop_timer()

def start_pressed(props, prop):
    start_timer()

def on_event(event):
    #if both autostart and autostop are diabled just return
    if not Data._autoStart_ and not Data._autoStop_: return

    #stream start
    if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTED and Data._autoStart_:
        stop_timer()
        if liveTime.source_name != "":
            start_timer()
    #stream stopped
    elif event == obs.OBS_FRONTEND_EVENT_STREAMING_STOPPED and Data._autoStop_:
        stop_timer()

    #if recording mode is enabled
    if Data._recording_:
        #recording start
        if event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTED and Data._autoStart_:
            stop_timer()
            if liveTime.source_name != "":
                start_timer()
        #recording stopped
        elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED and Data._autoStop_:
            stop_timer()

# -------------------------------------- script methods ----------------------------------------

desc = '<HTML><body><center><h2>LiveTime</h2><h5>v'+version+'</h5></center><center><a href="https://twitch.tv/shermanzero">ShermanZero</a> © 2021</center><p>A timer to display your uptime.  Options to automatically start and stop with your stream/recording are available.  Text formatting is also available as seen below, and is case-sensitive.<p>Simply create a text source, link it here, specify how the timer is formatted, and that\'s it.<p><br>Available formatting variables:<p><ul><li>{h} or {hh}</li><li>{m} or {mm}<li>{s} or {ss}</li></ul>Variables will display the hours, minutes, and seconds of the timer respectively.  Using the {hh}, {mm}, or {ss} variations will ensure a double-digit output (e.g "04").</body><br><center><a href="https://github.com/ShermanZero/LiveTime/blob/main/patchnotes.txt">Patch Notes</a></center></body></HTML>'
def script_description():
    return desc

def script_update(settings):
    liveTime.source_name = obs.obs_data_get_string(settings, "source")
    Data._format_ = obs.obs_data_get_string(settings, "format")
    Data._autoStart_ = obs.obs_data_get_bool(settings, "auto_start")
    Data._autoStop_ = obs.obs_data_get_bool(settings, "auto_stop")
    Data._recording_ = obs.obs_data_get_bool(settings, "recording")
    Data._visible_ = obs.obs_data_get_bool(settings, "visible")

    #force the text to update and do not increment the timer
    liveTime.update_text(True, False)

def script_properties():
    props = obs.obs_properties_create()
    p = obs.obs_properties_add_list(
        props,
        "source",
        "Text Source:",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING,
    )

    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

        obs.source_list_release(sources)

    obs.obs_properties_add_text(props, "format", "Text Format:", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_button(props, "reset_button", "Reset/Stop Timer", reset_pressed)
    obs.obs_properties_add_button(props, "start_button", "Start Timer", start_pressed)
    obs.obs_properties_add_bool(props, "auto_start", "Start Automatically with Stream/Recording")
    obs.obs_properties_add_bool(props, "auto_stop", "Stop Automatically with Stream/Recording")
    obs.obs_properties_add_bool(props, "recording", "Enable for Recording")
    obs.obs_properties_add_bool(props, "visible", "Text Visible Only While Timer Running")

    return props

def script_load(settings):
    obs.obs_frontend_add_event_callback(on_event)
    Data._format_ = obs.obs_data_get_string(settings, "format")
    Data._autoStart_ = obs.obs_data_get_bool(settings, "auto_start")
    Data._autoStop_ = obs.obs_data_get_bool(settings, "auto_stop")
    Data._recording_ = obs.obs_data_get_bool(settings, "recording")
    Data._visible_ = obs.obs_data_get_bool(settings, "visible")

    if not Data._format_:
        Data._format_ = Data._defaultFormat_

    obs.obs_data_set_string(settings, "format", Data._format_)
    obs.obs_data_set_bool(settings, "auto_start", Data._autoStart_)
    obs.obs_data_set_bool(settings, "auto_stop", Data._autoStop_)
    obs.obs_data_set_bool(settings, "recording", Data._recording_)
    obs.obs_data_set_bool(settings, "visible", Data._visible_)
