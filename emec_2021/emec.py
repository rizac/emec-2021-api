import urllib.request
import zipfile
from datetime import datetime, timedelta, MINYEAR
from io import BytesIO
from os.path import dirname, join, isfile, splitext, basename

import pandas as pd


SOURCE_URL = ('https://datapub.gfz-potsdam.de/download/'
              '10.5880.GFZ.EMEC.2021.001-Lewfnu/EMEC-2021.zip')

SOURCE_FILENAME = 'EMEC-2021_events.csv'


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


def create_catalog(
        src_url=SOURCE_URL, src_filename=SOURCE_FILENAME, verbose=False
) -> pd.DataFrame:

    dest_path = join(dirname(__file__), splitext(src_filename)[0] + '.hdf')

    if isfile(dest_path):
        return pd.read_hdf(dest_path)  # noqa

    if verbose:
        print(f'Reading {src_filename} from {src_url}')
    ret = get_source_catalog(src_url, src_filename)

    if verbose:
        print(f'Processing catalog')

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
        EmecField.magtype: ret['originalmagtype'].fillna('').astype('category'),
        EmecField.depth: ret[EmecField.depth].astype(float),
        EmecField.iscid: ret[EmecField.iscid].fillna(0).astype(int)
    })

    emec_df.to_hdf(dest_path, key='emec', format='table')

    if verbose:
        print(f'Saved {basename(dest_path)} to {dirname(dest_path)}')
        print(f'(Events: {len(emec_df)}, Fields: {len(emec_df.columns)})')
        _data = []
        for c in emec_df.columns:
            dtype = emec_df[c].dtype
            if len(getattr(dtype, 'categories', [])):
                dtype = (f'{dtype.categories.dtype} '
                         f'({len(dtype.categories)} categories)')
            else:
                dtype = str(dtype)
            _data.append({'Field': c, 'dtype': str(dtype), 'Null/NaNs': emec_df[c].isna().sum()})
        print(pd.DataFrame(_data).to_string(index=False))

    return emec_df


def get_source_catalog(src_url=SOURCE_URL, src_filename=SOURCE_FILENAME) -> pd.DataFrame:
    with urllib.request.urlopen(src_url) as _:
        zip_file = zipfile.ZipFile(BytesIO(_.read()))
    ret = pd.read_csv(zip_file.open(src_filename))
    zip_file.close()
    return ret


if __name__ == "__main__":
    create_catalog(verbose=True)