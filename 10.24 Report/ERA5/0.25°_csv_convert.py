import pandas as pd
import datetime
import re
import numpy as np

def read_format_era5(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    line_count = 0
    data_dict = {
        'dates': [],
        'lats': [],
        'lons': [],
        'pressure': [],
        'wind_speed': [],
        'fcst_ini_date': [],
        'lead_time_hours': []
    }

    while line_count < len(lines):
        line_zero = lines[line_count].strip()
        split_line = re.split(r'\s+', line_zero)

        if len(split_line) == 0 or split_line[0] != 'start':
            line_count += 1
            continue

        try:
            M = int(split_line[1])
            ini_year = int(split_line[2])
            ini_month = int(split_line[3])
            ini_day = int(split_line[4])
            ini_hour = int(split_line[5])

            fcst_ini_date_current = datetime.datetime(ini_year, ini_month, ini_day, ini_hour)
            line_count += 1

            for _ in range(M):
                if line_count >= len(lines):
                    break

                newline = lines[line_count].strip()
                split_data = re.split(r'\s+', newline)

                if len(split_data) < 11:  # 需要至少11列数据
                    print(f"Line {line_count + 1} has insufficient columns: {split_data}")
                    line_count += 1
                    continue

                try:
                    i = int(split_data[0])
                    j = int(split_data[1])
                    lon = float(split_data[2])
                    lat = float(split_data[3])
                    pressure = float(split_data[4])
                    wind_speed = float(split_data[5])
                    # 跳过 split_data[6]，值为 0.000000e+00
                    year = int(split_data[7])
                    month = int(split_data[8])
                    day = int(split_data[9])
                    hour = int(split_data[10])
                    valid_date = datetime.datetime(year, month, day, hour)
                    lead_time = int((valid_date - fcst_ini_date_current).total_seconds() / 3600)
                except Exception as e:
                    print(f"Error parsing line {line_count + 1}: {e}")
                    line_count += 1
                    continue

                data_dict['dates'].append(valid_date.strftime('%Y-%m-%d %H:%M:%S'))
                data_dict['lats'].append(lat)
                data_dict['lons'].append(lon)
                data_dict['pressure'].append(pressure)
                data_dict['wind_speed'].append(wind_speed)
                data_dict['fcst_ini_date'].append(fcst_ini_date_current.strftime('%Y-%m-%d %H:%M:%S'))
                data_dict['lead_time_hours'].append(lead_time)

                line_count += 1

        except Exception as e:
            print(f"Error processing line {line_count + 1}: {e}")
            line_count += 1
            continue

    # 检查数据完整性
    non_scalar_found = False
    for key, value in data_dict.items():
        for idx, item in enumerate(value):
            if isinstance(item, (list, np.ndarray, dict)):
                print(f"Found non-scalar in '{key}' at index {idx}: {item}")
                non_scalar_found = True
    if non_scalar_found:
        raise ValueError("Non-scalar elements exist in data_dict")

    # 检查所有列表长度是否一致
    lengths = [len(v) for v in data_dict.values()]
    if len(set(lengths)) != 1:
        raise ValueError(f"Inconsistent list lengths in data_dict: {lengths}")

    # 转换为 DataFrame
    try:
        df = pd.DataFrame(data_dict)
    except Exception as e:
        print(f"Error creating DataFrame: {e}")
        raise

    df = df.reset_index(drop=True)
    df['fcst_ini_date'] = pd.to_datetime(df['fcst_ini_date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    df['dates'] = pd.to_datetime(df['dates'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # 处理经度，使其在 -180 到 180 之间
    df['lons'] = df['lons'].apply(lambda x: x if x <= 180 else x - 360)

    # 过滤无效数据
    df_filtered = df[
        (df['lons'] >= -180) &
        (df['lons'] <= 180) &
        (df['lats'] >= -90) &
        (df['lats'] <= 90) &
        (~df['dates'].isnull()) &
        (~df['fcst_ini_date'].isnull())
    ]

    # 保存为 CSV
    output_file_path = 'ERA5_convert_dataset.csv'
    df_filtered.to_csv(output_file_path, index=False)
    print(f"Data has been saved into {output_file_path}")

if __name__ == "__main__":
    data_file_path = 'ERA5_second_trail.dat'  # 请替换为您的实际文件路径
    try:
        read_format_era5(data_file_path)
    except Exception as e:
        print(f"An error occurred: {e}")
