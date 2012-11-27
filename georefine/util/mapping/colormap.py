import georefine.util.mapping.interpolate as interpolate


def get_mapped_color(value, colormap):
    color_attrs = colormap.keys()
    mapped_color = {}
    for attr in color_attrs:
        mapped_color[attr] = interpolate.lin_interpolate(
            [value], colormap[attr])[0][1]
    return mapped_color

def generate_hsl_bw_colormap(vmin=0, vmax=1, w2b=True):
    if w2b:
        l = [(vmin, 0.0), (vmax, 1.0)]
    else:
        l = [(vmin, 1.0), (vmax, 0.0)]
    return {
        'h': [(vmin, 0,)],
        's': [(vmin, 1,)],
        'l': l,
    }

def generate_rgb_bw_colormap(vmin=0, vmax=1, w2b=True):
    if w2b:
        points = [(vmin, 0.0), (vmax, 255)]
    else:
        points = [(vmin, 255), (vmax, 0.0)]
    return {
        'r': points,
        'g': points,
        'b': points,
    }
