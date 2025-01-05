import datetime
import gcsfs
import jax
import numpy as np
import os
import pandas as pd
import pickle
import time as tm
import xarray

from dinosaur import horizontal_interpolation
from dinosaur import spherical_harmonic
from dinosaur import xarray_utils
import neuralgcm

MODEL_RES = '0_7'
DEMO_START_TIME = '1980-01-10'
#N_MONTHS = 1
DATA_INNER_STEPS = 6

def fetchModelData(res='2_8'):
    ''' returns the model and the ERA5 data'''
    gcs = gcsfs.GCSFileSystem(token='anon')
    model_name = 'neural_gcm_dynamic_forcing_deterministic_{}_deg.pkl'.format(res) 
    
    with gcs.open(f'gs://gresearch/neuralgcm/04_30_2024/{model_name}', 'rb') as f:
        ckpt = pickle.load(f)
    
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
    
    new_model_config_str = '\n'.join([
        ckpt['model_config_str'],
        f'DimensionalLearnedPrimitiveToWeatherbenchDecoder.inputs_to_units_mapping = {new_inputs_to_units_mapping}',
        'DimensionalLearnedPrimitiveToWeatherbenchDecoder.diagnostics_module = @NodalModelDiagnosticsDecoder',
        'StochasticPhysicsParameterizationStep.diagnostics_module = @SurfacePressureDiagnostics',
    ])
    
    ckpt['model_config_str'] = new_model_config_str
    
    model = neuralgcm.PressureLevelModel.from_checkpoint(ckpt)
    
    era5_path = 'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3'
    full_era5 = xarray.open_zarr(gcs.get_mapper(era5_path), chunks=None)
    
    return full_era5, model

def simulate(start_time=DEMO_START_TIME):
    ''' run the simulation '''
    print('beginning simulation starting from {}'.format(start_time))
    demo_start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    #use the below snippet if we need simulations spanning multiple months
    #sst_dates = pd.date_range(demo_start_time, periods=N_MONTHS , freq='MS').to_pydatetime().tolist()
    #demo_end_time = ( sst_dates[-1] + pd.offsets.MonthEnd() ).to_pydatetime()
    #sst_dates = [demo_start_time.replace(day=1)] #remove this later
    sst_dates = [demo_start_time]
    demo_end_time = demo_start_time + datetime.timedelta(days=14)
    demo_days = (demo_end_time-demo_start_time).days
    
    full_era5, model = fetchModelData(MODEL_RES)
    
    # get the forcing variables on these sst switch dates alone
    forcing_variables = full_era5[model.forcing_variables].sel(time=sst_dates)
    initial_conditions = full_era5[model.input_variables+model.forcing_variables].sel(time=demo_start_time)
    
    # regrid the data
    era5_grid = spherical_harmonic.Grid(
        latitude_nodes=full_era5.sizes['latitude'],
        longitude_nodes=full_era5.sizes['longitude'],
        latitude_spacing=xarray_utils.infer_latitude_spacing(full_era5.latitude),
        longitude_offset=xarray_utils.infer_longitude_offset(full_era5.longitude),
    )
    regridder = horizontal_interpolation.ConservativeRegridder(
        era5_grid, model.data_coords.horizontal, skipna=True
    )
    
    eval_era5 = xarray_utils.regrid(initial_conditions, regridder)
    eval_forcings = xarray_utils.regrid(forcing_variables, regridder)
    
    eval_era5 = xarray_utils.fill_nan_with_nearest(eval_era5)
    eval_forcings = xarray_utils.fill_nan_with_nearest(eval_forcings)
    
    inner_steps = DATA_INNER_STEPS
    outer_steps = 5 # we want to go upto 24 hours for each step of inference  
    timedelta = np.timedelta64(1, 'h') * inner_steps
    times = (np.arange(outer_steps) * inner_steps)  # time axis in hours for each step

    # initialize model state
    inputs = model.inputs_from_xarray(eval_era5)
    input_forcings = model.forcings_from_xarray(eval_era5)
    rng_key = jax.random.key(42)  # optional for deterministic models
    initial_state = model.encode(inputs, input_forcings, rng_key)
    
    # use persistence for forcing variables (SST and sea ice cover)
    all_forcings = model.forcings_from_xarray(eval_forcings)
    simfail = False
    
    # create the folder where the sims are going to be stored
    folderpath = './ngcm_start/'+start_time
    if not os.path.exists(folderpath):
        os.mkdir(folderpath)
    
    for d in range(demo_days+1):
        final_state, predictions = model.unroll(
            initial_state,
            all_forcings,
            steps=5, # outputs are for time=0,6,12,18,24
            timedelta=timedelta,
            start_with_input=True,
        )
        initial_state = final_state
        current_date = demo_start_time + datetime.timedelta(days=d)
        cur_times = np.timedelta64(1, 'h')*times + np.datetime64(current_date, 'ns')
        predictions_ds = model.data_to_xarray(predictions, times=cur_times)
        
        
        # use temperature as a proxy to see if it blows up
        if predictions_ds.temperature.isel(time=-1).sel(level=850).max().isnull():
            print('model blew up, stopping sim, start date: {}'.format(demo_start_time))
            simfail=True
            break
            
        predictions_ds.to_netcdf(folderpath+'/inf_{}.nc'.format(current_date.date()), mode='w')
        print('saved for date {}...'.format(current_date.date()))
        
    if not simfail:    
        print('sim success for start date {}!'.format(demo_start_time))
