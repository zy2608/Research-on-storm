import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature



#USA Storm Tracks for 2022 by Wind Speed Categories
data = "IBTrACS.last3years.v04r01.nc"
ds = nc.Dataset(data)

lon = ds.variables['usa_lon'][:]  
lat = ds.variables['usa_lat'][:]  
wind = ds.variables['usa_wind'][:]  
season = ds.variables['season'][:]  

season_mask = (season == 2022)
max_wind_mask = np.nanmax(wind, axis=1) >= 34
combined_mask = season_mask & max_wind_mask

filtered_lon = lon[combined_mask, :]
filtered_lat = lat[combined_mask, :]
filtered_wind = wind[combined_mask, :]

categories = [(34, 63, 'Tropical Storm', 'cyan'),
              (64, 82, 'Category 1', 'lightgreen'),
              (83, 95, 'Category 2', 'yellow'),
              (96, 112, 'Category 3', 'orange'),
              (113, 136, 'Category 4', 'red'),
              (137, np.inf, 'Category 5', 'purple')]

fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

ax.set_extent([-150, -40, 10, 70], crs=ccrs.PlateCarree())

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.STATES, linestyle='--')
ax.add_feature(cfeature.LAND, color='lightgray')
ax.add_feature(cfeature.OCEAN, color='lightblue')

for idx in range(len(filtered_lon)):
    storm_lon = filtered_lon[idx, :]
    storm_lat = filtered_lat[idx, :]
    storm_wind = filtered_wind[idx, :]  

    valid_points = np.isfinite(storm_lon) & np.isfinite(storm_lat) & np.isfinite(storm_wind)
    storm_lon = storm_lon[valid_points]
    storm_lat = storm_lat[valid_points]
    storm_wind = storm_wind[valid_points]
    for category in categories:
        min_wind, max_wind, label, color = category
        category_mask = (storm_wind >= min_wind) & (storm_wind <= max_wind)
        ax.plot(storm_lon[category_mask], storm_lat[category_mask], color=color, lw=1, transform=ccrs.PlateCarree(), label=label)


handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))  
ax.legend(by_label.values(), by_label.keys(), loc='upper left', title="Wind Categories (knots)")

plt.title('USA Storm Tracks for 2022 by Wind Speed Categories')
plt.show()






#Number of Unique Storms per Month in 2022 (WMO_WIND >= 34)
iso_time = ds.variables['iso_time'][:]  
wmo_wind = ds.variables['wmo_wind'][:]  
sid = ds.variables['sid'][:]  

def safe_decode(value):
    return ''.join([s.decode('utf-8') for s in value]).strip()

storm_data = []

for i in range(iso_time.shape[0]):  
    storm_times = iso_time[i, :, :]  
    storm_wind = wmo_wind[i, :]  

    if np.max(storm_wind) >= 34:
        storm_times_filled = storm_times.filled('')

        storm_times_decoded = []
        for t in storm_times_filled:
            try:
                decoded_time = ''.join([char.decode('utf-8') for char in t if char != ''])
                storm_times_decoded.append(decoded_time)
            except Exception:
                continue  

        storm_times_dt = pd.to_datetime(storm_times_decoded, errors='coerce', format='%Y-%m-%d %H:%M:%S')

        valid_times_2022 = storm_times_dt[(storm_times_dt.year == 2022) & (~storm_times_dt.isna())]

        storm_id_decoded = safe_decode(sid[i])

        for time in valid_times_2022:
            storm_data.append({'storm_id': storm_id_decoded, 'date': time})

df = pd.DataFrame(storm_data)

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

df_unique_storms = df.drop_duplicates(subset=['storm_id', 'month'])

unique_storms_per_month = df_unique_storms.groupby('month').size()


plt.figure(figsize=(10, 6))
unique_storms_per_month.plot(kind='bar', color='skyblue')
plt.title('Number of Unique Storms per Month in 2022 (WMO_WIND >= 34)')
plt.xlabel('Month')
plt.ylabel('Number of Unique Storms')
plt.xticks(np.arange(1, 13, 1))
plt.yticks(np.arange(0, unique_storms_per_month.max() + 1, 1))
plt.show()




#Number of Unique Storms per Month per Basin in 2022 (Max Wind Speed ≥ 34)
basin = ds.variables['basin'][:]  
storm_data = []

for i in range(iso_time.shape[0]):
    storm_times = iso_time[i, :, :]
    storm_basin = basin[i, 0]  
    storm_winds = wmo_wind[i, :]  

    if np.max(storm_winds) >= 34:
        storm_times_filled = storm_times.filled('')
        storm_times_decoded = []
        for t in storm_times_filled:
            try:
                decoded_time = ''.join([char.decode('utf-8') for char in t if char != ''])
                storm_times_decoded.append(decoded_time)
            except Exception:
                continue  
        storm_times_dt = pd.to_datetime(storm_times_decoded, errors='coerce', format='%Y-%m-%d %H:%M:%S')
        valid_times_2022 = storm_times_dt[(storm_times_dt.year == 2022) & (~storm_times_dt.isna())]
        storm_id_decoded = safe_decode(sid[i])
        storm_basin_decoded = safe_decode(storm_basin)
        for time in valid_times_2022:
            storm_data.append({'storm_id': storm_id_decoded, 'basin': storm_basin_decoded, 'date': time})

df = pd.DataFrame(storm_data)

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

df_unique_storms = df.drop_duplicates(subset=['storm_id', 'basin', 'month'])

unique_storms_per_basin_month = df_unique_storms.groupby(['basin', 'month'])['storm_id'].nunique()

result_df = unique_storms_per_basin_month.reset_index()
print(result_df)

result_df.pivot(index='month', columns='basin', values='storm_id').plot(kind='bar', stacked=True, figsize=(10, 6))

plt.title('Number of Unique Storms per Month per Basin in 2022 (Max Wind Speed ≥ 34)')
plt.xlabel('Month')
plt.ylabel('Number of Unique Storms')
plt.xticks(rotation=0)  
plt.show()


