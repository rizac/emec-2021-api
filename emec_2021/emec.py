import urllib.request
import zipfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from io import BytesIO
from os.path import dirname, join, isfile, splitext, basename

import pandas as pd
from werkzeug.utils import secure_filename

# the default EMEC 2021 source URL (zip file)
SOURCE_URL = ('https://datapub.gfz-potsdam.de/download/'
              '10.5880.GFZ.EMEC.2021.001-Lewfnu/EMEC-2021.zip')

# the default EMEC 2021 file name within the zip file pointed by SOURCE_URL
SOURCE_FILENAME = 'EMEC-2021_events.csv'

# the default destination directory for the catalog file(s) (this dir by default)
DEST_PATH = dirname(__file__)


class EmecField:
    """Enum displaying EMEC catalog columns names. The catalog will be loaded from
    SOURCE_URL (see above) and processed in this module"""
    eventid = 'event_id'
    time = 'time'  # is a unix timestamp (see below)
    lat = 'latitude'
    lon = 'longitude'
    mag = 'magnitude'
    magtype = 'magnitudetype'
    originalmag = 'originalmag'
    originalmagtype = 'originalmagtype'
    depth = 'depth'
    iscid = 'isc_id'


def create_catalog(force_reload=False, verbose=False) -> pd.DataFrame:
    """
    Create and return the EMEC 2021 catalog as pandas DataFrame.
    This is the same catalog returned by ``get_source_catalog`` with some
    post-processing in order to harmonize and correct data.
    Note that the catalog will be saved under this directory and same base name as
    `src_filename`. If such a file already exist, the returned catalog will be
    read from the local file without HTTP requests

    @param force_reload: if True (default False): will force a full reload from the
        remote URL, overwriting all local files
    @param verbose: whether to print info (default: False)
    """
    src_filename = SOURCE_FILENAME
    dest_path = join(DEST_PATH, splitext(src_filename)[0] + '.hdf')

    if not force_reload and isfile(dest_path):
        return pd.read_hdf(dest_path)  # noqa

    src_url = SOURCE_URL
    src_path = join(DEST_PATH, src_filename)
    if force_reload or not isfile(src_path):
        if verbose:
            print(f'Fetching {src_filename} from {src_url}')
        with open_source_catalog(src_url, src_filename) as _src:
            with open(src_path, 'wb') as _dest:
                _dest.write(_src.read())

    if verbose:
        print(f'Reading {src_filename} from {dirname(src_path)}')
    ret = pd.read_csv(src_path)

    if verbose:
        print(f'Processing catalog')

    emec_df = process_source_catalog(ret)
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


@contextmanager
def open_source_catalog(src_url=SOURCE_URL, src_filename=SOURCE_FILENAME):
    """
    Return the EMEC 2021 source catalog as pandas DataFrame

    @param src_url: the source catalog URL (zip file)
    @param src_filename: the source catalog file name within the zip
        file pointed by `src_url`
    """
    with urllib.request.urlopen(src_url) as _:
        zip_file = zipfile.ZipFile(BytesIO(_.read()))
    yield zip_file.open(src_filename)
    zip_file.close()


def process_source_catalog(src_catalog: pd.DataFrame) -> pd.DataFrame:
    """
    Process the given soruce catalog into a catalog to be used within this app
    """
    # filter out historic events (before 1900):
    ret = src_catalog[src_catalog['year'] >= 1900].copy()

    # Handle datetime(s): pandas to_datetime is limited to ~= 580 years
    # (https://stackoverflow.com/a/69507200), so use to datetime.timestamp(s) (float)
    # First create a datetime dataframe:
    dtime_df = ret[['year', 'month', 'day', 'second']].copy().fillna(0).astype(int)
    # fix month or day = 0 and set to 1 in both cases:
    dtime_df.loc[dtime_df['month'] == 0, 'month'] = 1
    dtime_df.loc[dtime_df['day'] == 0, 'day'] = 1
    # fix seconds = 60. The easiest way is to set a "total second" column:
    h = ret['hour'].fillna(0).astype(int)
    m = ret['minute'].fillna(0).astype(int)
    dtime_df['second'] = (h * 3600 + m * 60 + dtime_df['second'])

    # apply function converting the datetime dataframe to timestamps:
    def to_datetime(series):
        y, mo, d, s = series.tolist()
        # sometimes s=60, and consequently we should increase min, and hours, and so on
        # delegate python for that via timedelta:
        return (datetime(y, mo, d) + timedelta(seconds=s)).timestamp()

    # other columns:
    return pd.DataFrame({
        EmecField.eventid: ret[EmecField.eventid].astype(int),
        EmecField.time: dtime_df.apply(to_datetime, axis='columns'),
        EmecField.lat: ret[EmecField.lat].astype(float),
        EmecField.lon: ret[EmecField.lon].astype(float),
        EmecField.mag: ret['mw'].astype(float),
        EmecField.magtype: pd.Series(['Mw'] * len(ret), index=ret.index, dtype='category'),
        EmecField.originalmag: ret['originalmag'].astype(float),
        EmecField.originalmagtype: ret['originalmagtype'].fillna('').astype('category'),
        EmecField.depth: ret[EmecField.depth].astype(float),
        EmecField.iscid: ret[EmecField.iscid].fillna(0).astype(int)
    })


if __name__ == "__main__":
    create_catalog(force_reload=True, verbose=True)
