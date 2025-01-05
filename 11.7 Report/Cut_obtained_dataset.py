iimport xarray as xr
import numpy as np
input_path = '/data0/zy2608/predictions_output_0701.nc'
ds = xr.open_dataset(input_path)
ds = ds[["v_component_of_wind", "u_component_of_wind", "temperature", "geopotential", "surface_pressure"]]
ds = ds.isel(model=1)

ds['time'].attrs['units'] = 'hours since 2020-07-01 00:00:00'
ds['time'].attrs['calendar'] = 'proleptic_gregorian'

ds = xr.decode_cf(ds)
print("Decoded time variable:")
print(ds['time'].values)
time_origin = np.datetime64('2020-07-01T00:00:00')
ds['time'] = (ds['time'].values - time_origin) / np.timedelta64(1, 'h')
ds['time'] = xr.DataArray(ds['time'], dims='time')
ds['time'].attrs['units'] = 'hours since 2020-07-01 00:00:00'

print("Processed time variable values:")
print(ds['time'].values)
ds = ds.rename({
    'longitude': 'lon',
    'latitude': 'lat',
})
ds = ds.transpose('time', 'lat', 'lon', 'level')
SLP = ds['surface_pressure'].rename('SLP')
SLP.attrs['units'] = 'Pa'

levels = ds['level'].values
try:
    idx_1000 = int(np.where(levels == 1000)[0][0])  # 1000 hPa index
except IndexError:
    raise ValueError("1000 hPa level not found, please check 'level' variable values.")

U10M = ds['u_component_of_wind'].isel(level=idx_1000).drop_vars('level').rename('U10M')
V10M = ds['v_component_of_wind'].isel(level=idx_1000).drop_vars('level').rename('V10M')

U10M.attrs['units'] = 'm s-1'
V10M.attrs['units'] = 'm s-1'

desired_levels = [300, 500, 850]  # hPa
level_indices = []
for lev in desired_levels:
    idx = np.where(levels == lev)[0]
    if len(idx) == 0:
        raise ValueError(f"Level {lev} hPa not found, please check 'level' variable values.")
    level_indices.append(int(idx[0]))
T = ds['temperature'].isel(level=level_indices).rename({'level': 'lev'})
T = T.assign_coords(lev=('lev', desired_levels))
T.attrs['units'] = 'K'

g = 9.80665 
H = ds['geopotential'].isel(level=level_indices) / g
H = H.rename({'level': 'lev'})
H = H.assign_coords(lev=('lev', desired_levels))
H.attrs['units'] = 'm'
lev = xr.DataArray(np.array(desired_levels, dtype='float64'), dims='lev')
lev.attrs['units'] = 'hPa'
PHIS = ds['geopotential'].isel(level=idx_1000) / g
PHIS = PHIS.drop_vars('level').rename('PHIS')
PHIS.attrs['units'] = 'm'
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

ds_te = ds_te.transpose('time', 'lev', 'lat', 'lon')


for coord in ['lon', 'lat', 'time', 'lev']:
    ds_te[coord] = ds_te[coord].astype('float64')

output_path = '/data0/zy2608/predictions_output_TE_ready_0701.nc'
ds_te.to_netcdf(output_path)

print(f"Output has been saved to: {output_path}")