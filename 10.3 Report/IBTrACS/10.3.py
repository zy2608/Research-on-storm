import netCDF4 as nc
import xarray as xr
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

#track of storm in 2022
ds = xr.open_dataset('/home/zy2608/zy2608/9.22/IBTrACS.last3years.v04r01.nc')

ds_2022 = ds.where(ds['season'] == 2022, drop=True)

max_wind_per_storm = ds_2022['usa_wind'].max(dim='date_time')

storms_with_high_wind = max_wind_per_storm.where(max_wind_per_storm > 34, drop=True)
high_wind_storms = ds_2022.sel(storm=storms_with_high_wind['storm'])

latitudes = high_wind_storms['usa_lat']
longitudes = high_wind_storms['usa_lon']
winds = high_wind_storms['usa_wind']

longitudes = ((longitudes + 180) % 360) - 180

categories = {
    'Tropical Storm': {'min': 34, 'max': 63, 'color': 'cyan'},
    'Category 1': {'min': 64, 'max': 82, 'color': 'green'},
    'Category 2': {'min': 83, 'max': 95, 'color': 'yellow'},
    'Category 3': {'min': 96, 'max': 112, 'color': 'orange'},
    'Category 4': {'min': 113, 'max': 136, 'color': 'red'},
    'Category 5': {'min': 137, 'color': 'purple'},
}

plt.figure(figsize=(15, 10))

ax = plt.axes(projection=ccrs.Robinson())
ax.set_global()
ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN, facecolor='lightskyblue')

plt.title("Storm Tracks with Max Wind Speed > 34 in 2022")

for storm_idx in range(latitudes.sizes['storm']):
    storm_lat = latitudes.isel(storm=storm_idx).dropna('date_time')
    storm_lon = longitudes.isel(storm=storm_idx).dropna('date_time')
    max_wind = max_wind_per_storm.isel(storm=storm_idx)

    for category, props in categories.items():
        if ('min' in props and 'max' in props and props['min'] <= max_wind <= props['max']) or \
           ('min' in props and max_wind >= props['min'] and 'max' not in props):
            storm_category = category
            color = props['color']
            break

    if len(storm_lon) > 1:
        split_indices = np.where(np.abs(np.diff(storm_lon)) > 180)[0] + 1
        split_lon = np.split(storm_lon, split_indices)
        split_lat = np.split(storm_lat, split_indices)
        for lon_segment, lat_segment in zip(split_lon, split_lat):
            plt.plot(lon_segment, lat_segment, color=color, transform=ccrs.PlateCarree(), alpha=0.6)

import matplotlib.patches as mpatches
handles = [mpatches.Patch(color=props['color'], label=category) for category, props in categories.items()]
plt.legend(handles=handles, loc='lower left', fontsize='small', frameon=False, title="Wind Categories (knots)")

plt.show()




# track of 1980 storm
ds = xr.open_dataset('/home/zy2608/zy2608/9.22/IBTrACS.ALL.v04r01.nc')

ds_1980 = ds.where(ds['season'] == 1980, drop=True)

max_wind_per_storm = ds_1980['usa_wind'].max(dim='date_time')

storms_with_high_wind = max_wind_per_storm.where(max_wind_per_storm > 34, drop=True)
high_wind_storms = ds_2022.sel(storm=storms_with_high_wind['storm'])

latitudes = high_wind_storms['usa_lat']
longitudes = high_wind_storms['usa_lon']
winds = high_wind_storms['usa_wind']


longitudes = ((longitudes + 180) % 360) - 180

categories = {
    'Tropical Storm': {'min': 34, 'max': 63, 'color': 'cyan'},
    'Category 1': {'min': 64, 'max': 82, 'color': 'green'},
    'Category 2': {'min': 83, 'max': 95, 'color': 'yellow'},
    'Category 3': {'min': 96, 'max': 112, 'color': 'orange'},
    'Category 4': {'min': 113, 'max': 136, 'color': 'red'},
    'Category 5': {'min': 137, 'color': 'purple'},
}

plt.figure(figsize=(15, 10))

ax = plt.axes(projection=ccrs.Robinson())
ax.set_global()
ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN, facecolor='lightskyblue')

plt.title("Storm Tracks with Max Wind Speed > 34 in 1980")

for storm_idx in range(latitudes.sizes['storm']):
    storm_lat = latitudes.isel(storm=storm_idx).dropna('date_time')
    storm_lon = longitudes.isel(storm=storm_idx).dropna('date_time')
    max_wind = max_wind_per_storm.isel(storm=storm_idx)

    for category, props in categories.items():
        if ('min' in props and 'max' in props and props['min'] <= max_wind <= props['max']) or \
           ('min' in props and max_wind >= props['min'] and 'max' not in props):
            storm_category = category
            color = props['color']
            break

    if len(storm_lon) > 1:
        split_indices = np.where(np.abs(np.diff(storm_lon)) > 180)[0] + 1
        split_lon = np.split(storm_lon, split_indices)
        split_lat = np.split(storm_lat, split_indices)
        for lon_segment, lat_segment in zip(split_lon, split_lat):
            plt.plot(lon_segment, lat_segment, color=color, transform=ccrs.PlateCarree(), alpha=0.6)

import matplotlib.patches as mpatches
handles = [mpatches.Patch(color=props['color'], label=category) for category, props in categories.items()]
plt.legend(handles=handles, loc='lower left', fontsize='small', frameon=False, title="Wind Categories (knots)")

plt.show()

#Number of Storms per Month in 2022 (Max Wind Speed > 34)

ds = xr.open_dataset('/home/zy2608/zy2608/9.22/IBTrACS.last3years.v04r01.nc')

iso_time = pd.to_datetime(ds.iso_time.astype(str).values.flatten()).to_numpy().reshape(ds.iso_time.shape)
ds['iso_time'] = xr.DataArray(iso_time, dims=ds.iso_time.dims, coords=ds.iso_time.coords)

ds_2022 = ds.where(ds['iso_time'].dt.year == 2022, drop=True)
max_wind_per_storm = ds_2022['usa_wind'].max(dim='date_time')

storms_with_high_wind = max_wind_per_storm.where(max_wind_per_storm > 34, drop=True)
high_wind_storms = ds_2022.sel(storm=storms_with_high_wind['storm'])

months = high_wind_storms['iso_time'].dt.month

unique_storm_months_list = []
for storm in high_wind_storms['storm']:
    storm_months = months.sel(storm=storm).dropna('date_time').values
    unique_months = np.unique(storm_months)
    unique_storm_months_list.extend(unique_months)

all_unique_months = np.array(unique_storm_months_list)

monthly_counts = pd.Series(all_unique_months).value_counts().sort_index()

all_months_index = pd.Index(np.arange(1, 13), name="month")
monthly_counts_full = monthly_counts.reindex(all_months_index, fill_value=0)

plt.figure(figsize=(10, 6))
plt.bar(monthly_counts_full.index, monthly_counts_full.values, color='royalblue', edgecolor='black')
plt.xlabel('Month')
plt.ylabel('Number of Storms')
plt.title('Number of Storms per Month in 2022 (Max Wind Speed > 34)')
plt.xticks(ticks=np.arange(1, 13), labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

#Number of Storms per Month by Basin in 2022 (Max Wind Speed > 34)

ds = xr.open_dataset('/home/zy2608/zy2608/9.22/IBTrACS.last3years.v04r01.nc')
iso_time = pd.to_datetime(ds.iso_time.astype(str).values.flatten()).to_numpy().reshape(ds.iso_time.shape)
ds['iso_time'] = xr.DataArray(iso_time, dims=ds.iso_time.dims, coords=ds.iso_time.coords)

ds_2022 = ds.where(ds['iso_time'].dt.year == 2022, drop=True)

max_wind_per_storm = ds_2022['usa_wind'].max(dim='date_time')

storms_with_high_wind = max_wind_per_storm.where(max_wind_per_storm > 34, drop=True)
high_wind_storms = ds_2022.sel(storm=storms_with_high_wind['storm'])

months = high_wind_storms['iso_time'].dt.month
basins = high_wind_storms['basin']

unique_storm_months_list = []
unique_storm_basins_list = []

for storm in high_wind_storms['storm']:
    storm_months = months.sel(storm=storm).dropna('date_time').values
    storm_basins = basins.sel(storm=storm).dropna('date_time').values

    unique_months = np.unique(storm_months)
    unique_basins = np.unique(storm_basins)

    for month in unique_months:
        unique_storm_months_list.append(month)
        unique_storm_basins_list.append(unique_basins[0])

storm_data = pd.DataFrame({
    'month': unique_storm_months_list,
    'basin': unique_storm_basins_list
})

monthly_basin_counts = storm_data.groupby(['month', 'basin']).size().unstack(fill_value=0)

all_months_index = pd.Index(np.arange(1, 13), name="month")
monthly_basin_counts = monthly_basin_counts.reindex(all_months_index, fill_value=0)
monthly_basin_counts.plot(
    kind='bar',
    stacked=True,
    figsize=(12, 8),
    color=['royalblue', 'orange', 'green', 'red', 'purple', 'brown', 'pink'],
    edgecolor='black'
)

plt.xlabel('Month')
plt.ylabel('Number of Storms')
plt.title('Number of Storms per Month by Basin in 2022 (Max Wind Speed > 34)')
plt.xticks(ticks=np.arange(0, 12), labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend(title='Basin', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()



