import xarray as xr


ds = xr.open_zarr(
    'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3',
    chunks=None,  
    storage_options=dict(token='anon'),
)

time = '2022-07'
lat_bounds = slice(50, 25)  
lon_bounds = slice(-125, -66) 
level = [300, 400, 500]


u10 = ds['10m_u_component_of_wind'].sel(time=time, latitude=lat_bounds, longitude=lon_bounds)
v10 = ds['10m_v_component_of_wind'].sel(time=time, latitude=lat_bounds, longitude=lon_bounds)
pressure = ds['mean_sea_level_pressure'].sel(time=time, latitude=lat_bounds, longitude=lon_bounds)
h = ds['geopotential'].sel(time=time, level=level, latitude=lat_bounds, longitude=lon_bounds)
t = ds['temperature'].sel(time=time, level=level, latitude=lat_bounds, longitude=lon_bounds)


u10 = u10.rename('U10M').rename({'longitude': 'lon', 'latitude': 'lat'})
v10 = v10.rename('V10M').rename({'longitude': 'lon', 'latitude': 'lat'})
pressure = pressure.rename('SLP').rename({'longitude': 'lon', 'latitude': 'lat'})
h = h.rename('H').rename({'longitude': 'lon', 'latitude': 'lat'})
t = t.rename('T').rename({'longitude': 'lon', 'latitude': 'lat'})
topo = topo.rename('Zs').rename({'longitude': 'lon', 'latitude': 'lat'})

dataset = xr.Dataset({
    'SLP': pressure,
    'U10M': u10,
    'V10M': v10,
    'H': h,
    'T': t,
})

dataset['time'].attrs['units'] = 'hours since 1900-01-01'
dataset['time'].attrs['calendar'] = 'proleptic_gregorian'

dataset = dataset.rename({'level': 'lev'})
dataset['lev'].attrs['units'] = 'hPa'
dataset['lev'].attrs['long_name'] = 'vertical level'
dataset['lev'].attrs['positive'] = 'down'
dataset['lev'].attrs['coordinate'] = 'PLE'
dataset['lev'].attrs['standard_name'] = 'PLE_level'

dataset['lat'].attrs['units'] = 'degrees_north'
dataset['lon'].attrs['units'] = 'degrees_east'


dataset['SLP'].attrs['units'] = 'Pa'
dataset['SLP'].attrs['long_name'] = 'sea_level_pressure'
dataset['SLP'].attrs['standard_name'] = 'air_pressure_at_mean_sea_level'

dataset['U10M'].attrs['units'] = 'm s-1'
dataset['U10M'].attrs['long_name'] = '10-meter_eastward_wind'
dataset['U10M'].attrs['standard_name'] = 'eastward_wind'

dataset['V10M'].attrs['units'] = 'm s-1'
dataset['V10M'].attrs['long_name'] = '10-meter_northward_wind'
dataset['V10M'].attrs['standard_name'] = 'northward_wind'

dataset['T'].attrs['units'] = 'K'
dataset['T'].attrs['long_name'] = 'air_temperature'
dataset['T'].attrs['standard_name'] = 'air_temperature'

dataset['H'].attrs['units'] = 'm'
dataset['H'].attrs['long_name'] = 'geopotential_height'
dataset['H'].attrs['standard_name'] = 'geopotential_height'

dataset['Zs'].attrs['units'] = 'm'
dataset['Zs'].attrs['long_name'] = 'Surface Geopotential Height'
dataset['Zs'].attrs['standard_name'] = 'surface_geopotential_height'


dataset = dataset.load()
dataset.to_netcdf('/home/cl4460/ERA5/ERA5_combined.nc')

