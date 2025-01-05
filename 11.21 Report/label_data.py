import pandas as pd
import datetime
import re
import numpy as np
import glob
import os

def read_format_(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    line_count = 0
    data_dict = {
        'dates': [],
        'lats': [],
        'lons': [],
        'wind_speed': [],
        'pa': [],
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

                if len(split_data) < 11:
                    line_count += 1
                    continue

                try:
                    i = int(split_data[0])
                    j = int(split_data[1])
                    lon = float(split_data[2])
                    lat = float(split_data[3])
                    pressure = float(split_data[4])
                    V_speed = float(split_data[5])
                    year = int(split_data[7])
                    month = int(split_data[8])
                    day = int(split_data[9])
                    hour = int(split_data[10])
                    valid_date = datetime.datetime(year, month, day, hour)
                    lead_time = int((valid_date - fcst_ini_date_current).total_seconds() / 3600)
                except Exception as e:
                    print("Error parsing line {}: {}".format(line_count, e))
                    line_count += 1
                    continue

                data_dict['dates'].append(valid_date.strftime('%Y-%m-%d %H:%M:%S'))
                data_dict['lats'].append(lat)
                data_dict['lons'].append(lon)
                data_dict['wind_speed'].append(V_speed)
                data_dict['pa'].append(pressure)
                data_dict['fcst_ini_date'].append(fcst_ini_date_current.strftime('%Y-%m-%d %H:%M:%S'))
                data_dict['lead_time_hours'].append(lead_time)

                line_count += 1

        except Exception as e:
            print("Error processing line {}: {}".format(line_count, e))
            line_count += 1
            continue

    lengths = [len(v) for v in data_dict.values()]
    if len(set(lengths)) != 1:
        raise ValueError("Inconsistent list lengths in data_dict: {}".format(lengths))

    for key, value in data_dict.items():
        data_dict[key] = [item.item() if isinstance(item, np.ndarray) else item for item in value]

    try:
        df = pd.DataFrame(data_dict)
    except Exception as e:
        print("Error creating DataFrame: {}".format(e))
        raise

    df = df.reset_index(drop=True)
    df['fcst_ini_date'] = df['fcst_ini_date'].astype(str)

    return df

if __name__ == "__main__":
    import sys
    data_dir = '/home/cl4460/onemonth_NeuralGCM'
    file_pattern = 'NeuralGCM_2020-07-*.nc.dat'
    full_pattern = os.path.join(data_dir, file_pattern)
    file_list = glob.glob(full_pattern)
    file_list.sort()
    for data_file_path in file_list:
        try:
            df = read_format_(data_file_path)
            base_name = os.path.basename(data_file_path)
            output_file_name = os.path.splitext(base_name)[0] + '_processed.csv'
            output_file_path = os.path.join(data_dir, output_file_name)
            df.to_csv(output_file_path, index=False)
            print("The file was saved to {}".format(output_file_path))
        except Exception as e:
            print("An error occurred while processing file {}: {}".format(data_file_path, e))
