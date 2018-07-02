# import time
from copy import deepcopy
from datetime import datetime as DateTime, timedelta as TimeDelta
from inspect import currentframe, getfile, getsourcefile
from os import getcwd
from os.path import join, isdir, dirname, abspath
from random import SystemRandom
from sys import getfilesystemencoding

import pandas as pd
import pytz
# import numpy as np
# import requests
import yaml
from nilm_metadata import convert_yaml_to_hdf5
# from dateutil.relativedelta import relativedelta as RelativeDelta
from nilmtk.measurement import LEVEL_NAMES
from pkg_resources import resource_string, resource_filename

nominal = {'linear fluorescent lamp': {'min': 35, 'max': 80},
           'desktop computer': {'min': 80, 'max': 150},
           'computer monitor': {'min': 10, 'max': 25},
           'computer': {'min': 90, 'max': 175},
           'ethernet switch': {'min': 20, 'max': 130},
           'projector': {'min': 215, 'max': 300}}


def generate_dataset(hdf_filename):

    with open(resource_filename(__name__, 'metadata/dataset.yaml'), 'r') as dtst_stream:
        dtst = yaml.load(dtst_stream)

    with open(resource_filename(__name__, 'metadata/building1.yaml'), 'r') as bldn_stream:
        bldn = yaml.load(bldn_stream)

    with open(resource_filename(__name__, 'metadata/meter_devices.yaml'), 'r') as mtrd_stream:
        mtrd = yaml.load(mtrd_stream)

    start_date = DateTime(2017, 9, 1).replace(tzinfo=pytz.UTC)
    end_date = DateTime.today().replace(tzinfo=pytz.UTC)
    date = start_date

    data = []
    while date < end_date:
        d = {'timestamp': int(date.timestamp()) * 1000, 'reading': 0}
        data.append(d)
        date += TimeDelta(minutes=5)

    meters = bldn['elec_meters']
    appliances = bldn['appliances']
    for site_meter in meters:
        if meters[site_meter].get('site_meter', False):
            site_data = deepcopy(data)
            print("Site Meter " + str(site_meter))
            for app_meter in meters:
                if site_meter == meters[app_meter].get('submeter_of', -1):
                    for app in appliances:
                        if app_meter in app.get('meters'):
                            app_data = deepcopy(data)
                            mi = nominal[app['type']]['min']
                            ma = nominal[app['type']]['max']
                            avg = (mi + ma) / 2
                            print("Appliance Meter " + str(app_meter) + ": " + app['type'] + "->" + str(avg))
                            for ap, sd in zip(app_data, site_data):
                                # value = random.SystemRandom().randint(0, 1) * avg
                                value = SystemRandom().randint(0, 1) * SystemRandom().randint(mi, ma)
                                value = value * app.get('count', 1)
                                ap['reading'] = value
                                sd['reading'] += value

                            _write_hdf5(dtst, bldn, app_data, app_meter, hdf_filename)

            _write_hdf5(dtst, bldn, site_data, site_meter, hdf_filename)


def convert_metadata(hdf_filename):
    convert_yaml_to_hdf5(join(_get_module_directory(), 'metadata'), hdf_filename)


def _write_hdf5(dataset, building, data, meter, filename):
    dtfm = pd.DataFrame(data, columns=['timestamp', 'reading'])
    dtfm.set_index('timestamp', inplace=True)
    dtfm.index = pd.to_datetime(dtfm.index.values, unit='ms', utc=True)
    # dtfm.rename(columns={'reading': ('current', '')}, inplace=True)
    dtfm.columns = pd.MultiIndex.from_tuples([('power', 'reactive')])
    dtfm.columns.set_names(LEVEL_NAMES, inplace=True)
    dtfm = dtfm.tz_convert(dataset['timezone'])
    dtfm.to_hdf(filename, building['elec_meters'][meter]['data_location'],
                mode='a', format='table', complevel=9, complib='zlib')


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

