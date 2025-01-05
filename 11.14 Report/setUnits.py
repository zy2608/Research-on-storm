def setUnits(ds1):
    ''' set units of the given dataset '''
    ds = ds1[["v_component_of_wind", "u_component_of_wind", "temperature", "geopotential", "surface_pressure"]]

    ds['time'].attrs['units'] = 'hours since 2020-07-12 00:00:00'
    ds['time'].attrs['calendar'] = 'proleptic_gregorian'

    ds = xarray.decode_cf(ds)
    #print("Decoded time variable:")
    #print(ds['time'].values)
    time_origin = np.datetime64('2020-07-12T00:00:00')
    ds['time'] = (ds['time'].values - time_origin) / np.timedelta64(1, 'h')
    ds['time'] = xarray.DataArray(ds['time'], dims='time')
    ds['time'].attrs['units'] = 'hours since 2020-07-12 00:00:00'

    #print("Processed time variable values:")
    #print(ds['time'].values)
    ds = ds.rename({
        'longitude': 'lon',
        'latitude': 'lat',
    })
    ds = ds.transpose('time', 'lat', 'lon', 'level')
    SLP = ds['surface_pressure'].rename('SLP')
    SLP.attrs['units'] = 'Pa'

    levels = ds['level'].values
    #try:
    #    idx_1000 = int(np.where(levels == 1000)[0][0])  # 1000 hPa index
    #except IndexError:
    #    raise ValueError("1000 hPa level not found, please check 'level' variable values.")

    U10M = ds['u_component_of_wind'].sel(level=1000).drop_vars('level').rename('U10M')
    V10M = ds['v_component_of_wind'].sel(level=1000).drop_vars('level').rename('V10M')

    U10M.attrs['units'] = 'm s-1'
    V10M.attrs['units'] = 'm s-1'

    desired_levels = [300, 500, 850]  # hPa
    #level_indices = []
    #for lev in desired_levels:
    #    idx = np.where(levels == lev)[0]
    #    if len(idx) == 0:
    #        raise ValueError(f"Level {lev} hPa not found, please check 'level' variable values.")
    #    level_indices.append(int(idx[0]))
    T = ds['temperature'].sel(level=desired_levels).rename({'level': 'lev'})
    T = T.assign_coords(lev=('lev', desired_levels))
    T.attrs['units'] = 'K'

    g = 9.80665 
    H = ds['geopotential'].sel(level=desired_levels) / g
    H = H.rename({'level': 'lev'})
    H = H.assign_coords(lev=('lev', desired_levels))
    H.attrs['units'] = 'm'
    lev = xarray.DataArray(np.array(desired_levels, dtype='float64'), dims='lev')
    lev.attrs['units'] = 'hPa'
    PHIS = ds['geopotential'].sel(level=1000) / g
    PHIS = PHIS.drop_vars('level').rename('PHIS')
    PHIS.attrs['units'] = 'm'
    ds_te = xarray.Dataset(
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
    return ds_te
