import time
import datetime as dt
import pytz
from inspect import currentframe, getfile, getsourcefile
from os import getcwd
from os.path import join, isdir, dirname, abspath
from sys import getfilesystemencoding

import pandas as pd
import requests
import yaml
from dateutil.relativedelta import relativedelta
from nilmtk.measurement import LEVEL_NAMES
import pkg_resources
import glob
from pprint import pprint


def download(sparkworks, hdf_filename, periods_to_load=None):

    with open(pkg_resources.resource_filename(__name__, 'metadata/dataset.yaml'), 'r') as dataset_stream:
        dataset = yaml.load(dataset_stream, Loader=yaml.FullLoader)
    with open(pkg_resources.resource_filename(__name__, 'metadata/meter_devices.yaml'), 'r') as meters_stream:
        meters = yaml.load(meters_stream, Loader=yaml.FullLoader)

    building_paths = glob.glob(pkg_resources.resource_filename(__name__, 'metadata/building[1-3].yaml'))

    for bp in building_paths:
        with open(bp, 'r') as building_stream:
            building = yaml.load(building_stream, Loader=yaml.FullLoader)

        meter_types = ['env_meters', 'net_meters', 'qos_meters', 'elec_meters']
        for mt in meter_types:
            for m in building[mt]:
                uuids = building[mt][m]['uuid']
                dpath = building[mt][m]['data_location']

                if periods_to_load is None:
                    start_date = dt.datetime.now()
                    for _u in uuids:
                        if uuids[_u] is None:
                            continue
                        _start_date = findDataStart(sparkworks, uuids[_u])
                        if _start_date < start_date:
                            start_date = _start_date
                    end_date = dt.datetime.now()
                else:
                    start_date = periods_to_load['start_date']
                    end_date = periods_to_load['end_date']

                hdf_store = pd.HDFStore(hdf_filename, 'r')
                print(dpath)
                print(hdf_store.keys())
                if dpath in hdf_store.keys():
                    start_date = pd.to_datetime(hdf_store[dpath].tail(1).index.item())
                    start_date = start_date + dt.timedelta(minutes=5)
                    print(start_date)
                hdf_store.close()

                dataframe = None

                while start_date < end_date:
                    print(start_date)
                    chunk_date = start_date + dt.timedelta(days=5)
                    uuid_list = [uuids[x] for x in uuids if uuids[x] is not None]
                    response = sparkworks.timerange(uuid_list, start_date, chunk_date, "5min")
                    _dataframe = None
                    for result in response['results']:
                        print(result)
                        for _u in uuids:
                            if uuids[_u] is None:
                                continue
                            if uuids[_u] in result:
                                data = list(response['results'][result]['data'])
                                _dtfm = pd.DataFrame(data, columns=['timestamp', 'reading'])
                                _dtfm.set_index('timestamp', inplace=True)
                                _dtfm.index = pd.to_datetime(_dtfm.index.values, unit='ms')
                                _dtfm.rename(columns={'reading': _u}, inplace=True)
                                if _dataframe is None:
                                    _dataframe = _dtfm
                                else:
                                    _dataframe = _dataframe.join(_dtfm)
                    if dataframe is None:
                        dataframe = _dataframe
                    else:
                        dataframe = dataframe.append(_dataframe, sort=True)
                    ts = dataframe.tail(1).index.item()/1000000000
                    start_date = chunk_date

                # dataframe.columns = pd.MultiIndex.from_tuples([('power', 'active')])
                # dataframe.columns.set_names(LEVEL_NAMES, inplace=True)
                # dataframe = dataframe.tz_convert(dataset['timezone'])
                # dataframe = dataframe.div(1000, axis='columns')
                # dataframe = dataframe.mul(230, axis='columns')

                # TODO: check this
                # dtfm.columns = pd.MultiIndex.from_arrays([msr[0]['physical_quantity'], msr[0]['type']])

                if dataframe is not None:
                    print(dataframe)
                    dataframe.sort_index(inplace=True)
                    dataframe = dataframe.groupby(dataframe.index).first()
                    hdf_store = pd.HDFStore(hdf_filename, 'a')
                    dataframe.to_hdf(hdf_store, dpath,
                                     mode='a', format='table', append=True,
                                     data_columns=True, complevel=9, complib='zlib')
                    hdf_store.close()


def findDataStart(api, uuid):
    lower_date = dt.datetime(2015, 1, 1)
    upper_date = dt.datetime.now()
    resource = api.resourceByUuid(uuid)
    creat_date = dt.datetime.strptime(resource["createdDate"], "%Y-%m-%dT%H:%M:%S.%f%z")
    creat_date = lower_date
    for gran in ['month', 'day', 'hour', '5min']:
        resp = api.timerange([uuid], creat_date, upper_date, gran)
        # this works because we request only one uri
        data = list(resp['results'].values())[0]['data']
        for d in data:
            if d['reading'] != 0.0:
                break
            creat_date = dt.datetime.fromtimestamp(d['timestamp'] / 1000)
        # granularity 5min causes a TypeError but we don't care about it, so ingore it and continue
        try:
            upper_date = creat_date + relativedelta(**{gran + 's': +2})
        except TypeError:
            continue
    return creat_date


def _to_nano_timestamp(date_str):
    return int(time.mktime(dt.datetime.strptime(date_str, "%Y-%m-%d").timetuple()) * 1000)


def _from_nano_timestamp(date_int):
    return dt.datetime.fromtimestamp(date_int / 1000)

