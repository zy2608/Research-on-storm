import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature


df = pd.read_csv('convert_dataset.dat', sep='\s+', engine='python')
df['dates'] = pd.to_datetime(df['dates'], errors='coerce')
df['fcst_ini_date'] = pd.to_datetime(df['fcst_ini_date'], errors='coerce')


if df['fcst_ini_date'].isnull().any():
    print("Warning: Some 'fcst_ini_date' entries could not be parsed and will be dropped.")
    df = df.dropna(subset=['fcst_ini_date'])


df['lons'] = df['lons'].apply(lambda x: x if x <= 180 else x - 360)
# get the tracks of storms
unique_storms = df['fcst_ini_date'].unique()


plt.figure(figsize=(12, 8))
ax_main = plt.axes(projection=ccrs.PlateCarree())
ax_main.set_global()


ax_main.coastlines()
gridlines = ax_main.gridlines(draw_labels=True)
ax_main.add_feature(cfeature.LAND)
ax_main.add_feature(cfeature.OCEAN)


colors = cm.rainbow(np.linspace(0, 1, len(unique_storms)))
for idx, storm_date in enumerate(unique_storms):
    storm_data = df[df['fcst_ini_date'] == storm_date]
    ax_main.plot(
        storm_data['lons'],
        storm_data['lats'],
        marker='o',
        color=colors[idx % len(colors)],
        transform=ccrs.PlateCarree()
    )


plt.title('Storm Tracks from 1980')
plt.legend(loc='upper right')
output_file = 'storm_tracks_1980.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.show()