import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np

file_path = r'C:\Users\10575\Desktop\TE_ready_MERRA2_198001.nc'
dataset = nc.Dataset(file_path)


slp = dataset.variables['SLP'][:]
lat = dataset.variables['lat'][:]
lon = dataset.variables['lon'][:]
time = dataset.variables['time'][:]


start_day = 0
end_day = 7
fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(15, 10), constrained_layout=True)
lat_mid = lat.shape[0] // 2
lon_mid = lon.shape[0] // 2

for i in range(start_day, end_day):
    ax = axes.flatten()[i]
    cont = ax.contourf(lon, lat, slp[i, :, :], cmap='coolwarm')
    ax.set_title(f"Day {i + 1}: Sea Level Pressure")
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
fig.colorbar(cont, ax=axes[:, -1], orientation='vertical', fraction=0.05, pad=0.05)

plt.show()
