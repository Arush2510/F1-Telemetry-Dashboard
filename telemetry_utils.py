# scripts/telemetry_utils.py
import fastf1
from fastf1 import plotting
import pandas as pd

def get_session_data(year, gp, session_type):
    fastf1.Cache.enable_cache('./data')  # enable cache for faster access
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    return session

def get_telemetry_for_driver(session, driver_code):
    lap = session.laps.pick_driver(driver_code).pick_fastest()
    telemetry = lap.get_telemetry()
    return telemetry  # contains Speed, Throttle, Brake, RPM, DRS, X, Y, Distance
