import xarray as xr


ds = xr.open_zarr(
    'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3',
    chunks=None,
    storage_options=dict(token='anon'),
)


lat_bounds = slice(50, 25)  
lon_min = (-125 + 360) % 360  
lon_max = (-66 + 360) % 360  
lon_bounds = slice(lon_min, lon_max)


topo = ds['geopotential'].isel(time=0).sel(latitude=lat_bounds, longitude=lon_bounds)
topo_height = topo / 9.80665
topo_height = topo_height.rename('Zs').rename({'longitude': 'lon', 'latitude': 'lat'})


topo_height.attrs['units'] = 'm'
topo_height.attrs['long_name'] = 'Surface Geopotential Height'
topo_height.attrs['standard_name'] = 'surface_geopotential_height'


topo_height['lat'].attrs['units'] = 'degrees_north'
topo_height['lon'].attrs['units'] = 'degrees_east'


topo_height = topo_height.load()
topo_height.to_netcdf('/home/cl4460/ERA5/ERA5_topo.nc')
print(topo_height)
