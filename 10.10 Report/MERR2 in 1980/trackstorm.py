import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature

column_names = ['date', 'time', 'lats', 'lons', 'vs', 'pa', 'fcst_date', 'fcst_time', 'lead_time_hours']
df = pd.read_csv('convert_dataset.dat', sep='\s+', header=None, names=column_names, skiprows=1)
df['dates'] = pd.to_datetime(df['date'] + ' ' + df['time'])
df['fcst_ini_date'] = pd.to_datetime(df['fcst_date'] + ' ' + df['fcst_time'])
df = df.drop(columns=['date', 'time', 'fcst_date', 'fcst_time'])
df['lons'] = df['lons'].apply(lambda x: x if x <= 180 else x - 360)
df_filtered = df[(df['lons'] >= -180) & (df['lons'] <= 180) & (df['lats'] >= -90) & (df['lats'] <= 90)]

unique_storms = df_filtered['fcst_ini_date'].unique()
num_storms = len(unique_storms)
storm_indices = {storm_date: idx for idx, storm_date in enumerate(unique_storms)}

df_filtered['storm_idx'] = df_filtered['fcst_ini_date'].map(storm_indices)

norm = mcolors.Normalize(vmin=0, vmax=num_storms - 1)
cmap = cm.get_cmap('plasma', num_storms)  

plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_global()
ax.coastlines()
ax.add_feature(cfeature.LAND)
ax.add_feature(cfeature.OCEAN)

scatter = ax.scatter(
    df_filtered['lons'],
    df_filtered['lats'],
    c=df_filtered['storm_idx'],
    cmap=cmap,
    norm=norm,
    s=10,
    transform=ccrs.PlateCarree(),
)

cbar = plt.colorbar(scatter, ax=ax, orientation='vertical', pad=0.02, shrink=0.7)
cbar.set_label('Storm Index')

tick_locs = range(0, num_storms, max(1, num_storms // 10)) 
cbar.set_ticks(tick_locs)
cbar.set_ticklabels(tick_locs)

plt.title('Storm Tracks from 1980')
output_file = 'storm_tracks_1980.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.show()
print(f"Plot saved as {output_file}")