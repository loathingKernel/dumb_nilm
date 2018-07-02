from __future__ import print_function, division
import os

# import gaiaspark
# gaiaspark.download_gaiaspark(username, password, client_id, client_secret, name + ext)
# gaiaspark.convert_metadata(name + ext)

import pandas as pd
import matplotlib.pyplot as plt

import time
from matplotlib import rcParams
import numpy as np
from six import iteritems
import warnings
from datetime import datetime as DateTime
from datetime import timezone
import pytz

warnings.filterwarnings('ignore')
#%matplotlib inline

rcParams['figure.figsize'] = (13, 6)

from nilmtk import DataSet, TimeFrame, MeterGroup, HDFDataStore, CSVDataStore
from nilmtk.disaggregate import combinatorial_optimisation

train = DataSet('data/gaiaspark.h5')
test = DataSet('data/gaiaspark.h5')

building = 1

train.set_window(end='2017-12-31')
test.set_window(start='2017-10-1')

train_elec = train.buildings[1].elec
test_elec = test.buildings[1].elec

# co = combinatorial_optimisation.CombinatorialOptimisation()
# co.import_model('data/synthetic3.mdl')
# print(co.model)
# print(co.state_combinations)
#
# os.remove('data/gaiaspark_out.h5')
# os.mknod('data/gaiaspark_out.h5')
# out = HDFDataStore('data/gaiaspark_out.h5')
# co.disaggregate(test_elec.mains(), out)

out = DataSet('data/gaiaspark_out.h5')
out_elec = out.buildings[1].elec

# train_elec.plot()
# test_elec.mains().plot()

test_elec.mains()[1].plot()
# test_elec.mains()[2].plot()
# test_elec.mains()[3].plot()
out_elec['linear fluorescent lamp'].plot()
out_elec['computer'].plot()
out_elec['ethernet switch'].plot()
# out_elec['projector'].plot()


# test1 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter1', mode='r')
# test1.plot()
# test2 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter2', mode='r')
# test2.plot()
# test3 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter3', mode='r')
# test3.plot()
plt.show()
