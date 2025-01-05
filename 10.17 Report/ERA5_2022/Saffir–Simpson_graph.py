import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

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

    labels = ['TD', 'TS', 'Category 1', 'Category 2', 'Category 3', 'Category 4', 'Category 5']
    missing_categories = set(labels) - set(df['category'].dropna().unique())
    if missing_categories:
        print(f"\n Warning: The following categories are missing from the data: {missing_categories}")

    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS, alpha=0.5)


    for category in labels:
        category_data = df[df['category'] == category]
        if not category_data.empty:
            ax.scatter(
                category_data['lons'],
                category_data['lats'],
                label=category,
                color=category_colors[category],
                s=10,
                transform=ccrs.PlateCarree(),
                alpha=0.6,  
            )
    plt.legend(title='Saffir-Simpson Category', loc='lower left', fontsize='medium', markerscale=2)
    plt.title('Storm Tracks Based on Saffir-Simpson Scale', fontsize=16)
    output_image = 'storm_tracks_Saffir_Simpson.png'
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Plot saved as {output_image}")

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


        print("DataFrame column name:", df.columns.tolist())
        print(df.head())
        df['dates'] = df['date'] + ' ' + df['time']
        df['fcst_ini_date'] = df['fcst_ini_date_date'] + ' ' + df['fcst_ini_date_time']
        df = df.drop(columns=['date', 'time', 'fcst_ini_date_date', 'fcst_ini_date_time'])

        if 'lons' not in df.columns:
            print("DataFrame column name:", df.columns.tolist())
            raise KeyError("'lons'")


        df['lons'] = pd.to_numeric(df['lons'], errors='coerce')
        df['lats'] = pd.to_numeric(df['lats'], errors='coerce')
        df['wind_speed'] = pd.to_numeric(df['wind_speed'], errors='coerce')

        print(df.isnull().sum())
        df['lons'] = df['lons'].apply(lambda x: x if x <= 180 else x - 360)
        df_filtered = df[
            (df['lons'] >= -180) &
            (df['lons'] <= 180) &
            (df['lats'] >= -90) &
            (df['lats'] <= 90)
        ]


        df_filtered = df_filtered.dropna(subset=['lons', 'lats', 'wind_speed'])
        df_filtered = categorize_wind_speed(df_filtered)
        print(df_filtered[['wind_speed', 'category']].head(10))
        plot_storm_tracks(df_filtered)
    except Exception as e:
        print(f"An error occurred: {e}")
