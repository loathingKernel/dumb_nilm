import time
from datetime import datetime, timedelta
from inspect import currentframe, getfile, getsourcefile
from os import getcwd
from os.path import join, isdir, dirname, abspath
from sys import getfilesystemencoding

import pandas as pd
import requests
import yaml
from dateutil.relativedelta import relativedelta
from nilmtk.measurement import LEVEL_NAMES
from nilm_metadata import convert_yaml_to_hdf5
from pkg_resources import resource_filename
import pprint

api_url = "http://150.140.5.23:9000/v1/data"


def download(hdf_filename, periods_to_load=None):

    with open(resource_filename(__name__, 'metadata/dataset.yaml'), 'r') as dtst_stream:
        dtst = yaml.load(dtst_stream)

    with open(resource_filename(__name__, 'metadata/building1.yaml'), 'r') as bldn_stream:
        bldn = yaml.load(bldn_stream)

    with open(resource_filename(__name__, 'metadata/meter_devices.yaml'), 'r') as mtrd_stream:
        mtrd = yaml.load(mtrd_stream)

    for m in bldn['elec_meters']:
        uri = bldn['elec_meters'][m]['meter_uri']

        params = {'uri': uri, 'size': 1000000}
        resp = requests.get(api_url + '/search/findByUri', params=params).json()
        while True:
            print('Processing page: '+str(resp['page']['number'])+' of '+str(resp['page']['totalPages'])+' for '+str(uri))

            _embedded = resp['_embedded']
            for d in _embedded['rawDatas']:
                del d['_links']
                del d['uri']

            dtfm = pd.DataFrame(_embedded['rawDatas'], columns=['timestamp', 'value'])

            dtfm.set_index('timestamp', inplace=True)
            dtfm.index = pd.to_datetime(dtfm.index.values, utc=True)
            # dtfm.rename(columns={'reading': ('current', '')}, inplace=True)
            dtfm.columns = pd.MultiIndex.from_tuples([('power', 'reactive')])
            dtfm.columns.set_names(LEVEL_NAMES, inplace=True)

            dtfm = dtfm.tz_convert(dtst['timezone'])
            dtfm = dtfm.div(1000, axis='columns')
            dtfm = dtfm.mul(230, axis='columns')

            # TODO: check this
            # dtfm.columns = pd.MultiIndex.from_arrays([msr[0]['physical_quantity'], msr[0]['type']])

            # print(dtfm)

            dtfm.to_hdf(hdf_filename, bldn['elec_meters'][m]['data_location'],
                        mode='a', format='table', complevel=9, complib='zlib')

            _links = resp['_links']
            if _links['self']['href'] == _links['last']['href']:
                break
            else:
                resp = requests.get(_links['next']['href']).json()


def convert_metadata(hdf_filename):
    convert_yaml_to_hdf5(join(_get_module_directory(), 'metadata'), hdf_filename)


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


def _find_by_uri(uri, page=None, size=None, sort=None):
    path = '/search/findByUri'
    params = {'uri': uri}
    if page is not None:
        params['page'] = page
    if size is not None:
        params['size'] = size
    if sort is not None:
        params['sort'] = sort
    return _api_get(path, params)


def _api_get(path, params):
    return requests.get(api_url + path, params=params)


def _api_post(path, payload):
    return requests.post(api_url + path, json=payload)

