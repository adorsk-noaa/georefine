import georefine.util.mapping.interpolate as interpolate


def get_mapped_hsl(value, colormap):
    hsl_attrs = ['h', 's', 'l']
    mapped_hsl = {}
    for attr in hsl_attrs:
        mapped_hsl[attr] = interpolate.lin_interpolate(
            [value], colormap[attr])[0][1]
    return mapped_hsl

def generate_bw_colormap(vmin=0, vmax=1, w2b=True):
    return {
        'h': [(vmin, 0,)],
        's': [(vmin, 1,)],
        'l': [(vmin, 0.0,), (vmax, 1.0,)],
    }
