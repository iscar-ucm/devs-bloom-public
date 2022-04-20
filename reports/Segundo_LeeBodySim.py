import pandas as pd
import matplotlib.pyplot as plt
import netCDF4
from site import addsitedir   #Para añadir la ruta del proyecto
addsitedir("C:/Users/segu2/OneDrive - Universidad Complutense de Madrid (UCM)/devs-bloom-1") 

filename = './body/Washington-1d-2008-09-12_compr.nc'
nc = netCDF4.Dataset(filename)
# File info format HDF5:
import numpy as np
# File info
#print(nc) # General attributes
print(nc.dimensions)
print(nc.variables.keys()) # All variables names
#print(nc.variables) # All variables and their attributes

# Read variables
#   Not all variables have the same dimensions, see file info for details
lat = np.array(nc['lat'])
lon = np.array(nc['lon'])
time= np.array(nc['time'])
layers= np.array(nc['layers'])
WQ_O= np.array(nc['WQ_O'])

# Remove fill values
#   The cells in which no water is present are filled with FillValue
#   Change FillValue to NaN so that those cells don't appear in the plot
lat[lat == nc['lat'].FillValue] = np.nan
lon[lon == nc['lon'].FillValue] = np.nan
WQ_O[WQ_O== nc['WQ_O'].FillValue]=np.nan

# Plots
from matplotlib import pyplot as plt

#WQ_O
#plt.figure(figsize=(5, 5), dpi=300)
#plt.imshow(WQ_O[1,:,:,1], cmap=plt.cm.jet,origin='lower')

plt.figure(figsize=(4, 4), dpi=300)
plt.scatter(lon,lat,c=WQ_O[1,:,:,2] , s=5, cmap=plt.cm.jet)
cbar = plt.colorbar()

plt.show()

