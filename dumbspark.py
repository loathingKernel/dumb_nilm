import requests
import time
import datetime
import json
import numpy
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot
import matplotlib.dates
import csv

api_url = "https://api.sparkworks.net"
sso_url = "https://sso.sparkworks.net/aa/oauth/token"

client_id = "spark"
client_secret = "spark"
username = "spark"
password = "spark"

#client_id = "GAIAWorkshop"
#client_secret = "07a746c1-dd58-44bd-819a-61e8f9a8231d"
#usernm = "greenmindset44"
#passwd = "7A2E7FBF5"

token = {}


def get_token():
    params = {'username': username,
              'password': password,
              'grant_type': "password",
              'client_id': client_id,
              'client_secret': client_secret}
    response = requests.post(sso_url, params)
    return response.json()


def connect():
    global token
    token = get_token()


def api_get_authorized(path):
    return requests.get(api_url + path, headers={'Authorization': 'Bearer ' + token["access_token"]})


def api_post_authorized(path, payload):
    return requests.post(api_url + path, headers={'Authorization': 'Bearer ' + token["access_token"]}, json=payload)


def query_timerange(question):
    queries = []
    for q in question['resourceURI']:
        query = {'from': time.mktime(datetime.datetime.strptime(question['from'], "%Y/%m/%d").timetuple()) * 1000,
                 'granularity': question['granularity'],
                 'resourceURI': q,
                 'to': time.mktime(datetime.datetime.strptime(question['to'], "%Y/%m/%d").timetuple()) * 1000}
        queries.append(query)
    payload = {'queries': queries}
    resp = api_post_authorized('/v1/resource/query/timerange', payload)
    return resp.json()


connect()

response = query_timerange({'from': '2017/10/1',
                            'to': '2018/5/10',
                            'resourceURI': [
                                '0013a20040b55ff0/0xe44/cur/1',
                                '0013a20040b55ff0/0xe44/cur/2',
                                '0013a20040b55ff0/0xe44/cur/3',
                            ],
                            'granularity': 'hour'})

results = response['results']
print(list(results.keys())[0])
resource = list(results.values())[0]
data = resource['data']

timestamps = []
values = []
dic = {'timestamps': timestamps, 'values': values}

for d in data:
    timestamps.append(datetime.datetime.fromtimestamp(d['timestamp'] / 1000))
    values.append(float(d['reading']))

print("Gathering finished. Starting plot")
print(len(timestamps), len(values))

mjl = matplotlib.dates.MonthLocator()
dFmt = matplotlib.dates.DateFormatter('%y-%m-%d')

fig, ax = matplotlib.pyplot.subplots(figsize=(480, 6), dpi=80)
ax.plot(timestamps, values)

ax.xaxis.set_major_locator(mjl)
ax.xaxis.set_major_formatter(dFmt)

ax.set(xlabel='time', ylabel='mW')
ax.grid()

fig.savefig("test" + str(1) + ".png")
matplotlib.pyplot.show()
