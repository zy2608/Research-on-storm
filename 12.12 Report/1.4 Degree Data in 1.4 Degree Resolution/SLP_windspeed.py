import os
import pandas as pd
import matplotlib.pyplot as plt

folder_path = "/home/zy2608/TE_ready_07/0.7_resolution_processed_results/"

results = []

for file_name in os.listdir(folder_path):
    if file_name.endswith(".csv"):
        file_path = os.path.join(folder_path, file_name)
        
        data = pd.read_csv(file_path)
        
        if {'wind_speed', 'pa', 'storm_id'}.issubset(data.columns):
            grouped = data.groupby('storm_id').agg({
                'wind_speed': 'max',
                'pa': 'min'
            }).reset_index()
            
            for _, row in grouped.iterrows():
                results.append({
                    'file': file_name,
                    'storm_id': row['storm_id'],
                    'max_wind_speed': row['wind_speed'],
                    'min_pa': row['pa']
                })
        else:
            print(f"Skipping {file_name} as it does not contain the required columns.")


max_wind_speeds = [r['max_wind_speed'] for r in results]
min_pas = [r['min_pa'] for r in results]

plt.figure(figsize=(10, 6))
plt.scatter(max_wind_speeds, min_pas, color='blue', alpha=0.7)
plt.title('Maximum Wind Speed vs Minimum Pressure by Storm ID with 0.7 degree 1.4 resolution', fontsize=14)
plt.xlabel('Maximum Wind Speed', fontsize=12)
plt.ylabel('Minimum Pressure (pa)', fontsize=12)
plt.grid(True)
plt.show()
