import xarray as xr
ds = xr.open_zarr(
    'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3',
    chunks=None,
    storage_options=dict(token='anon'),
)
ds.time.sel(time=ds.time.dt.hour.isin([0, 6]))

time = '2022-07'
geopotential = ds['geopotential'].sel(time = time)
u10 = ds['10m_u_component_of_wind'].sel(time=time)
pressure = ds.mean_sea_level_pressure.sel(time=time)
v10 = ds['10m_v_component_of_wind'].sel(time=time)
level = [300, 400, 500] #replace with the desired levels
h = ds.geopotential.sel(time=time).sel(level=level)
t = ds.temperature.sel(time=time).sel(level=level)

u10.load()
h.load()
t.load()
pressure.load()
v10.load()
geopotential.load()

comp = dict(zlib=True)

pressure.encoding.update(comp)
h.encoding.update(comp)
t.encoding.update(comp)
v10.encoding.update(comp)
geopotential.encoding.update(comp)
u10.encoding.update(comp)

pressure.to_netcdf(r'/home/zy2608/zy2608/9.22/pressure.nc')
t.to_netcdf(r'/home/zy2608/zy2608/9.22/t.nc')
h.to_netcdf(r'/home/zy2608/zy2608/9.22/h.nc')
v10.to_netcdf(r'/home/zy2608/zy2608/9.22/v10.nc')
geopotential.to_netcdf(r'/home/zy2608/zy2608/9.22/geopotential.nc')
u10.to_netcdf(r'/home/zy2608/zy2608/9.22/u10.nc')




