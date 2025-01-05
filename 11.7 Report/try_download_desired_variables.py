import os
import jax
import gcsfs
import numpy as np
import pickle
import xarray as xr
from dinosaur import horizontal_interpolation
from dinosaur import spherical_harmonic
from dinosaur import xarray_utils
import neuralgcm
import json

# **Step 1: Set Environment Variables**
os.environ['PROJ_LIB'] = '/home/cl4460/proj_data'
os.environ['PROJ_DATA'] = '/home/cl4460/proj_data'
os.environ['PROJ_NETWORK'] = 'ON'

from pyproj import datadir
datadir.set_data_dir('/home/cl4460/proj_data')

# **Step 2: Load Model Checkpoint**
gcs = gcsfs.GCSFileSystem(token='anon')
model_name = 'neural_gcm_dynamic_forcing_deterministic_1_4_deg.pkl'

with gcs.open(f'gs://gresearch/neuralgcm/04_30_2024/{model_name}', 'rb') as f:
    ckpt = pickle.load(f)

# **Step 3: Define and Update Input Units Mapping**
# Only include variables required by the model
new_inputs_to_units_mapping = {
    'u': 'meter / second',
    'v': 'meter / second',
    't': 'kelvin',
    'z': 'meter',  # geopotential height in meters
    'specific_humidity': 'kg kg-1',
    'surface_pressure': 'Pa'
}

# **Step 4: Define Input Variables and Forcing Variables**
# Only include variables required for model run
new_input_variables = [
    'u',                # Eastward wind component
    'v',                # Northward wind component
    't',                # Temperature
    'z',                # Geopotential height
    'specific_humidity',# Specific humidity
    'surface_pressure'  # Surface pressure
]
new_forcing_variables = [
    'sea_surface_temperature',  # Sea surface temperature
    'sea_ice_cover'             # Sea ice cover
]

# **Step 5: Create New Model Configuration String**
new_model_config_str = '\n'.join([
    ckpt['model_config_str'],
    f'DimensionalLearnedPrimitiveToWeatherbenchDecoder.inputs_to_units_mapping = {json.dumps(new_inputs_to_units_mapping)}',
    'DimensionalLearnedPrimitiveToWeatherbenchDecoder.diagnostics_module = @NodalModelDiagnosticsDecoder',
    'StochasticPhysicsParameterizationStep.diagnostics_module = @SurfacePressureDiagnostics',
    f'PressureLevelModel.input_variables = {json.dumps(new_input_variables)}',
    f'PressureLevelModel.forcing_variables = {json.dumps(new_forcing_variables)}',
])

# **Step 6: Update Configuration in Checkpoint**
ckpt['model_config_str'] = new_model_config_str

# **Step 7: Load Modified NeuralGCM Model**
model = neuralgcm.PressureLevelModel.from_checkpoint(ckpt)

# **Step 8: Define ERA5 Data Path and Required Variables**
era5_path = 'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3'

variables_needed = [
    'u_component_of_wind',          # u
    'v_component_of_wind',          # v
    'temperature',                  # t
    'geopotential',                 # z
    'surface_pressure',             # surface_pressure
    'specific_humidity',            # specific_humidity
    'sea_surface_temperature',      # Forcings
    'sea_ice_cover'                 # Forcings
]

# **Step 9: Open ERA5 Data and Select Required Variables**
print("Opening ERA5 dataset and selecting necessary variables...")
full_era5 = xr.open_zarr(
    gcs.get_mapper(era5_path),
    chunks={'time': 10},  # Adjust chunk size as needed
    consolidated=True
)[variables_needed]

print("Selected variables:")
print(full_era5.data_vars)

# **Step 10: Rename Variables to Match Model Expectations**
full_era5 = full_era5.rename({
    'u_component_of_wind': 'u',
    'v_component_of_wind': 'v',
    'temperature': 't',
    'geopotential': 'z'
    # 'surface_pressure' remains unchanged
    # 'specific_humidity' remains unchanged
    # 'sea_surface_temperature' remains unchanged
    # 'sea_ice_cover' remains unchanged
})

print("Renamed variables:")
print(full_era5.data_vars)

# **Step 11: Define Start and End Times**
demo_start_time = '2020-07-02'
demo_end_time = '2020-07-30'
data_inner_steps = 6  # Process data every 6 hours

# **Step 12: Slice ERA5 Data and Apply Selective Temporal Shift**
print("Slicing ERA5 data and applying temporal shift...")
sliced_era5 = (
    full_era5
    .sel(time=slice(demo_start_time, demo_end_time))
    .pipe(
        xarray_utils.selective_temporal_shift,
        variables=new_forcing_variables,
        time_shift='6 hours',
    )
    .isel(time=slice(None, None, data_inner_steps))
    .compute()
)

print("Sliced ERA5 dataset:")
print(sliced_era5)

# **Step 13: Define ERA5 Data Grid**
print("Defining ERA5 grid...")
era5_grid = spherical_harmonic.Grid(
    latitude_nodes=full_era5.sizes['latitude'],
    longitude_nodes=full_era5.sizes['longitude'],
    latitude_spacing=xarray_utils.infer_latitude_spacing(full_era5.latitude),
    longitude_offset=xarray_utils.infer_longitude_offset(full_era5.longitude),
)

# **Step 14: Create Conservative Regridder**
print("Creating conservative regridder...")
regridder = horizontal_interpolation.ConservativeRegridder(
    era5_grid, model.data_coords.horizontal, skipna=True
)

# **Step 15: Regrid and Fill Missing Data**
print("Regridding ERA5 data...")
eval_era5 = xarray_utils.regrid(sliced_era5, regridder)
print("Filling missing data...")
eval_era5 = xarray_utils.fill_nan_with_nearest(eval_era5)

print("Regridded ERA5 dataset:")
print(eval_era5)

# **Step 16: Define Prediction Steps and Time Interval**
inner_steps = 6  # Save model output every 6 hours
outer_steps = 15 * 24 // inner_steps  # Predict a total of 15 days
timedelta = np.timedelta64(1, 'h') * inner_steps
times = (np.arange(outer_steps) * inner_steps)  # Time axis in hours

# **Step 17: Initialize Model State**
print("Initializing model state...")
inputs = model.inputs_from_xarray(eval_era5.isel(time=0))
input_forcings = model.forcings_from_xarray(eval_era5.isel(time=0))
rng_key = jax.random.PRNGKey(42)  # For deterministic model
initial_state = model.encode(inputs, input_forcings, rng_key)

print("Model inputs initialized.")

# **Step 18: Prepare Forcings for Prediction Steps**
print("Preparing forcings for prediction steps...")
all_forcings = model.forcings_from_xarray(eval_era5.head(time=1))

# **Step 19: Run Model Prediction**
print("Running model prediction...")
final_state, predictions = model.unroll(
    initial_state,
    all_forcings,
    steps=outer_steps,
    timedelta=timedelta,
    start_with_input=True,
)
predictions_ds = model.data_to_xarray(predictions, times=times)

print("Model prediction completed.")

# **Step 20: Select ERA5 Target Data, Ensure Time Slices Match**
print("Selecting target trajectory data...")
target_trajectory = model.inputs_from_xarray(
    eval_era5
    .thin(time=(inner_steps // data_inner_steps))
    .isel(time=slice(outer_steps))
)
target_data_ds = model.data_to_xarray(target_trajectory, times=times)

print("Target trajectory data selected.")

# **Step 21: Concatenate Predictions and Target Data**
print("Concatenating predictions and target data...")
combined_ds = xr.concat([target_data_ds, predictions_ds], 'model')
combined_ds.coords['model'] = ['ERA5', 'NeuralGCM']

print("Combined dataset:")
print(combined_ds)

# **Step 22: Save Results to NetCDF File**
output_path = '/data0/cl4460/predictions_output_1106.nc'
print(f"Saving combined dataset to {output_path}...")
combined_ds.to_netcdf(output_path, encoding={var: {'zlib': True, 'complevel': 5} for var in combined_ds.data_vars})

print(f"Output has been saved to: {output_path}")
