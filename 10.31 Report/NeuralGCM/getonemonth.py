import os

# Set environment variables for PROJ data directory
os.environ['PROJ_LIB'] = '/home/cl4460/proj_data'
os.environ['PROJ_DATA'] = '/home/cl4460/proj_data'
os.environ['PROJ_NETWORK'] = 'ON'

from pyproj import datadir
# Set PROJ data directory path
datadir.set_data_dir('/home/cl4460/proj_data')

import jax
import gcsfs
import numpy as np
import pickle
import xarray
from dinosaur import horizontal_interpolation
from dinosaur import spherical_harmonic
from dinosaur import xarray_utils
import neuralgcm

# Load checkpoint using an anonymous token
gcs = gcsfs.GCSFileSystem(token='anon')
model_name = 'neural_gcm_dynamic_forcing_deterministic_1_4_deg.pkl'

# Load checkpoint
with gcs.open(f'gs://gresearch/neuralgcm/04_30_2024/{model_name}', 'rb') as f:
    ckpt = pickle.load(f)

# Define new input units mapping
new_inputs_to_units_mapping = {
    'u': 'meter / second',
    'v': 'meter / second',
    't': 'kelvin',
    'z': 'm**2 s**-2',
    'sim_time': 'dimensionless',
    'tracers': {
        'specific_humidity': 'dimensionless',
        'specific_cloud_liquid_water_content': 'dimensionless',
        'specific_cloud_ice_water_content': 'dimensionless',
    },
    'diagnostics': {
        'surface_pressure': 'kg / (meter s**2)'
    }
}

# Create new model configuration string, modify only in memory
new_model_config_str = '\n'.join([
    ckpt['model_config_str'],
    f'DimensionalLearnedPrimitiveToWeatherbenchDecoder.inputs_to_units_mapping = {new_inputs_to_units_mapping}',
    'DimensionalLearnedPrimitiveToWeatherbenchDecoder.diagnostics_module = @NodalModelDiagnosticsDecoder',
    'StochasticPhysicsParameterizationStep.diagnostics_module = @SurfacePressureDiagnostics',
])

# Update configuration in the checkpoint
ckpt['model_config_str'] = new_model_config_str

# Load model with the modified checkpoint and proceed with subsequent code
model = neuralgcm.PressureLevelModel.from_checkpoint(ckpt)

# Further data processing and prediction code remains the same
era5_path = 'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3'
full_era5 = xarray.open_zarr(gcs.get_mapper(era5_path), chunks=None)

# Define start and end times for demo data
demo_start_time = '2020-07-01'
demo_end_time = '2020-07-30'
data_inner_steps = 6  # Process data every 6 hours

# Slice ERA5 data and select relevant variables
sliced_era5 = (
    full_era5
    [model.input_variables + model.forcing_variables]
    .pipe(
        xarray_utils.selective_temporal_shift,
        variables=model.forcing_variables,
        time_shift='6 hours',
    )
    .sel(time=slice(demo_start_time, demo_end_time, data_inner_steps))
    .compute()
)

# Define grid for ERA5 data
era5_grid = spherical_harmonic.Grid(
    latitude_nodes=full_era5.sizes['latitude'],
    longitude_nodes=full_era5.sizes['longitude'],
    latitude_spacing=xarray_utils.infer_latitude_spacing(full_era5.latitude),
    longitude_offset=xarray_utils.infer_longitude_offset(full_era5.longitude),
)

# Create regridder for conservative interpolation
regridder = horizontal_interpolation.ConservativeRegridder(
    era5_grid, model.data_coords.horizontal, skipna=True
)

# Regrid and fill missing data in ERA5 sliced data
eval_era5 = xarray_utils.regrid(sliced_era5, regridder)
eval_era5 = xarray_utils.fill_nan_with_nearest(eval_era5)

# Define inner and outer steps for model output saving
inner_steps = 6  # Save model output every 6 hours
outer_steps = 15 * 24 // inner_steps  # Predict for a total of 15 days
timedelta = np.timedelta64(1, 'h') * inner_steps
times = (np.arange(outer_steps) * inner_steps)  # Time axis in hours

# Initialize model state
inputs = model.inputs_from_xarray(eval_era5.isel(time=0))
input_forcings = model.forcings_from_xarray(eval_era5.isel(time=0))
rng_key = jax.random.key(42)  # Used for deterministic model
initial_state = model.encode(inputs, input_forcings, rng_key)

# Use persistence of forcing variables (SST and sea ice cover)
all_forcings = model.forcings_from_xarray(eval_era5.head(time=1))

# Run model prediction
final_state, predictions = model.unroll(
    initial_state,
    all_forcings,
    steps=outer_steps,
    timedelta=timedelta,
    start_with_input=True,
)
predictions_ds = model.data_to_xarray(predictions, times=times)

# Select ERA5 target data, ensuring time slices match
target_trajectory = model.inputs_from_xarray(
    eval_era5
    .thin(time=(inner_steps // data_inner_steps))
    .isel(time=slice(outer_steps))
)
target_data_ds = model.data_to_xarray(target_trajectory, times=times)

# Concatenate predictions and target data
combined_ds = xarray.concat([target_data_ds, predictions_ds], 'model')
combined_ds.coords['model'] = ['ERA5', 'NeuralGCM']

# Save the result to a NetCDF file
output_path = '/data0/cl4460/predictions_output_onemonth.nc'
combined_ds.to_netcdf(output_path)

print(f"output has been preserved: {output_path}")
