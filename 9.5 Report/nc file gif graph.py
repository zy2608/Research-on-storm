import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.animation as animation
file_path = r'C:\Users\10575\Desktop\TE_ready_MERRA2_198001.nc'
dataset = nc.Dataset(file_path)
slp = dataset.variables['SLP'][:]
lat = dataset.variables['lat'][:]
lon = dataset.variables['lon'][:]
time = dataset.variables['time'][:]
fig, ax = plt.subplots(figsize=(10, 6))


lat_mid = lat.shape[0] // 2
lon_mid = lon.shape[0] // 2
contour = ax.contourf(lon, lat, slp[0, :, :], cmap='coolwarm')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Sea Level Pressure')
cbar = fig.colorbar(contour)
cbar.set_label('Sea Level Pressure (hPa)')


def update(frame):
    ax.clear()
    contour = ax.contourf(lon, lat, slp[frame, :, :], cmap='coolwarm')
    ax.set_title(f"Day {frame + 1}: Sea Level Pressure")
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    return contour

# To create an animation, interval is the time interval between each frame (in milliseconds)
ani = animation.FuncAnimation(fig, update, frames=7, interval=500, repeat=True)
ani.save('sea_level_pressure_animation.gif', writer='imagemagick')
plt.show()
