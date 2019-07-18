import os
import sys
import math
import time
import datetime as dt
import pytz
import glob
import pkg_resources
import yaml
import requests
import pandas as pd
from pprint import pprint


def download(api_key, hdf_filename, periods_to_load=None):

    with open(pkg_resources.resource_filename(__name__, 'metadata/dataset.yaml'), 'r') as dataset_stream:
        dataset = yaml.load(dataset_stream, Loader=yaml.FullLoader)
    with open(pkg_resources.resource_filename(__name__, 'metadata/meter_devices.yaml'), 'r') as meters_stream:
        meters = yaml.load(meters_stream, Loader=yaml.FullLoader)

    building_paths = glob.glob(pkg_resources.resource_filename(__name__, 'metadata/building[1-3].yaml'))

    for bp in building_paths:
        with open(bp, 'r') as building_stream:
            building = yaml.load(building_stream, Loader=yaml.FullLoader)

        if periods_to_load is None:
            hdf_store = pd.HDFStore(hdf_filename, 'r')
            start_date = dt.datetime.now()
            end_date = dt.datetime.now()
            meter_types = ['env_meters', 'net_meters', 'qos_meters', 'elec_meters']
            for mt in meter_types:
                for m in building[mt]:
                    ts = hdf_store[building[mt][m]['data_location']].head(1).index.item()/1000000000
                    _start_date = dt.datetime.fromtimestamp(ts)
                    if _start_date < start_date:
                        start_date = _start_date
            hdf_store.close()
        else:
            start_date = periods_to_load['start_date']
            end_date = periods_to_load['end_date']

        meter_types = ['wthr_meters']
        for mt in meter_types:
            for m in building[mt]:
                location = building[mt][m]['location']
                lat = location['latitude']
                lng = location['longitude']
                dpath = building[mt][m]['data_location']

                hdf_store = pd.HDFStore(hdf_filename, 'r')
                print(dpath)
                print(hdf_store.keys())
                if dpath in hdf_store.keys():
                    start_date = pd.to_datetime(hdf_store[dpath].tail(1).index.item())
                    start_date = start_date + dt.timedelta(hours=12)
                    print(start_date)
                hdf_store.close()

                dataframe = None

                while start_date < end_date:
                    forecast = load_forecast(api_key, lat, lng, req_time=start_date)
                    dtfm = pd.DataFrame(forecast.json()['hourly']['data'])
                    dtfm.set_index('time', inplace=True)
                    dtfm.index = pd.to_datetime(dtfm.index.values, unit='s')
                    if dataframe is None:
                        dataframe = dtfm
                    else:
                        dataframe = dataframe.append(dtfm, sort=True)
                    ts = dataframe.tail(1).index.item()/1000000000
                    start_date = dt.datetime.fromtimestamp(ts) + dt.timedelta(hours=12)

                if dataframe is not None:
                    print(dataframe)
                    dataframe.sort_index(inplace=True)
                    dataframe = dataframe.groupby(dataframe.index).first()
                    hdf_store = pd.HDFStore(hdf_filename, 'a')
                    dataframe.to_hdf(hdf_filename, dpath,
                                     mode='a', format='table', append=True,
                                     data_columns=True, complevel=9, complib='zlib')
                    hdf_store.close()


def load_forecast(key, lat, lng, req_time=None, units="auto", lang="en"):
    url_time = int(req_time.replace(microsecond=0).timestamp())
    print(url_time)
    url = 'https://api.darksky.net/forecast/%s/%s,%s,%s' \
          '?units=%s&lang=%s' % (key, lat, lng, url_time, units, lang)
    return requests.get(url)
