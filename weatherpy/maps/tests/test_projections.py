import cartopy.crs as ccrs

from weatherpy.maps import projections


class DummyCfVariable(object):
    def __init__(self, **kwargs):
        self._var_dict = kwargs

    def ncattrs(self):
        return self._var_dict.keys()

    def __getattr__(self, item):
        if item[0] != '_':
            return self._var_dict[item]
        else:
            return None


# TODO: load a real NetCDF variable?
def test_should_get_lcc_projection():
    lcc_var = DummyCfVariable(**{'grid_mapping_name': 'lambert_conformal_conic',
                                 'latitude_of_projection_origin': 25.0,
                                 'longitude_of_central_meridian': -95.0,
                                 'standard_parallel': 25.0,
                                 'earth_radius': 6371229.0})

    expected_proj = ccrs.LambertConformal(central_longitude=-95.0,
                                          central_latitude=25.0,
                                          standard_parallels=[25.0],
                                          globe=ccrs.Globe(ellipse='sphere',
                                                           semimajor_axis=6371229.0,
                                                           semiminor_axis=6371229.0))

    assert projections.from_cf_var(lcc_var) == expected_proj
