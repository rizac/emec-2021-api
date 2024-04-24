"""
utilities for FDSN queries
(https://www.fdsn.org/webservices/fdsnws-event-1.2.pdf)
"""
from datetime import datetime
from enum import Enum
from io import StringIO

import pandas as pd

from emec_2021.emec import EmecField


class Param(Enum):
    """
    FDSN required query params. Name should be the short name, value the verbose
    one. If the param has no alias, map the param name to itself.
    (https://www.fdsn.org/webservices/fdsnws-event-1.2.pdf)
    """
    maxlat = 'maxlatitude'
    minlat = 'minlatitude'
    minlon = 'minlongitude'
    maxlon = 'maxlongitude'
    minmag = 'minmagnitude'
    maxmag = 'maxmagnitude'
    mindepth = 'mindepth'
    maxdepth = 'maxdepth'
    magtype = 'magnitudetype'
    start = 'starttime'
    end = 'endtime'
    orderby = 'orderby'


def apply_query_param(
        catalog: pd.DataFrame, param: str, value: str, strict_check=True
) -> pd.DataFrame:
    try:
        param, value = validate_param(param, value)
    except ValueError as err:
        if not strict_check:
            return catalog
        raise err from None

    # https://www.fdsn.org/webservices/fdsnws-event-1.2.pdf
    if param == Param.start:
        return catalog[catalog[EmecField.time] >= value]
    if param == Param.end:
        return catalog[catalog[EmecField.time] <= value]
    if param == Param.minlat:
        return catalog[catalog[EmecField.lat] >= value]
    if param == Param.maxlat:
        return catalog[catalog[EmecField.lat] <= value]
    if param == Param.minlon:
        return catalog[catalog[EmecField.lon] >= value]
    if param == Param.maxlon:
        return catalog[catalog[EmecField.lon] <= value]
    if param == Param.minmag:
        return catalog[catalog[EmecField.mag] > value]
    if param == Param.maxmag:
        return catalog[catalog[EmecField.mag] < value]
    if param == Param.mindepth:
        return catalog[catalog[EmecField.depth] > value]
    if param == Param.maxdepth:
        return catalog[catalog[EmecField.depth] < value]
    if param == Param.orderby:
        order_by = value
        ascending = False
        if order_by.endswith("-asc"):
            order_by = value[:-4]
            ascending = True
        try:
            return catalog.sort_values(by=order_by, ascending=ascending)
        except KeyError as err:
            raise ValueError(f'Invalid value for orderby: {str(err)}')
        # orderby required time Valid sort value string
        # Order the result by time or magnitude with the following possibilities:
        # time: order by origin descending time
        # time-asc: order by origin ascending time
        # magnitude: order by descending magnitude
        # magnitude-asc: order by ascending magnitude
    return catalog


def validate_param(param: str, value: str) -> tuple:  # tuple[Param, Any]
    try:
        col = Param(param)
    except ValueError:
        try:
            col = Param[param]
        except KeyError:
            raise ValueError(f'unknown parameter {param}')
    if col in (Param.start, Param.end):
        return col, datetime.fromisoformat(value).timestamp()
    elif col in (Param.magtype, Param.orderby):
        return col, str(value)
    else:
        return col, float(value)


def to_text(catalog: pd.DataFrame) -> StringIO:
    s = StringIO()
    s.write('#EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|'
            'ContributorID|MagType|Magnitude|MagAuthor|EventLocationName|EventType')
    iterator = zip(
        catalog[EmecField.eventid],
        catalog[EmecField.time],
        catalog[EmecField.lat],
        catalog[EmecField.lon],
        catalog[EmecField.depth],
        catalog[EmecField.mag],
        catalog[EmecField.magtype],
        catalog[EmecField.iscid],
    )
    for ev_id, timestamp, lat, lon, depth, mag, magtype, isc_id in iterator:
        c = 'ISC' if isc_id > 0 else ''
        cid = isc_id if isc_id > 0 else ''
        s.write(f'\n{ev_id}|{datetime.fromtimestamp(timestamp).isoformat()}|'
                f'{lat}|{lon}|{depth}||EMEC-2021|{c}|{cid}|{magtype}|{mag}|||'
                f'earthquake')
    s.seek(0)
    return s
