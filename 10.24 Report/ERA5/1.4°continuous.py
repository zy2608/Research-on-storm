import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0  
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance = R * c
    return distance

def plot_storm_tracks(df):
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS, alpha=0.5)

    grouped = df.groupby('fcst_ini_date')
    print(f"Number of unique storms: {len(grouped)}")

    for name, group in grouped:
        group = group.sort_values('dates')
        lons = group['lons'].values
        lats = group['lats'].values

        for i in range(len(lons) - 1):
            lon1 = lons[i]
            lon2 = lons[i + 1]
            lat1 = lats[i]
            lat2 = lats[i + 1]

            dist = haversine(lon1, lat1, lon2, lat2)

            if dist < 500:  #threshold
                if abs(lon2 - lon1) > 180:
                    if lon1 > lon2:
                        lon2 += 360
                    else:
                        lon1 += 360

                ax.plot(
                    [lon1, lon2],
                    [lat1, lat2],
                    color='green',  
                    linewidth=1.5,
                    transform=ccrs.PlateCarree()
                )

    plt.title('Storm Tracks')
    output_file = 'storm_tracks_green_lines.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Plot saved as {output_file}")

if __name__ == "__main__":
    data_file_path = '/home/cl4460/NeuralGCM/NeuralGCM_convert_dataset.csv'  
    try:
        column_names = ['dates', 'lats', 'lons', 'pressure', 'fcst_ini_date', 'lead_time_hours']
        df = pd.read_csv(
            data_file_path,
            sep=',',  
            header=0,  
            names=column_names,  
            on_bad_lines='skip'  
        )


        print("First few rows of data:")
        print(df.head())
        print("Data types:")
        print(df.dtypes)

        df['dates'] = pd.to_datetime(df['dates'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['fcst_ini_date'] = pd.to_datetime(df['fcst_ini_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

        if df['dates'].isnull().any() or df['fcst_ini_date'].isnull().any():
            print("Warning: Some dates could not be parsed. Please check the date format in your data file.")
            print("Rows with unparsed dates:")
            print(df[df['dates'].isnull() | df['fcst_ini_date'].isnull()])


        df['lons'] = df['lons'].apply(lambda x: x if x <= 180 else x - 360)
        df_filtered = df[
            (df['lons'] >= -180) &
            (df['lons'] <= 180) &
            (df['lats'] >= -90) &
            (df['lats'] <= 90)
        ]
        if df_filtered.empty:
            print("No valid data to plot after filtering.")
        else:
            plot_storm_tracks(df_filtered)
    except Exception as e:
        print(f"An error occurred: {e}")
