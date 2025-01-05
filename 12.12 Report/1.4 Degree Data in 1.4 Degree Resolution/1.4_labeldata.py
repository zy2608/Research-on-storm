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
    storm_id = 1  # Initialize storm ID

    data_dict = {
        'storm_id': [],  # Add storm ID column
        'dates': [],
        'lats': [],
        'lons': [],
        'wind_speed': [],
        'pa': [],
        'storm_start_time': [],  # Rename column
        'time_since_start_hours': []  # Rename column
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

            storm_start_time = datetime.datetime(ini_year, ini_month, ini_day, ini_hour)
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
                    time_since_start = int((valid_date - storm_start_time).total_seconds() / 3600)
                except Exception as e:
                    print(f"Error parsing line {line_count} in {filename}: {e}")
                    line_count += 1
                    continue

                # Add storm ID and other data to dictionary
                data_dict['storm_id'].append(storm_id)
                data_dict['dates'].append(valid_date.strftime('%Y-%m-%d %H:%M:%S'))
                data_dict['lats'].append(lat)
                data_dict['lons'].append(lon)
                data_dict['wind_speed'].append(V_speed)
                data_dict['pa'].append(pressure)
                data_dict['storm_start_time'].append(storm_start_time.strftime('%Y-%m-%d %H:%M:%S'))
                data_dict['time_since_start_hours'].append(time_since_start)

                line_count += 1

            storm_id += 1  # Increment storm ID after processing each storm

        except Exception as e:
            print(f"Error processing line {line_count} in {filename}: {e}")
            line_count += 1
            continue

    # Check data consistency
    lengths = [len(v) for v in data_dict.values()]
    if len(set(lengths)) != 1:
        raise ValueError(f"Inconsistent list lengths in data_dict for {filename}: {lengths}")

    # Handle potential numpy arrays
    for key, value in data_dict.items():
        data_dict[key] = [item.item() if isinstance(item, np.ndarray) else item for item in value]

    try:
        df = pd.DataFrame(data_dict)
    except Exception as e:
        print(f"Error creating DataFrame for {filename}: {e}")
        raise

    df = df.reset_index(drop=True)
    df['storm_start_time'] = df['storm_start_time'].astype(str)

    return df

if __name__ == "__main__":
    import sys
    import argparse

    # Use argparse for more flexible input and output directory specification
    parser = argparse.ArgumentParser(description="Process .dat files and convert them to .csv")
    parser.add_argument('--input_dir', type=str, default='/home/cl4460/NeuralGCM_1.4/1.4_resolution_output_files',
                        help='Directory containing input .dat files')
    parser.add_argument('--output_dir', type=str, default='/home/cl4460/NeuralGCM_1.4/1.4_resolution_processed_results',
                        help='Directory to save processed .csv files')
    args = parser.parse_args()

    data_dir = args.input_dir
    output_base_dir = args.output_dir

    # Create base output directory (if it does not exist)
    os.makedirs(output_base_dir, exist_ok=True)

    # File pattern: Match all .dat files
    file_pattern = 'NeuralGCM_*.dat'  # Ensure matching all .dat files
    full_pattern = os.path.join(data_dir, file_pattern)
    file_list = glob.glob(full_pattern)
    file_list.sort()

    # Print file list for debugging
    print(f"Found {len(file_list)} files to process.")
    for f in file_list:
        print(f"Processing file: {f}")

    for data_file_path in file_list:
        try:
            df = read_format_(data_file_path)
            base_name = os.path.basename(data_file_path)
            # Remove .dat extension
            name_without_ext = os.path.splitext(base_name)[0]
            # Replace spaces in file name with underscores to avoid issues
            name_without_ext_safe = name_without_ext.replace(' ', '_')
            # Create output file name
            output_file_name = f"{name_without_ext_safe}_processed.csv"
            output_file_path = os.path.join(output_base_dir, output_file_name)
            # Save DataFrame as CSV
            df.to_csv(output_file_path, index=False)
            print(f"The file was saved to {output_file_path}")
        except Exception as e:
            print(f"An error occurred while processing file {data_file_path}: {e}")
