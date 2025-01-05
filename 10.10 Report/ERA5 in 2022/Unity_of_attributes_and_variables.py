import xarray as xr
import numpy as np

era5_ds = xr.open_dataset('ERA5_TE_ready_2022.nc')
merra2_ds = xr.open_dataset('/home/skompella/MERRA2/TE_data/TE_ready_MERRA2_198001.nc')
variables_to_process = ['SLP', 'U10M', 'V10M', 'T', 'H', 'lev', 'time']

def replace_variable_attrs(era5_var, merra2_var):
    era5_var = era5_var.astype(merra2_var.dtype)
    era5_var.attrs = {}
    era5_var.attrs.update(merra2_var.attrs)
    era5_var.encoding = {}

    if merra2_var.encoding:
        era5_var.encoding.update(merra2_var.encoding)
    return era5_var

for var_name in variables_to_process:
    if var_name in era5_ds and var_name in merra2_ds:
        era5_ds[var_name] = replace_variable_attrs(era5_ds[var_name], merra2_ds[var_name])
    else:
        print(f"The variable '{var_name}' was not found in both datasets.")

for coord_name in ['lat', 'lon']:
    if coord_name in era5_ds.coords and coord_name in merra2_ds.coords:
        era5_ds.coords[coord_name].attrs = merra2_ds.coords[coord_name].attrs.copy()
        era5_ds.coords[coord_name] = era5_ds.coords[coord_name].astype(merra2_ds.coords[coord_name].dtype)
    else:
        print(f"The coordinate '{coord_name}' is not found in both datasets.")


era5_vars_to_remove = set(era5_ds.data_vars) - set(variables_to_process)
for var_name in era5_vars_to_remove:
    print(f"Remove the redundant variable '{var_name}' from the ERA5 dataset.")
    era5_ds = era5_ds.drop_vars(var_name)
    
era5_coords_to_remove = set(era5_ds.coords) - set(['lat', 'lon', 'lev', 'time'])

for coord_name in era5_coords_to_remove:
    print(f"Removes redundant coordinates '{coord_name}' from the ERA5 dataset.")
    era5_ds = era5_ds.drop_vars(coord_name)

# Update global attributes
era5_ds.attrs = merra2_ds.attrs.copy()
if '_NCProperties' in era5_ds.attrs:
    del era5_ds.attrs['_NCProperties']

era5_ds.to_netcdf('ERA5_TE_ready_2022_modified_v5.nc')

