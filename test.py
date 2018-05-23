from nilmtk import DataSet
from nilmtk.utils import print_dict
from IPython.core.display import display

gaia = DataSet('gaia_spark_dataset.h5')

print_dict(gaia.metadata)
print_dict(gaia.buildings)

