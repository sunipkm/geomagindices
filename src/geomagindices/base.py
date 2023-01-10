from __future__ import annotations
import typing
import pandas
import numpy as np
from dateutil.parser import parse
from datetime import datetime, date, timedelta
import pytz

from .web import downloadfile
from .io import load

def get_indices(time: str | datetime, smoothdays: int = None, forcedownload: bool = False, newsource: bool = True) -> pandas.DataFrame:
    """Get geomagnetic indices.

    alternative going back to 1931:
    ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/

    20 year Forecast data from:
    https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf

    newsource data from:
    ftp://ftp.gfz-potsdam.de/pub/home/obs/Kp_ap_Ap_SN_F107/

    Args:
        time (str | datetime): Timezone aware datetime.
        smoothdays (int, optional): Days to average over (for f10.7). Defaults to None.
        forcedownload (bool, optional): Force downloading data from servers every time. Defaults to False.
        newsource (bool, optional): Use the new datasource (newsource). Defaults to True.

    Returns:
        pandas.DataFrame: Dataframe containing the retrieved geomagnetic indices.
    """
    dtime = todatetime(time)

    _smoothdays = 0 if smoothdays is None else smoothdays # pass 0 if None
    fn = downloadfile(dtime, _smoothdays, forcedownload, newsource)
    # %% load data
    dat: pandas.DataFrame = load(fn)
    # %% optional smoothing over days
    if isinstance(smoothdays, int):
        periods = np.rint(timedelta(days=smoothdays) / (dat.index[1] - dat.index[0])).astype(int)

        if "f107" in dat:
            dat["f107s"] = dat["f107"].rolling(periods, min_periods=1).mean()
        if "Ap" in dat:
            dat["Aps"] = dat["Ap"].rolling(periods, min_periods=1).mean()

    # %% pull out the times we want
    i = dat.index.get_indexer(dtime, method = 'nearest') # fix for get_loc deprecation warning
    Indices = dat.iloc[i, :]

    return Indices


getApF107 = get_indices  # legacy


def moving_average(dat: pandas.Series, periods: int) -> np.ndarray:

    if periods > dat.size:
        raise ValueError("cannot smooth over more time periods than exist in the data")

    return np.convolve(dat, np.ones(periods) / periods, mode="same")


def todatetime(time: str | date | datetime | np.datetime64) -> typing.Any:
    if isinstance(time, str):
        d = todatetime(parse(time))
    elif isinstance(time, datetime):
        d = time.astimezone(pytz.utc).replace(tzinfo=None) # convert to UTC and strip timezone
    elif isinstance(time, np.datetime64):
        d = time.astype(datetime)
    elif isinstance(time, date):
        d = datetime(time.year, time.month, time.day)
    elif isinstance(time, (tuple, list, np.ndarray)):
        d = np.atleast_1d([todatetime(t) for t in time]).squeeze()
    elif isinstance(time, pandas.DatetimeIndex):
        d = time.to_pydatetime()
    else:
        raise TypeError(f"{time} must be representable as datetime.datetime")

    dates = np.atleast_1d(d).ravel()

    return dates


def todate(time: str | date | datetime | np.datetime64) -> typing.Any:

    if isinstance(time, str):
        d = todate(parse(time))
    elif isinstance(time, datetime):
        d = time.astimezone(pytz.utc).replace(tzinfo=None).date() # convert to UTC and strip timezone
    elif isinstance(time, np.datetime64):
        d = time.astype(date)
    elif isinstance(time, date):
        d = time
    elif isinstance(time, (tuple, list, np.ndarray)):
        d = np.atleast_1d([todate(t) for t in time]).squeeze()
    else:
        raise TypeError(f"{time} must be representable as datetime.date")

    dates = np.atleast_1d(d).ravel()

    return dates
