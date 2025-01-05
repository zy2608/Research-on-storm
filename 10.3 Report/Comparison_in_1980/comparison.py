import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.patches as mpatches


ds_ibtracs = xr.open_dataset('/home/zy2608/zy2608/9.22/IBTrACS.ALL.v04r01.nc')
ds_1980 = ds_ibtracs.where(ds_ibtracs['season'] == 1980, drop=True)
max_wind_per_storm = ds_1980['usa_wind'].max(dim='date_time')
storms_with_high_wind = max_wind_per_storm.where(max_wind_per_storm > 34, drop=True)
high_wind_storms = ds_1980.sel(storm=storms_with_high_wind['storm'])


latitudes_ibtracs = high_wind_storms['usa_lat']
longitudes_ibtracs = high_wind_storms['usa_lon']
winds_ibtracs = high_wind_storms['usa_wind']
longitudes_ibtracs = ((longitudes_ibtracs + 180) % 360) - 180


categories = {
    'Tropical Storm': {'min': 34, 'max': 63, 'color': 'cyan'},
    'Category 1': {'min': 64, 'max': 82, 'color': 'green'},
    'Category 2': {'min': 83, 'max': 95, 'color': 'yellow'},
    'Category 3': {'min': 96, 'max': 112, 'color': 'orange'},
    'Category 4': {'min': 113, 'max': 136, 'color': 'red'},
    'Category 5': {'min': 137, 'color': 'purple'},
}


column_names = ['date', 'time', 'lats', 'lons', 'vs', 'pa', 'fcst_date', 'fcst_time', 'lead_time_hours']
df_te = pd.read_csv('/home/cl4460/TE_whole_year/convert_dataset.dat', sep='\s+', header=None, names=column_names, skiprows=1)


df_te['dates'] = pd.to_datetime(df_te['date'] + ' ' + df_te['time'])
df_te['fcst_ini_date'] = pd.to_datetime(df_te['fcst_date'] + ' ' + df_te['fcst_time'])
df_te = df_te.drop(columns=['date', 'time', 'fcst_date', 'fcst_time'])
df_te['lons'] = df_te['lons'].apply(lambda x: x if x <= 180 else x - 360)


df_filtered_te = df_te[(df_te['lons'] >= -180) & (df_te['lons'] <= 180) &
                       (df_te['lats'] >= -90) & (df_te['lats'] <= 90)]


fig, axes = plt.subplots(nrows=2, figsize=(15, 20), subplot_kw={'projection': ccrs.Robinson()})


ax1 = axes[0]
ax1.set_global()
ax1.coastlines()
ax1.add_feature(cfeature.BORDERS, linestyle=':')
ax1.add_feature(cfeature.LAND, facecolor='lightgray')
ax1.add_feature(cfeature.OCEAN, facecolor='lightskyblue')
ax1.set_title("IBTrACS Storm Tracks with Max Wind Speed > 34 in 1980")

for storm_idx in range(latitudes_ibtracs.sizes['storm']):
    storm_lat = latitudes_ibtracs.isel(storm=storm_idx).dropna('date_time')
    storm_lon = longitudes_ibtracs.isel(storm=storm_idx).dropna('date_time')
    max_wind = max_wind_per_storm.isel(storm=storm_idx)


    for category, props in categories.items():
        if ('min' in props and 'max' in props and props['min'] <= max_wind <= props['max']) or \
           ('min' in props and max_wind >= props['min'] and 'max' not in props):
            color = props['color']
            break

    if len(storm_lon) > 1:
        split_indices = np.where(np.abs(np.diff(storm_lon)) > 180)[0] + 1
        split_lon = np.split(storm_lon, split_indices)
        split_lat = np.split(storm_lat, split_indices)
        for lon_segment, lat_segment in zip(split_lon, split_lat):
            ax1.plot(lon_segment, lat_segment, color=color, transform=ccrs.PlateCarree(), alpha=0.6)


handles = [mpatches.Patch(color=props['color'], label=category) for category, props in categories.items()]
ax1.legend(handles=handles, loc='lower left', fontsize='small', frameon=False, title="Wind Categories (knots)")


ax2 = axes[1]
ax2.set_global()
ax2.coastlines()
ax2.add_feature(cfeature.BORDERS, linestyle=':')
ax2.add_feature(cfeature.LAND, facecolor='lightgray')
ax2.add_feature(cfeature.OCEAN, facecolor='lightskyblue')
ax2.set_title('TempestExtremes Storm Tracks from 1980')


unique_storms = df_filtered_te['fcst_ini_date'].unique()
num_storms = len(unique_storms)
norm = mcolors.Normalize(vmin=0, vmax=num_storms - 1)
cmap = cm.plasma


for idx, storm_date in enumerate(unique_storms):
    storm_data = df_filtered_te[df_filtered_te['fcst_ini_date'] == storm_date]
    color = cmap(norm(idx))
    ax2.plot(
        storm_data['lons'],
        storm_data['lats'],
        color=color,
        linewidth=1,
        transform=ccrs.PlateCarree(),
        alpha=0.6,
    )


sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax2, orientation='vertical', pad=0.02, shrink=0.7)
cbar.set_label('Storm Index')


plt.tight_layout()


output_file = 'combined_storm_tracks_1980.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Plot saved as {output_file}")
plt.show()
