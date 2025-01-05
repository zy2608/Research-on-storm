import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import glob
import os

def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0  
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance = R * c
    return distance

def plot_storm_tracks(data_dir, processed_file_pattern):
    """
    Plot storm tracks from multiple datasets, each represented with a distinct color and included in the legend.
    """
    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()  
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS, alpha=0.5)

    # Define a colormap that can handle many discrete colors
    cmap = plt.get_cmap('tab20', 31)  # 'tab20' has 20 colors; using it with more bins cycles through colors
    processed_file_paths = glob.glob(os.path.join(data_dir, processed_file_pattern))
    processed_file_paths.sort()
    legend_entries = []
    for idx, processed_file in enumerate(processed_file_paths):
        df = pd.read_csv(processed_file)
        df['dates'] = pd.to_datetime(df['dates'], errors='coerce')
        df['fcst_ini_date'] = pd.to_datetime(df['fcst_ini_date'], errors='coerce')


        if df['dates'].isnull().any() or df['fcst_ini_date'].isnull().any():
            print("Warning: Unparseable dates in file {}.".format(processed_file))
            continue
        df['lons'] = df['lons'].apply(lambda x: x if x <= 180 else x - 360)
        df_filtered = df[
            (df['lons'] >= -180) &
            (df['lons'] <= 180) &
            (df['lats'] >= -90) &
            (df['lats'] <= 90)
        ]

        if df_filtered.empty:
            print("No valid data in file {}.".format(processed_file))
            continue
        grouped = df_filtered.groupby('fcst_ini_date')
        # Assign a color from the colormap to this dataset
        color = cmap(idx % cmap.N)  # Use modulo in case idx exceeds the number of colors
        base_name = os.path.basename(processed_file)
        label_name = os.path.splitext(base_name)[0]


        for name, group in grouped:
            group = group.sort_values('dates')
            lons = group['lons'].values
            lats = group['lats'].values
            for i in range(len(lons) - 1):
                lon1, lon2 = lons[i], lons[i + 1]
                lat1, lat2 = lats[i], lats[i + 1]
                dist = haversine(lon1, lat1, lon2, lat2)
                if dist < 500:  
                    if abs(lon2 - lon1) > 180:
                        if lon1 > lon2:
                            lon2 += 360
                        else:
                            lon1 += 360
                    ax.plot(
                        [lon1, lon2],
                        [lat1, lat2],
                        color=color,
                        linewidth=1.5,
                        transform=ccrs.PlateCarree()
                    )
        legend_entries.append((plt.Line2D([0], [0], color=color, lw=2), label_name))
    legend_entries = sorted(legend_entries, key=lambda x: x[1]) 
    legend_handles, legend_labels = zip(*legend_entries)
    ax.legend(legend_handles, legend_labels, loc='lower left', fontsize='small', ncol=4, bbox_to_anchor=(0, -0.2))

    plt.title('Storm Tracks from Multiple Datasets')
    output_file = 'storm_tracks_all_files.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print("Plot saved as {}".format(output_file))

if __name__ == "__main__":
    data_dir = '/home/cl4460/onemonth_NeuralGCM'  
    processed_file_pattern = '*_processed.csv'  
    plot_storm_tracks(data_dir, processed_file_pattern)
