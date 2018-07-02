from __future__ import print_function, division
import os

# import synthetic
# synthetic.generate_dataset('data/synthetic.h5')
# synthetic.convert_metadata('data/synthetic.h5')

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
from nilmtk.disaggregate import combinatorial_optimisation, fhmm_exact

train = DataSet('data/synthetic.h5')
test = DataSet('data/synthetic.h5')

building = 1

train.set_window(end="31-12-2017")
test.set_window(start="31-12-2017")

train_elec = train.buildings[1].elec
test_elec = test.buildings[1].elec


co = combinatorial_optimisation.CombinatorialOptimisation()
co.train(train_elec)
print(co.model)
print(co.state_combinations)

os.mknod('data/synthetic_out.h5')
out = HDFDataStore('data/synthetic_out.h5')
co.disaggregate(test_elec, out)
print(co.model)
print(co.state_combinations)

co.export_model('data/synthetic3.mdl')

# fhmm = fhmm_exact.FHMM()
# fhmm.train(train_elec)
# print(fhmm.model)
# out = HDFDataStore('synthetic_out.h5')
# fhmm.disaggregate(test_elec.mains(), out)

out = DataSet('data/synthetic_out.h5')
out_elec = out.buildings[1].elec

# train_elec.plot()
test_elec.mains().plot()
# test_elec['linear fluorescent lamp'].plot()
out_elec['linear fluorescent lamp'].plot()

# test1 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter1', mode='r')
# test1.plot()
# test2 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter2', mode='r')
# test2.plot()
# test3 = pd.read_hdf('gaia_sparkworks.h5', '/building1/elec/meter3', mode='r')
# test3.plot()

plt.show()
