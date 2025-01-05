import pandas as pd
import datetime
import re
import numpy as np

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
                    print(f"Error parsing line {line_count}: {e}")
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
            print(f"Error processing line {line_count}: {e}")
            line_count += 1
            continue

    print("Data Dictionary Contents:")
    for key, value in data_dict.items():
        print(f"{key}: Type={type(value)}, Length={len(value)}")
        if len(value) > 0:
            print(f"First 5 elements of {key}: {value[:5]}")
        else:
            print(f"{key} is empty.")

    non_scalar_found = False
    for key, value in data_dict.items():
        for idx, item in enumerate(value):
            if isinstance(item, (list, np.ndarray, dict)):
                print(f"Found non-scalar in '{key}' at index {idx}: {item}")
                non_scalar_found = True
    if non_scalar_found:
        raise ValueError("Non-scalar elements exist in data_dict")

    lengths = [len(v) for v in data_dict.values()]
    if len(set(lengths)) != 1:
        raise ValueError(f"Inconsistent list lengths in data_dict: {lengths}")

    for key, value in data_dict.items():
        data_dict[key] = [item.item() if isinstance(item, np.ndarray) else item for item in value]

    try:
        df = pd.DataFrame(data_dict)
    except Exception as e:
        print(f"Error creating DataFrame: {e}")
        raise

    df = df.reset_index(drop=True)
    df['fcst_ini_date'] = df['fcst_ini_date'].astype(str)

    return df

if __name__ == "__main__":
    data_file_path = '/home/cl4460/ERA5_2022/ERA5_second_trail.dat'
    try:
        df = read_format_(data_file_path)
        output_file_path = 'convert_dataset.dat'
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(df.to_string(index=False, header=True))
        print(f"Data has been saved into {output_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")