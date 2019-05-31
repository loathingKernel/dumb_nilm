import time
from datetime import datetime, timezone, timedelta
import pytz
from inspect import currentframe, getfile, getsourcefile
from os import getcwd
from os.path import join, isdir, dirname, abspath
from sys import getfilesystemencoding

import pandas as pd
import requests
import yaml
from dateutil.relativedelta import relativedelta as RelativeDelta
from nilmtk.measurement import LEVEL_NAMES
import pkg_resources
import glob
from pprint import pprint
from sparkworks import SparkWorks
import credentials as creds


def download(usernm, passwd, cid, csecret, hdf_filename, periods_to_load=None):
    sw = SparkWorks(cid, csecret)
    sw.connect(usernm, passwd)

    with open(pkg_resources.resource_filename(__name__, 'metadata/dataset.yaml'), 'r') as dtst_stream:
        dtst = yaml.load(dtst_stream)
    with open(pkg_resources.resource_filename(__name__, 'metadata/meter_devices.yaml'), 'r') as mtrd_stream:
        mtrd = yaml.load(mtrd_stream)

    bldn_paths = glob.glob(pkg_resources.resource_filename(__name__, 'metadata/building*.yaml'))

    for bp in bldn_paths:
        with open(bp, 'r') as bldn_stream:
            bldn = yaml.load(bldn_stream)

        for m in bldn['elec_meters']:
            uuid = bldn['elec_meters'][m]['uuid']
            # msr = mtrd[bldn['elec_meters'][m]['device_model']]['measurements']

            start_date = findDataStart(sw, uuid)
            # end_date = DateTime(2017, 9, 30)
            end_date = datetime.today()

            data = []

            while start_date < end_date:
                chnk_date = start_date + timedelta(days=30)
                response = sw.timerange([uuid], start_date, end_date, "5min")
                print(response['results'].keys())
                data += list(response['results'].values())[0]['data']
                start_date = datetime.fromtimestamp(data[-1]['timestamp'] / 1000) + timedelta(minutes=1)

            dtfm = pd.DataFrame(data, columns=['timestamp', 'reading'])

            dtfm.set_index('timestamp', inplace=True)
            dtfm.index = pd.to_datetime(dtfm.index.values, unit='ms', utc=True)
            # dtfm.rename(columns={'reading': ('current', '')}, inplace=True)
            dtfm.columns = pd.MultiIndex.from_tuples([('power', 'active')])
            dtfm.columns.set_names(LEVEL_NAMES, inplace=True)
            dtfm = dtfm.tz_convert(dtst['timezone'])
            dtfm = dtfm.div(1000, axis='columns')
            dtfm = dtfm.mul(230, axis='columns')

            # TODO: check this
            # dtfm.columns = pd.MultiIndex.from_arrays([msr[0]['physical_quantity'], msr[0]['type']])

            print(dtfm)

            dtfm.to_hdf(hdf_filename, bldn['elec_meters'][m]['data_location'],
                        mode='a', format='table', complevel=9, complib='zlib')


def findDataStart(api, uuid):
    lower_date = datetime(2015, 1, 1, tzinfo=timezone.utc)
    pprint(lower_date)
    upper_date = datetime.now(timezone.utc)
    pprint(upper_date)
    resource = api.resourceByUuid(uuid)
    pprint(resource)
    creat_date = datetime.strptime(resource["createdDate"], "%Y-%m-%dT%H:%M:%S.%f%z")
    pprint(creat_date)
    creat_date = lower_date
    for gran in ['month', 'day', 'hour', '5min']:
        resp = api.timerange([uuid], creat_date, upper_date, gran)
        # this works because we request only one uri
        print(resp)
        data = list(resp['results'].values())[0]['data']
        for d in data:
            if d['reading'] != 0.0:
                break
            creat_date = datetime.fromtimestamp(d['timestamp'] / 1000)
        # granularity 5min causes a TypeError but we don't care about it, so ingore it and continue
        try:
            upper_date = creat_date + RelativeDelta(**{gran + 's': +2})
        except TypeError:
            continue
    return creat_date


def _to_nano_timestamp(date_str):
    return int(time.mktime(datetime.strptime(date_str, "%Y-%m-%d").timetuple()) * 1000)


def _from_nano_timestamp(date_int):
    return datetime.fromtimestamp(date_int / 1000)


if __name__ == '__main__':
    download(creds.username, creds.password, creds.client_id, creds.client_secret, 'data/gaiaspark.h5')
