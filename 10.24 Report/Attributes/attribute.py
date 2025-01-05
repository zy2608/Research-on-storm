from netCDF4 import Dataset, num2date, date2num

input_path = '/home/zy2608/tempest_project/ERA5_TE_ready_2022.nc'
output_path = '/data0/zy2608/ERA5_TE_ready_2022_modified_generalized.nc'

desired_units = {
    'SLP': 'Pa',
    'U10M': 'm s⁻¹',
    'V10M': 'm s⁻¹',
    'time': 'hours',  
    'T': 'K',
    'H': 'm',
    'lev': 'hPa',
    'lat': 'degrees_north',
    'lon': 'degrees_east'
}

with Dataset(input_path, 'r') as src:
    with Dataset(output_path, 'w') as dst:
        dst.setncatts({k: src.getncattr(k) for k in src.ncattrs()})
        for name, dimension in src.dimensions.items():
            dst.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))
        for name, variable in src.variables.items():
            current_units = variable.units if 'units' in variable.ncattrs() else None
            new_units = desired_units.get(name)

            if name == 'time':
                time_var = dst.createVariable(name, variable.datatype, variable.dimensions)
                if current_units and "since" in current_units:
                    reference_date = current_units.split("since")[-1].strip()
                    new_units = f'hours since {reference_date}'
                else:
                    new_units = 'hours'
                time_values = variable[:]
                if current_units and 'hours' not in current_units:
                    time_dates = num2date(time_values, current_units, calendar='proleptic_gregorian')
                    new_time_values = date2num(time_dates, new_units, calendar='proleptic_gregorian')
                else:
                    new_time_values = time_values
                new_attrs = {k: variable.getncattr(k) for k in variable.ncattrs()}
                new_attrs['units'] = new_units
                time_var.setncatts(new_attrs)
                time_var[:] = new_time_values

            else:
                out_var = dst.createVariable(name, variable.datatype, variable.dimensions)
                new_attrs = {k: variable.getncattr(k) for k in variable.ncattrs()}
                if new_units and current_units != new_units:
                    new_attrs['units'] = new_units  
                out_var.setncatts(new_attrs)
                out_var[:] = variable[:]

print(f"New dataset saved to {output_path}")

