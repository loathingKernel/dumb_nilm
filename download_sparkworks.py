import datetime
import time
from inspect import currentframe, getfile, getsourcefile
from os.path import isdir, dirname, abspath

import requests

api_url = "https://api.sparkworks.net"
sso_url = "https://sso.sparkworks.net/aa/oauth/token"

token = {}

def download_sparkworks(spark_user, spark_pass, spark_id, spark_secret,
                        hdf_filename, periods_to_load=None):

    _connect(spark_user, spark_pass, spark_id, spark_secret)

    store = pd.HDFStore(hdf_filename, 'w', complevel=9, complib='zlib')

    response = _query_timerange({'from': '2017-10-1',
                                'to': str(datetime.date.today),
                                'resourceURI': [
                                    '0013a20040b55ff0/0xe44/cur/1',
                                    '0013a20040b55ff0/0xe44/cur/2',
                                    '0013a20040b55ff0/0xe44/cur/3',
                                ],
                                'granularity': '5min'})


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
        qry = {'from': time.mktime(datetime.datetime.strptime(qstn['from'], "%Y-%m-%d").timetuple()) * 1000,
               'granularity': qstn['granularity'],
               'resourceURI': q,
               'to': time.mktime(datetime.datetime.strptime(qstn['to'], "%Y-%m-%d").timetuple()) * 1000}
        qrs.append(qry)
    pld = {'queries': qrs}
    resp = _api_post_authorized('/v1/resource/query/timerange', pld)
    return resp.json()


def _get_module_directory():
    # Taken from http://stackoverflow.com/a/6098238/732596
    path_to_this_file = dirname(getfile(currentframe()))
    if not isdir(path_to_this_file):
        encoding = getfilesystemencoding()
        path_to_this_file = dirname(unicode(__file__, encoding))
    if not isdir(path_to_this_file):
        abspath(getsourcefile(lambda _: None))
    if not isdir(path_to_this_file):
        path_to_this_file = getcwd()
    assert isdir(path_to_this_file), path_to_this_file + ' is not a directory'
return path_to_this_file