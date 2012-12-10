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

def generate_bins(vmin=0, vmax=1, num_bins=10, include_values=[],
                  include_bins=[], value_bin_pct_width=.2):
    """ Generate a set of (v0, v1) bins from the given parameters.
    If 'include_bins' is specified, those bins are merged (see below) into the list 
    of generated bins.
    If 'include_values' is specified, bins are generated for each value,
    with each generated bin being 'value_bin_pct_width' wide. These bins are
    then merged into the list of generated bins.
    Merging bins: bins are merged by 'cracking' existing bins in order to fit
    in the new bins.
    For example, if the initial bin list is [(0,5), (5,10)],
    and we merge in (3,7), the merged bin list will be [(0,3),(3,7),(7,10)].
    If a new bin spans multiple existing bins, it will consume them.
    For example, if the initial bin list is [(0,1), (1,2), (2,3), (3,4)]
    and we merge in (0, 2.5), the merged bin list will be [(0,2.5),(2.5,3),(3,4)].
    Note that bins produced by 'include_values' are merged *after* bins from
    'include_bins'. This means that bins 'include_values' takes precedence over
    include_bins.
    """
    # Generate the initial bin list.
    bins = []
    vrange = vmax - vmin
    bin_width = 0
    if num_bins > 0:
        bin_width = 1.0 * vrange/num_bins
    for i in range(num_bins):
        bins.append((vmin + i * bin_width, vmin + (i+1) * bin_width,))

    # Generate bins for include_values.
    include_values_bins = []
    for v in include_values:
        v_bin_width = bin_width * value_bin_pct_width
        v_bin = (v - v_bin_width/2.0, v + v_bin_width/2.0,)
        include_values_bins.append(v_bin)

    # Merge in bins from include_bins and include_values.
    for bin_ in include_bins + include_values_bins:

        left_bin = None
        slice_start = None
        for i in range(len(bins)):
            if bins[i][0] <= bin_[0]:
                left_bin = bins[i]
                slice_start = i
            else:
                break
        if left_bin and left_bin[1] <= bin_[0]:
            left_bin = None
            slice_start = len(bins)

        right_bin = None
        slice_end = len(bins)
        for i in range(len(bins) - 1, -1, -1):
            if bins[i][1] >= bin_[1]:
                right_bin = bins[i]
                slice_end = i + 1
            else:
                break
        if right_bin and right_bin[0] >= bin_[1]:
            right_bin = None
            slice_end = 0
        
        # Replace bins with new bins.
        new_bins = []
        if left_bin:
            new_bins.append((left_bin[0], bin_[0],))
        new_bins.append(bin_)
        if right_bin:
            new_bins.append((bin_[1], right_bin[1],))
        bins[slice_start:slice_end] = new_bins

    return sorted(bins, key=lambda b: b[0])
