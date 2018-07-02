import matplotlib.pyplot as plt
import h5py

# open the file
with h5py.File('synthetic_out.h5') as dataH5:
    # get the keys
    #key_list = dataH5.keys()
    for key in ['/building1/elec/meter1', '/building1/elec/meter2', '/building1/elec/meter3']:
        # show every matrix for a given key
        matrix = dataH5.get(key)
        print(matrix)
        #plt.imshow(matrix.reshape(matrix.shape[0], matrix.shape[1]), cmap=plt.cm.Greys)
        plt.show()
