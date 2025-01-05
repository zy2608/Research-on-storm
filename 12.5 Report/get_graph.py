import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import glob
import os

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the surface distance between two points using the haversine formula.
    Input longitude and latitude (in decimal degrees), output distance (in kilometers).
    """
    R = 6371.0  # Earth's radius in kilometers
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    distance = R * c
    return distance

def plot_all_storm_tracks(data_dir, processed_file_pattern):
    """
    Traverse all CSV files in the specified directory and plot all storm tracks.
    Each storm in a file is distinguished by a different color, and all storms are
    combined into a single map.
    
    Parameters:
    - data_dir: Path to the directory containing input CSV files.
    - processed_file_pattern: File pattern to match CSV files (e.g., '*_processed.csv').
    """
    plt.figure(figsize=(20, 10))
    # Set projection to PlateCarree with a central longitude of 180°
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS, alpha=0.5)
    ax.gridlines(draw_labels=True)

    # Define a list of colors to distinguish storms (extend if necessary)
    storm_colors = ['red', 'yellow', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'brown', 'black']
    num_colors = len(storm_colors)

    # Get all matching CSV file paths
    processed_file_paths = glob.glob(os.path.join(data_dir, processed_file_pattern))
    processed_file_paths.sort()

    total_storms = 0  # To count the total number of storms

    for file_idx, processed_file in enumerate(processed_file_paths):
        df = pd.read_csv(processed_file)
        df['dates'] = pd.to_datetime(df['dates'], errors='coerce')
        df['storm_start_time'] = pd.to_datetime(df['storm_start_time'], errors='coerce')

        # Check if date parsing was successful
        if df['dates'].isnull().any() or df['storm_start_time'].isnull().any():
            print(f"Warning: File {processed_file} contains unparseable dates. Skipping this file.")
            continue

        # Adjust longitudes to the range [0, 360)
        df['lons'] = df['lons'] % 360

        # Filter valid longitude and latitude data
        df_filtered = df[
            (df['lons'] >= 0) &
            (df['lons'] < 360) &
            (df['lats'] >= -90) &
            (df['lats'] <= 90)
        ]

        if df_filtered.empty:
            print(f"Warning: File {processed_file} contains no valid data. Skipping this file.")
            continue

        # Group by storm ID
        grouped = df_filtered.groupby('storm_id')
        num_storms_in_file = len(grouped)
        total_storms += num_storms_in_file

        for storm_idx, (name, group) in enumerate(grouped):
            group = group.sort_values('dates')
            lons = group['lons'].values
            lats = group['lats'].values

            # Handle longitude jumps and split tracks
            lons, lats = split_track_by_dateline(lons, lats)

            # Assign a color for each storm, cycling through the color list
            color = storm_colors[storm_idx % num_colors]

            # Plot the track
            for lon_seg, lat_seg in zip(lons, lats):
                ax.plot(
                    lon_seg,
                    lat_seg,
                    color=color,
                    linewidth=1.0,
                    alpha=0.6,  # Set transparency to avoid excessive overlap
                    transform=ccrs.PlateCarree(),
                    label=f"{os.path.basename(processed_file)} Storm {storm_idx + 1}" if storm_idx < 10 else None  # Limit legend entries
                )

    # Create a custom legend (only show the first 10 colors)
    import matplotlib.patches as mpatches
    legend_handles = []
    unique_colors = storm_colors  # List of colors
    for color in unique_colors:
        handle = mpatches.Patch(color=color, label=color)
        legend_handles.append(handle)
    ax.legend(handles=legend_handles, loc='lower left', fontsize='small', ncol=2, bbox_to_anchor=(0, -0.2))

    plt.title(f'Global storm tracks for 2020 (Total number of storms: {total_storms})')
    output_file = 'global_storm_tracks_2020.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Image saved as {output_file}")
    print(f"Total number of storms: {total_storms}")

def split_track_by_dateline(lons, lats):
    """
    Handle longitude crossings of the International Date Line.
    Split tracks into segments that do not cross the dateline to
    avoid lines spanning the entire map.

    Parameters:
    - lons: Array of longitudes (already adjusted to the [0, 360) range).
    - lats: Array of latitudes.

    Returns:
    - lons_segments: List of longitude segments, each segment as an array.
    - lats_segments: List of latitude segments corresponding to longitude segments.
    """
    lons_segments = []
    lats_segments = []
    lon_segment = [lons[0]]
    lat_segment = [lats[0]]
    for i in range(1, len(lons)):
        lon_current = lons[i]
        lon_prev = lons[i - 1]
        # Calculate longitude difference, considering 360-degree periodicity
        delta_lon = abs(lon_current - lon_prev)
        if delta_lon > 180:
            # Split the track
            lons_segments.append(np.array(lon_segment))
            lats_segments.append(np.array(lat_segment))
            lon_segment = [lon_current]
            lat_segment = [lats[i]]
        else:
            lon_segment.append(lon_current)
            lat_segment.append(lats[i])
    # Add the last segment
    lons_segments.append(np.array(lon_segment))
    lats_segments.append(np.array(lat_segment))
    return lons_segments, lats_segments

if __name__ == "__main__":
    # Set input and output directories
    data_dir = '/home/cl4460/NeuralGCM_1.4/processed_results'  
    processed_file_pattern = '*_processed.csv'  
    plot_all_storm_tracks(data_dir, processed_file_pattern)
