#!/usr/bin/python

from __future__ import print_function, division
import pdb
import os
import sys
import warnings

#import gaiaspark
#import spark as sa
#gaiaspark.download(sa.uname, sa.pword, sa.clid, sa.clsec, 'data/gaiaspark.h5')
#gaiaspark.convert_metadata('data/gaiaspark.h5')

import pandas as pd
import matplotlib.pyplot as plt

import time
from matplotlib import rcParams
import numpy as np
from six import iteritems
from datetime import datetime as DateTime
from datetime import timezone
import pytz

import pprint

#%matplotlib inline

rcParams['figure.figsize'] = (13, 6)

from nilmtk import DataSet, TimeFrame, MeterGroup, HDFDataStore, CSVDataStore
from nilmtk.disaggregate import combinatorial_optimisation

train = DataSet('data/gaiaspark.h5')
test = DataSet('data/gaiaspark.h5')

building = 1

train.set_window(end='2017-12-31')
#test.set_window(start='2017-10-1', end='2018-02-01')
test.set_window(start='2017-11-13', end='2017-11-15')

train_elec = train.buildings[1].elec
test_elec = test.buildings[1].elec

co = combinatorial_optimisation.CombinatorialOptimisation()
co.import_model('data/synthetic3.mdl')
pprint.pprint(co.model)
pprint.pprint(co.state_combinations)
outfile = 'data/gaiaspark_out_2.h5'

if os.path.isfile(outfile):
    os.remove(outfile)

os.mknod(outfile)
out = HDFDataStore(outfile)
#warnings.simplefilter('error')
#warnings.simplefilter('ignore', UserWarning)
#warnings.simplefilter('ignore', DeprecationWarning)
#warnings.simplefilter('ignore', RuntimeWarning)
co.disaggregate(test_elec.mains()[3], out)

out = DataSet(outfile)
out_elec = out.buildings[1].elec

# train_elec.plot()
#plt.subplot(5, 2, 1)
test_elec.mains().plot()

#plt.subplot(5, 2, 2)
#test_elec.mains()[1].plot()
out_elec['linear fluorescent lamp', 1].plot()
#for i in range(2, 8):
#plt.subplot(5, 2, 1 + i)
#out_elec['computer', i].plot()

#plt.subplot(5, 2, 9)
#out_elec['ethernet switch', 1].plot()

#test_elec.mains()[2].plot()
# out_elec['linear fluorescent lamp', 2].plot()
# out_elec['projector'].plot()
# out_elec['computer', 1].plot()

#test_elec.mains()[3].plot()
#for i in range(3, 4):
#out_elec['linear fluorescent lamp', i].plot()

# test1 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter1', mode='r')
# test1.plot()
# test2 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter2', mode='r')
# test2.plot()
# test3 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter3', mode='r')
# test3.plot()
plt.show()
