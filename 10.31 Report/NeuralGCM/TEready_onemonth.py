import os
import numpy as np
import xarray as xr
import pandas as pd

# **Step 1: Set environment variables**
os.environ['PROJ_LIB'] = '/home/cl4460/proj_data'
os.environ['PROJ_DATA'] = '/home/cl4460/proj_data'
os.environ['PROJ_NETWORK'] = 'ON'

from pyproj import datadir
datadir.set_data_dir('/home/cl4460/proj_data')

# **Step 2: Open the original NeuralGCM data**
input_path = '/data0/cl4460/predictions_output_onemonth_updated.nc'
ds = xr.open_dataset(input_path)

# **Check original time variable**
print("Original time variable information:")
print(ds['time'])
print("Time values:")
print(ds['time'].values)
print("Time attributes:")
print(ds['time'].attrs)

# **Step 3: Select NeuralGCM model data**
# Assuming model=1 corresponds to NeuralGCM
model_index = 1
if 'model' in ds.dims:
    ds = ds.isel(model=model_index)
    ds = ds.drop_vars('model')
else:
    print("Dimension 'model' does not exist, skipping this step.")

# **Step 4: Process time dimension**

# Set time variable units and reference time
ds['time'].attrs['units'] = 'hours since 2020-07-01 00:00:00'
ds['time'].attrs['calendar'] = 'proleptic_gregorian'

# Decode time variable using xarray
ds = xr.decode_cf(ds)

# Verify decoded time variable
print("Decoded time variable:")
print(ds['time'].values)

# Define new reference time as numpy.datetime64 type
time_origin = np.datetime64('1970-01-01T00:00:00')

# Calculate time difference (in hours)
ds['time'] = (ds['time'].values - time_origin) / np.timedelta64(1, 'h')

# Ensure time is in float type
ds['time'] = xr.DataArray(ds['time'], dims='time')

# Add attributes to the time variable
ds['time'].attrs['units'] = 'hours since 1970-01-01 00:00:00'
ds['time'].attrs['long_name'] = 'time'
ds['time'].attrs['calendar'] = 'proleptic_gregorian'

# **Verify processed time variable values**
print("Processed time variable values:")
print(ds['time'].values)

# **Step 5: Process coordinates and dimensions**
# Rename coordinates to match ERA5 data
ds = ds.rename({
    'longitude': 'lon',
    'latitude': 'lat',
})

# Adjust dimension order
ds = ds.transpose('time', 'lat', 'lon', 'level')

# **Step 6: Extract and process necessary variables**

# **6.1 Extract SLP (Sea Level Pressure)**
SLP = ds['surface_pressure'].rename('SLP')
SLP.attrs['long_name'] = 'sea_level_pressure'
SLP.attrs['units'] = 'Pa'

# **6.2 Extract U10M and V10M (10m Wind Speed)**
levels = ds['level'].values
try:
    idx_1000 = int(np.where(levels == 1000)[0][0])  # 1000 hPa index
except IndexError:
    raise ValueError("1000 hPa level not found, please check 'level' variable values.")

# Extract U10M and V10M
U10M = ds['u_component_of_wind'].isel(level=idx_1000).drop_vars('level').rename('U10M')
V10M = ds['v_component_of_wind'].isel(level=idx_1000).drop_vars('level').rename('V10M')

# Add attributes
U10M.attrs['long_name'] = '10-meter_eastward_wind'
U10M.attrs['units'] = 'm s-1'
V10M.attrs['long_name'] = '10-meter_northward_wind'
V10M.attrs['units'] = 'm s-1'

# **6.3 Extract Temperature T**
# Extract temperature at 300 hPa, 500 hPa, and 850 hPa levels
desired_levels = [300, 500, 850]  # hPa
level_indices = []
for lev in desired_levels:
    idx = np.where(levels == lev)[0]
    if len(idx) == 0:
        raise ValueError(f"Level {lev} hPa not found, please check 'level' variable values.")
    level_indices.append(int(idx[0]))

# Extract temperature and rename level dimension
T = ds['temperature'].isel(level=level_indices).rename({'level': 'lev'})
T = T.assign_coords(lev=('lev', desired_levels))
T.attrs['long_name'] = 'air_temperature'
T.attrs['units'] = 'K'
T.attrs['standard_name'] = 'air_temperature'

# **6.4 Extract Geopotential Height H**
# Convert geopotential to height at the desired levels (unit: meters)
g = 9.80665  # Gravity acceleration in m s-2
H = ds['geopotential'].isel(level=level_indices) / g
H = H.rename({'level': 'lev'})
H = H.assign_coords(lev=('lev', desired_levels))
H.attrs['long_name'] = 'edge_heights'
H.attrs['units'] = 'm'
H.attrs['standard_name'] = 'edge_heights'

# **6.5 Process lev variable**
# Ensure lev is float type and create DataArray
lev = xr.DataArray(np.array(desired_levels, dtype='float64'), dims='lev')
lev.attrs['long_name'] = 'vertical level'
lev.attrs['units'] = 'hPa'
lev.attrs['positive'] = 'down'
lev.attrs['coordinate'] = 'PLE'
lev.attrs['standard_name'] = 'PLE_level'
lev.attrs['origname'] = 'lev'
lev.attrs['fullnamepath'] = '/lev'
lev.attrs['vmax'] = 1.e+15
lev.attrs['vmin'] = -1.e+15
lev.attrs['valid_range'] = (-1.e+15, 1.e+15)

# **6.6 Extract PHIS and process**
PHIS = ds['geopotential'].isel(level=idx_1000) / g
PHIS = PHIS.drop_vars('level').rename('PHIS')
PHIS.attrs['long_name'] = 'surface_geopotential_height'
PHIS.attrs['units'] = 'm'

# **Step 7: Create new dataset**
ds_te = xr.Dataset(
    {
        'SLP': SLP,
        'U10M': U10M,
        'V10M': V10M,
        'T': T,
        'H': H,
        'PHIS': PHIS,
    },
    coords={
        'lon': ds['lon'],
        'lat': ds['lat'],
        'time': ds['time'],
        'lev': lev,
    }
)

# **Step 8: Adjust dimension order**
ds_te = ds_te.transpose('time', 'lev', 'lat', 'lon')

# **Step 9: Handle missing values**

fill_value_float = 1.e+15
variables_with_fill_value = ['SLP', 'U10M', 'V10M']
variables_with_nan = ['T', 'H', 'PHIS']

# Handle SLP, U10M, V10M
for var in variables_with_fill_value:
    ds_te[var] = ds_te[var].where(np.isfinite(ds_te[var]), fill_value_float)
    # Set encoding attributes
    ds_te[var].encoding['_FillValue'] = fill_value_float
    # Add additional attributes
    ds_te[var].attrs['missing_value'] = fill_value_float
    ds_te[var].attrs['valid_range'] = (-fill_value_float, fill_value_float)
    ds_te[var].attrs['vmax'] = fill_value_float
    ds_te[var].attrs['vmin'] = -fill_value_float
    ds_te[var].attrs['add_offset'] = 0.0
    ds_te[var].attrs['scale_factor'] = 1.0
    ds_te[var].attrs['fmissing_value'] = fill_value_float

# Handle T, H, PHIS
for var in variables_with_nan:
    ds_te[var] = ds_te[var].where(np.isfinite(ds_te[var]), np.nan)
    # Set encoding attributes
    ds_te[var].encoding['_FillValue'] = np.nan
    # Add additional attributes
    ds_te[var].attrs['missing_value'] = np.nan
    ds_te[var].attrs['valid_range'] = (-fill_value_float, fill_value_float)
    ds_te[var].attrs['vmax'] = fill_value_float
    ds_te[var].attrs['vmin'] = -fill_value_float
    ds_te[var].attrs['origname'] = var
    ds_te[var].attrs['fullnamepath'] = f"/{var}"
    ds_te[var].attrs['fmissing_value'] = fill_value_float

# **Step 10: Process coordinate variables**
# Set attributes for coordinate variables
ds_te['lon'].attrs['long_name'] = 'longitude'
ds_te['lon'].attrs['units'] = 'degrees_east'
ds_te['lat'].attrs['long_name'] = 'latitude'
ds_te['lat'].attrs['units'] = 'degrees_north'
ds_te['time'].attrs['long_name'] = 'time'
ds_te['time'].attrs['units'] = 'hours since 1970-01-01 00:00:00'
ds_te['time'].attrs['calendar'] = 'proleptic_gregorian'

# Ensure coordinate variables are in float type and set encoding attributes
for coord in ['lon', 'lat', 'time', 'lev']:
    ds_te[coord] = ds_te[coord].astype('float64')
    ds_te[coord].encoding['_FillValue'] = None  # Do not set _FillValue

# **Step 11: Add global attributes**
ds_te.attrs['History'] = 'Generated from NeuralGCM data'
ds_te.attrs['Conventions'] = 'CF-1.7'
ds_te.attrs['Institution'] = 'Your Institution'
ds_te.attrs['Source'] = 'NeuralGCM model output'
ds_te.attrs['Contact'] = 'Your Contact Information'
ds_te.attrs['Description'] = 'NeuralGCM data processed to match ERA5 format for TempestExtremes'

# **Step 12: Save as NetCDF file**
output_path = '/home/cl4460/NeuralGCM/predictions_output_onemonth_TE_ready.nc'
ds_te.to_netcdf(output_path)

print(f"Output has been saved to: {output_path}")
