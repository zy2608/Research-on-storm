import os
import numpy as np
import xarray as xr


# **Step 2: Open the NetCDF file**
input_path = '/home/cl4460/NeuralGCM/predictions_output_onemonth_TE_ready.nc'

try:
    ds = xr.open_dataset(input_path)
    print(f"Successfully opened {input_path}\n")
except FileNotFoundError:
    print(f"File not found: {input_path}")
    exit(1)
except Exception as e:
    print(f"An error occurred while opening the file: {e}")
    exit(1)

# **Step 3: Display basic information about the dataset**
print("=== Dataset Summary ===")
print(ds)
print("\n")

# **Step 4: List all variables and their attributes**
print("=== Variables and Attributes ===")
for var in ds.data_vars:
    print(f"Variable: {var}")
    print(ds[var].attrs)
    print("----------------------------")
print("\n")

# **Step 5: Display basic statistics for each variable**
print("=== Variables' Basic Statistics ===")
for var in ds.data_vars:
    data = ds[var]
    if np.issubdtype(data.dtype, np.number):
        print(f"Variable: {var}")
        print(f"  - Min: {data.min().values}")
        print(f"  - Max: {data.max().values}")
        print(f"  - Mean: {data.mean().values}")
        print(f"  - Std: {data.std().values}")
    else:
        print(f"Variable: {var} is not numerical and skipped.")
    print("----------------------------")
print("\n")

# **Step 6: Provide sample data for each variable**
print("=== Variables' Sample Data ===")
for var in ds.data_vars:
    data = ds[var]
    print(f"Variable: {var}")
    try:
        # Show the first few data points to avoid excessive output
        sample = data.isel(time=0).isel(lat=slice(0,5)).isel(lon=slice(0,5))
        print(sample)
    except Exception as e:
        print(f"  - Could not display sample data: {e}")
    print("----------------------------")
print("\n")

# **Step 7: List all dimensions and coordinates**
print("=== Dimensions and Coordinates ===")
print(ds.dims)
print(ds.coords)
print("\n")

# **Step 8: Close the dataset**
ds.close()
