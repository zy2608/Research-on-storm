import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points on the Earth surface.
    Input coordinates must be in decimal degrees.
    Returns distance in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance = R * c
    return distance

def plot_storm_tracks(df1, df2):
    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS, alpha=0.5)

    # Plot the storm track for the first dataset (green lines)
    if not df1.empty:
        grouped1 = df1.groupby('fcst_ini_date')
        print(f"Number of unique storms in Dataset 1: {len(grouped1)}")

        for name, group in grouped1:
            group = group.sort_values('dates')
            lons = group['lons'].values
            lats = group['lats'].values

            for i in range(len(lons) - 1):
                lon1 = lons[i]
                lon2 = lons[i + 1]
                lat1 = lats[i]
                lat2 = lats[i + 1]

                dist = haversine(lon1, lat1, lon2, lat2)

                if dist < 1000:  
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

    # Plot storm tracks for the second dataset (black scatter)
    if not df2.empty:
        grouped2 = df2.groupby('fcst_ini_date')
        print(f"Number of unique storms in Dataset 2: {len(grouped2)}")

        for name, group in grouped2:
            lons = group['lons'].values
            lats = group['lats'].values

            ax.scatter(
                lons,
                lats,
                color='black',
                s=10,
                transform=ccrs.PlateCarree()
            )

    plt.title('Combined Storm Tracks from Two Datasets', fontsize=16)
    output_file = 'combined_storm_tracks.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Combined plot saved as {output_file}")

if __name__ == "__main__":
    try:
        # Read the first dataset (1.4°)
        data_file_path1 = '/home/cl4460/NeuralGCM/NeuralGCM_convert_dataset.csv' 
        column_names1 = ['dates', 'lats', 'lons', 'pressure', 'fcst_ini_date', 'lead_time_hours']
        df1 = pd.read_csv(
            data_file_path1,
            sep=',',  
            header=0,  
            names=column_names1,  
            on_bad_lines='skip' 
        )
        print("First few rows of Dataset 1:")
        print(df1.head())

        # Make sure 'dates' and 'fcst_ini_date' are datetime types
        df1['dates'] = pd.to_datetime(df1['dates'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df1['fcst_ini_date'] = pd.to_datetime(df1['fcst_ini_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df1['lons'] = df1['lons'].apply(lambda x: x if x <= 180 else x - 360)
        df1_filtered = df1[
            (df1['lons'] >= -180) &
            (df1['lons'] <= 180) &
            (df1['lats'] >= -90) &
            (df1['lats'] <= 90)
        ]

        # Read the second dataset (0.25°)
        data_file_path2 = '/home/cl4460/NeuralGCM/ERA5_convert_dataset.csv' 
        column_names2 = ['dates', 'lats', 'lons', 'wind_speed', 'pa', 'fcst_ini_date', 'lead_time_hours']
        df2 = pd.read_csv(
            data_file_path2,
            sep=',',  
            header=0,  
            names=column_names2, 
            on_bad_lines='skip'  
        )
        print("First few rows of Dataset 2:")
        print(df2.head())

  
        df2['dates'] = pd.to_datetime(df2['dates'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df2['fcst_ini_date'] = pd.to_datetime(df2['fcst_ini_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df2['lons'] = df2['lons'].apply(lambda x: x if x <= 180 else x - 360)
        df2_filtered = df2[
            (df2['lons'] >= -180) &
            (df2['lons'] <= 180) &
            (df2['lats'] >= -90) &
            (df2['lats'] <= 90)
        ]
        if df1_filtered.empty and df2_filtered.empty:
            print("No valid data to plot after filtering for both datasets.")
        else:
            plot_storm_tracks(df1_filtered, df2_filtered)
    except Exception as e:
        print(f"An error occurred: {e}")
