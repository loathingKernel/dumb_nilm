import time
from datetime import datetime, timedelta
from inspect import currentframe, getfile, getsourcefile
from os import getcwd
from os.path import join, isdir, dirname, abspath
from sys import getfilesystemencoding

import pandas as pd
import requests
import yaml
from dateutil.relativedelta import relativedelta as RelativeDelta
from nilmtk.measurement import LEVEL_NAMES
from nilm_metadata import convert_yaml_to_hdf5

api_url = "https://api.sparkworks.net"
sso_url = "https://sso.sparkworks.net/aa/oauth/token"

token = {}


def download_gaiaspark(spark_user, spark_pass, spark_id, spark_secret, hdf_filename, periods_to_load=None):
    _connect(spark_user, spark_pass, spark_id, spark_secret)

    with open('metadata/dataset.yaml', 'r') as dtst_stream:
        dtst = yaml.load(dtst_stream)

    with open('metadata/building1.yaml', 'r') as bldn_stream:
        bldn = yaml.load(bldn_stream)

    with open('metadata/meter_devices.yaml', 'r') as mtrd_stream:
        mtrd = yaml.load(mtrd_stream)

    for m in bldn['elec_meters']:
        uri = bldn['elec_meters'][m]['name']
        msr = mtrd[bldn['elec_meters'][m]['device_model']]['measurements']

        start_date = _find_data_start(uri)
        # end_date = DateTime(2017, 9, 30)
        end_date = datetime.today()

        data = []

        while start_date < end_date:
            chnk_date = start_date + timedelta(days=30)
            response = _query_timerange({'from': start_date,
                                         'to': chnk_date,
                                         'resultLimit': None,
                                         'resourceURI': [uri],
                                         'granularity': '5min'})
            print(response['results'].keys())
            data += list(response['results'].values())[0]['data']
            start_date = datetime.fromtimestamp(data[-1]['timestamp'] / 1000) + timedelta(minutes=1)

        dtfm = pd.DataFrame(data, columns=['timestamp', 'reading'])

        dtfm.set_index('timestamp', inplace=True)
        dtfm.index = pd.to_datetime(dtfm.index.values, unit='ms', utc=True)
        # dtfm.rename(columns={'reading': ('current', '')}, inplace=True)
        dtfm.columns = pd.MultiIndex.from_tuples([('power', 'reactive')])
        dtfm.columns.set_names(LEVEL_NAMES, inplace=True)

        dtfm = dtfm.tz_convert(dtst['timezone'])
        dtfm = dtfm.div(1000, axis='columns')
        dtfm = dtfm.mul(240, axis='columns')

        # TODO: check this
        # dtfm.columns = pd.MultiIndex.from_arrays([msr[0]['physical_quantity'], msr[0]['type']])

        print(dtfm)

        dtfm.to_hdf(hdf_filename, bldn['elec_meters'][m]['data_location'],
                    mode='a', format='table', complevel=9, complib='zlib')


def convert_metadata(hdf_filename):
    convert_yaml_to_hdf5(join(_get_module_directory(), 'metadata'), hdf_filename)


def _get_token(un, pw, ci, cs):
    params = {'username': un,
              'password': pw,
              'grant_type': "password",
              'client_id': ci,
              'client_secret': cs}
    response = requests.post(sso_url, params)
    return response.json()


def _connect(un, pw, ci, cs):
    global token
    token = _get_token(un, pw, ci, cs)


def _api_get_authorized(path):
    return requests.get(api_url + path, headers={'Authorization': 'Bearer ' + token["access_token"]})


def _api_post_authorized(path, payload):
    return requests.post(api_url + path, headers={'Authorization': 'Bearer ' + token["access_token"]}, json=payload)


def _query_timerange(qstn):
    qrs = []
    for q in qstn['resourceURI']:
        qry = {'from': qstn['from'].timestamp() * 1000,
               'granularity': qstn['granularity'],
               'resourceURI': q,
               'resultLimit': qstn['resultLimit'],
               'to': qstn['to'].timestamp() * 1000}
        qrs.append(qry)
    pld = {'queries': qrs}
    resp = _api_post_authorized('/v1/resource/query/timerange', pld)
    return resp.json()


def _uri_details(uri):
    resp = _api_get_authorized('/v1/resource/uri/' + uri)
    return resp.json()


def _get_module_directory():
    # Taken from http://stackoverflow.com/a/6098238/732596
    path_to_this_file = dirname(getfile(currentframe()))
    if not isdir(path_to_this_file):
        encoding = getfilesystemencoding()
        path_to_this_file = dirname(str(__file__, encoding))
    if not isdir(path_to_this_file):
        abspath(getsourcefile(lambda _: None))
    if not isdir(path_to_this_file):
        path_to_this_file = getcwd()
    assert isdir(path_to_this_file), path_to_this_file + ' is not a directory'
    return path_to_this_file


def _find_data_start(uri):
    lower_date = datetime(2015, 1, 1)
    upper_date = datetime.today()
    creation_date = datetime.fromtimestamp(_uri_details(uri)['creationDate'] / 1000)
    if creation_date < lower_date:
        creation_date = lower_date
        for gran in ['month', 'day', 'hour', '5min']:
            resp = _query_timerange({'from': creation_date,
                                     'to': upper_date,
                                     'resultLimit': None,
                                     'resourceURI': [uri],
                                     'granularity': gran})
            # this works because we request only one uri
            data = list(resp['results'].values())[0]['data']
            for d in data:
                if d['reading'] != 0.0:
                    break
                creation_date = datetime.fromtimestamp(d['timestamp'] / 1000)
            # granularity 5min causes a TypeError but we don't care about it, so ingore it and continue
            try:
                upper_date = creation_date + RelativeDelta(**{gran + 's': +2})
            except TypeError:
                continue
    return creation_date


def _to_nano_timestamp(date_str):
    return int(time.mktime(datetime.strptime(date_str, "%Y-%m-%d").timetuple()) * 1000)


def _from_nano_timestamp(date_int):
    return datetime.fromtimestamp(date_int / 1000)
