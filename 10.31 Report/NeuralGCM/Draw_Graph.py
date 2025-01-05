import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np


ds = xr.open_zarr('gs://weatherbench2/datasets/neuralgcm_ens/2020-240x121_equiangular_with_poles_conservative.zarr')
# ds_new = ds[["v_component_of_wind", "u_component_of_wind", "temperature", "geopotential", "wind_speed"]]
# ds_new["geopotentialheight"] = ds_new["geopotential"] / 9.8
# ds_new = ds_new.drop_vars("geopotential")


ds_july = ds.sel(time=ds.time.dt.month == 7)

ds_filtered = ds_july.sel(time=ds_july.time.dt.hour.isin([0, 6, 12, 18]))
ds_filtered = ds_filtered.sel(level=[300, 400, 500])
level_300_data = ds_filtered.sel(level=300)

initial_time = np.datetime64("2020-07-01")
plt.figure(figsize=(15, 10))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN, facecolor='lightskyblue')
plt.title("Storm Tracks Based on Latitude and Longitude (15-day forecast)")

for timedelta in ds_july.prediction_timedelta[:15]:  
    
    prediction_time = initial_time + timedelta.values    
    current_data = ds_july.sel(prediction_timedelta=timedelta, realization=5, level =400,time=initial_time)    
    if 'latitude' in current_data and 'longitude' in current_data:
        lats = current_data['latitude'].values
        lons = current_data['longitude'].values

        print(f"Time Step {timedelta}:")
        print(f"Latitudes: {lats}")
        print(f"Longitudes: {lons}")        
        if len(lats) > 0 and len(lats) == len(lons):
            plt.scatter(lons, lats, color='blue', s=10, transform=ccrs.PlateCarree(), alpha=0.6, label="Storm Track" )

plt.legend(loc="lower left")

plt.show()