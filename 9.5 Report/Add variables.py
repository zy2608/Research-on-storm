import netCDF4 as nc
import matplotlib.pyplot as plt

file_path = r'C:\Users\10575\Desktop\TE_ready_MERRA2_198001.nc'
dataset = nc.Dataset(file_path)

slp = dataset.variables['SLP'][:]
u10m = dataset.variables['U10M'][:]
v10m = dataset.variables['V10M'][:]
lat = dataset.variables['lat'][:]
lon = dataset.variables['lon'][:]

plt.figure(figsize=(12, 8))
plt.contourf(lon, lat, slp[0, :, :], cmap='coolwarm', alpha=0.6)
plt.colorbar(label='Sea Level Pressure (hPa)')
plt.quiver(lon[::5], lat[::5], u10m[0, ::5, ::5], v10m[0, ::5, ::5], scale=500, color='black')

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('SLP and Wind Vectors at 10m Height')
plt.show()
