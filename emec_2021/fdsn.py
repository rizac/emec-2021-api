"""
utilities for FDSN queries
(https://www.fdsn.org/webservices/fdsnws-event-1.2.pdf)
"""
from datetime import datetime
from enum import Enum
from io import BytesIO
from typing import Any

import pandas as pd
from obspy import Catalog, UTCDateTime
from obspy.core.event import Event, Origin, Magnitude, resourceid, base


from emec_2021.emec import EmecField


class Param(Enum):
    """
    FDSN required query params. Name should be the short name, value the verbose
    one. If the param has no alias, map the param name to itself.
    (https://www.fdsn.org/webservices/fdsnws-event-1.2.pdf)
    """
    minlat = 'minlatitude'
    maxlat = 'maxlatitude'
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
    format='format'


def apply_query_param(
        catalog: pd.DataFrame, param: Param, value: Any, strict_check=True
) -> pd.DataFrame:
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
        order_by, ascending = value
        return catalog.sort_values(by=order_by, ascending=ascending)
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
    if col == Param.magtype:
        return col, str(value)
    if col == Param.orderby:
        # orderby required time Valid sort value string
        # Order the result by time or magnitude with the following possibilities:
        # time: order by origin descending time
        # time-asc: order by origin ascending time
        # magnitude: order by descending magnitude
        # magnitude-asc: order by ascending magnitude
        try:
            (order_by, ascending) = {
                'time': (EmecField.time, False),
                'time-asc': (EmecField.time, True),
                'magnitude': (EmecField.mag, False),
                'magnitude-asc': (EmecField.mag, True)
            }[str(value)]
            return col, (order_by, ascending)
        except KeyError:
            raise ValueError(f'Invalid value for orderby: {str(value)}')
    if col == Param.format:
        if value not in ('text', 'xml'):
            raise ValueError(f'Invalid value for format: {str(value)}')
        return col, value
    return col, float(value)


def to_text(catalog: pd.DataFrame) -> BytesIO:
    b = BytesIO()
    b.write(('#EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|'
             'ContributorID|MagType|Magnitude|MagAuthor|EventLocationName|EventType')
            .encode('utf8'))
    iterator = catalog_iterator(catalog, na_repr='')
    for ev_id, timestamp, lat, lon, depth, mag, magtype, isc_id in iterator:
        c = 'ISC' if isc_id > 0 else ''
        cid = isc_id if isc_id > 0 else ''
        dtime = '' if not timestamp else datetime.fromtimestamp(timestamp).isoformat()
        b.write(f'\n{ev_id}|{dtime}|'
                f'{lat}|{lon}|{depth}||EMEC-2021|{c}|{cid}|{magtype}|{mag}|||'
                f'earthquake'.encode('utf8'))
    b.seek(0)
    return b


def to_xml(catalog: pd.DataFrame) -> BytesIO:
    events = []
    iterator = catalog_iterator(catalog, na_repr=None)

    for ev_id, timestamp, lat, lon, depth, mag, magtype, isc_id in iterator:
        time = None if timestamp is None else \
            UTCDateTime(datetime.fromtimestamp(timestamp))
        evt_params = {
            'resource_id': rid(ev_id),
            'origins': [Origin(latitude=lat, longitude=lon, depth=depth, time=time,
                               resource_id=rid(f'origin/{ev_id}'))],
            'magnitudes': [Magnitude(mag=mag, magnitude_type=magtype,
                                     resource_id=rid(f'magnitude/{ev_id}'))]
        }
        if isc_id > 0:
            evt_params['creation_info'] = base.CreationInfo(author='ISC')
        events.append(Event(**evt_params))
    bio = BytesIO()
    Catalog(events, resource_id=rid()).write(bio, format="QUAKEML")  # noqa
    bio.seek(0)
    return bio


def rid(resid=None):
    _id = 'EMEC-2021' if resid is None else f'EMEC-2021/{resid}'
    return resourceid.ResourceIdentifier(_id).get_quakeml_id('org.gfz-potsdam.de')


def catalog_iterator(catalog: pd.DataFrame, na_repr=None):
    columns = [
        EmecField.eventid,
        EmecField.time,
        EmecField.lat,
        EmecField.lon,
        EmecField.depth,
        EmecField.mag,
        EmecField.magtype,
        EmecField.iscid,
    ]
    nan_values = pd.isna(catalog[columns]).values
    row_is_nan = nan_values.any(axis=1)
    for i, data in enumerate(zip(*[catalog[c] for c in columns])):
        if row_is_nan[i]:
            data = [na_repr if nan_values[i][j] else d for j, d in enumerate(data)]
        yield data
