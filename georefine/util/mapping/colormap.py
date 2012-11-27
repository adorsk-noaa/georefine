import georefine.util.interpolate as interpolate


def get_mapped_hsl(value, colormap):
    hsl_attrs = ['h', 's', 'l']
    mapped_hsl = {}
    for attr in hsl_attrs:
        mapped_hsl[attr] = interpolate.lin_interpolate(
            [value], colormap[attr])[0][0]
    return mapped_hsl
