import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


def haversine(lon1, lat1, lon2, lat2):  #Calculate the distance between two latitude and longitude points in kilometers
    R = 6371.0  # The radius of the earth, in kilometers
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def categorize_wind_speed(df):
    bins = [-np.inf, 17, 32, 42, 49, 58, 70, np.inf]
    labels = ['TD', 'TS', 'Category 1', 'Category 2', 'Category 3', 'Category 4', 'Category 5']
    df['category'] = pd.cut(df['wind_speed'], bins=bins, labels=labels, right=True)
    return df

def plot_storm_tracks(df):
    category_colors = {
        'TD': 'blue',
        'TS': 'cyan',
        'Category 1': 'green',
        'Category 2': 'yellow',
        'Category 3': 'orange',
        'Category 4': 'red',
        'Category 5': 'purple',
    }

    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS, alpha=0.5)


    grouped = df.groupby('fcst_ini_date')
    for name, group in grouped:
        group = group.sort_values('dates')

        lons = group['lons'].values
        lats = group['lats'].values
        categories = group['category'].values


        for i in range(len(lons) - 1):
            dist = haversine(lons[i], lats[i], lons[i + 1], lats[i + 1])
            if dist < 500: 
                # Solve the problem of crossing 180 degrees longitude
                lon_diff = abs(lons[i] - lons[i + 1])
                if lon_diff > 180:
                    lons[i + 1] = lons[i + 1] - 360 if lons[i + 1] > 0 else lons[i + 1] + 360
                
                color = category_colors.get(categories[i], 'black')
                ax.plot(
                    [lons[i], lons[i + 1]],
                    [lats[i], lats[i + 1]],
                    color=color,
                    linewidth=1.5,
                    transform=ccrs.PlateCarree(),
                    alpha=0.7,
                )
    labels = ['TD', 'TS', 'Category 1', 'Category 2', 'Category 3', 'Category 4', 'Category 5']
    legend_elements = [plt.Line2D([0], [0], color=category_colors[label], lw=2, label=label) for label in labels]
    plt.legend(handles=legend_elements, title='Saffir-Simpson Category', loc='lower left', fontsize='medium')

    plt.title('Storm Tracks Based on Saffir-Simpson Scale', fontsize=16)
    output_image = 'storm_tracks_Saffir_Simpson_lines_corrected.png'
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    data_file_path = '/home/cl4460/ERA5_2022/convert_dataset.dat'  
    try:
        column_names = ['date', 'time', 'lats', 'lons', 'wind_speed', 'pa', 'fcst_ini_date_date', 'fcst_ini_date_time', 'lead_time_hours']
        df = pd.read_csv(
            data_file_path,
            sep='\s+',            
            header=None,         
            names=column_names,  
            on_bad_lines='skip'  
        )

        df['dates'] = df['date'] + ' ' + df['time']
        df['fcst_ini_date'] = df['fcst_ini_date_date'] + ' ' + df['fcst_ini_date_time']
        df = df.drop(columns=['date', 'time', 'fcst_ini_date_date', 'fcst_ini_date_time'])

        df['lons'] = pd.to_numeric(df['lons'], errors='coerce')
        df['lats'] = pd.to_numeric(df['lats'], errors='coerce')
        df['wind_speed'] = pd.to_numeric(df['wind_speed'], errors='coerce')

        df['lons'] = df['lons'].apply(lambda x: x if x <= 180 else x - 360)
        df_filtered = df[
            (df['lons'] >= -180) &
            (df['lons'] <= 180) &
            (df['lats'] >= -90) &
            (df['lats'] <= 90)
        ]

        df_filtered = df_filtered.dropna(subset=['lons', 'lats', 'wind_speed', 'dates', 'fcst_ini_date'])
        df_filtered = categorize_wind_speed(df_filtered)
        df_filtered['dates'] = pd.to_datetime(df_filtered['dates'], errors='coerce')
        df_filtered['fcst_ini_date'] = pd.to_datetime(df_filtered['fcst_ini_date'], errors='coerce')

        plot_storm_tracks(df_filtered)
    except Exception as e:
        print(f"An error occurred: {e}")
