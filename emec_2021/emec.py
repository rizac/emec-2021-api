import urllib.request
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from os.path import dirname, join

import pandas as pd

FILENAME = 'EMEC-2021_events'


class EmecField:
    """Enum displaying EMEC source data columns names"""
    eventid = 'event_id'
    time = 'time'  # is a unix timestamp (see below)
    lat = 'latitude'
    lon = 'longitude'
    mag = 'magnitude'
    magtype = 'magnitudetype'
    depth = 'depth'
    iscid = 'isc_id'


def read_emec(url, save=True) -> pd.DataFrame:
    with urllib.request.urlopen(url) as _:
        zip_file = zipfile.ZipFile(BytesIO(_.read()))
    ret = pd.read_csv(zip_file.open(FILENAME + '.csv'))
    zip_file.close()

    # convert columns:

    # Date times: pandas to_datetime is limited to ~= 580 years
    # (https://stackoverflow.com/a/69507200), so cionvert to datetime.timestamp using
    # apply:
    def to_datetime(series):
        y, mo, d, s = series.tolist()
        # sometimes s=60, and consequently we should increase min, and hours, and so on
        # delegate python for that via timedelta:
        return (datetime(y, mo, d) + timedelta(seconds=s)).timestamp()

    dtime_cols = ['year', 'month', 'day', 'hour', 'minute', 'second']
    dtime_df = ret[dtime_cols].fillna(0).astype(int)
    # fix missing month/day and month day = 0: take 1 in both cases:
    dtime_df.loc[pd.isna(dtime_df['month']) == 0, 'month'] = 1
    dtime_df.loc[pd.isna(dtime_df['day']) == 0, 'day'] = 1
    # fix second=60 by providing a "total second" column (handled in to_datetime above):
    dtime_df['second'] = (
        dtime_df['hour'] * 3600 + dtime_df['minute'] * 60 + dtime_df['second']
    )
    dtime_df.drop(columns=['hour', 'minute'], inplace=True)

    # other columns:
    emec_df = pd.DataFrame({
        EmecField.eventid: ret[EmecField.eventid].astype(int),
        EmecField.time: dtime_df.apply(to_datetime, axis='columns'),
        EmecField.lat: ret[EmecField.lat].astype(float),
        EmecField.lon: ret[EmecField.lon].astype(float),
        EmecField.mag: ret['originalmag'].astype(float),
        EmecField.magtype: ret['originalmagtype'].astype('category'),
        EmecField.depth: ret[EmecField.depth].astype(float),
        EmecField.iscid: ret[EmecField.iscid].fillna(0).astype(int)
    })

    if save:
        emec_df.to_hdf(
            join(dirname(__file__), FILENAME + '.hdf'), key='emec', format='table'
        )
    return ret


if __name__ == "__main__":
    read_emec('https://datapub.gfz-potsdam.de/download/'
              '10.5880.GFZ.EMEC.2021.001-Lewfnu/EMEC-2021.zip')

    # ret = pd.read_hdf('/Users/rizac/work/gfz/projects/sources/python/emec_2021_restful_api/emec_2021_restful_api/emec_2021/EMEC-2021_events.hdf')
    # def to_datetime(v):
    #     return datetime.fromtimestamp(v).isoformat()
    #
    # ret['time'] = ret['time'].apply(to_datetime)
    #
    # ret.to_hdf(join(dirname(__file__), FILENAME + '.hdf2'), key='emec',
    #            format='table')

    # ret1 = pd.read_hdf(
    #     '/Users/rizac/work/gfz/projects/sources/python/emec_2021_restful_api/emec_2021_restful_api/emec_2021/EMEC-2021_events.hdf')
    # ret2 = pd.read_hdf(
    #     '/Users/rizac/work/gfz/projects/sources/python/emec_2021_restful_api/emec_2021_restful_api/emec_2021/EMEC-2021_events.hdf2')
    #
    # print(ret1['time'].memory_usage(deep=True))
    # print(ret2['time'].memory_usage(deep=True))
    #
    # ret2['time'] = ret2['time'].astype("S19")
    # assert (ret2['time'] == b'1003-01-01T00:00:00').any()
    #
    # b = BytesIO()
    # ret2.to_csv(b)
    # bb = b.getvalue()
    # print(tmp2.memory_usage(deep=True))
    # asd = 8