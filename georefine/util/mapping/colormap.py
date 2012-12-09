import georefine.util.mapping.interpolate as interpolate
from bisect import bisect


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
                  include_bins=[], value_bin_pct_width=.1):
    """ Generate a set of (v0, v1) bins from the given parameters.
    If 'include_bins' is specified, those bins are merged (see below) into the list 
    of generated bins.
    If 'include_values' is specified, bins are generated for each value,
    with each generated bin being 'value_bin_pct_width' wide. These bins are
    then merged into the list of generated bins.
    Merging bins: bins are merged by 'cracking' existing bins in order to fit
    in the new bins, so that there are no overlaps and no gaps.
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
        bins.append(tuple(vmin + i * bin_width, 
                          vmin + (i+1) * bin_width))

    # Generate bins for include_values.
    include_values_bins = []
    for v in include_values:
        v_bin_width = bin_width * value_bin_pct_width
        v_bin = tuple(v - v_bin_width/2.0, v + v_bin_width/2.0)
        include_values_bins.append(v_bin)

    # Merge in bins from include_bins and include_values.
    for bin_ in include_bins + include_values_bins:
        # Left intersect = bin whose x0 <= merge_bin x0.
        left_bin_idx = bisect([b[0] for b in bins], bin_[0]) - 1
        if left_bin_idx > -1:
            left_bin = bins[left_bin_idx]
        else:
            left_bin = None
        # Right intersect = bin whose xf >= merge_bin x1.
        right_bin_idx = bisect([b[1] for b in bins], bin_[1]) - 1
        if right_bin_idx < len(bins):
            right_bin = bins[right_bin_idx]
        else:
            right_bin = None
        # Remove all bins from left_intersect to right_intersect.
        bins[left_bin_idx:right_bin_idx] = []

        # Insert new bins, starting from left_intersect.
        new_bins = []
        if left_bin:
            new_bins.append(tuple(left_bin[0], bin_[0]))
        new_bins.append(bin_)
        if right_bin:
            new_bins.append(tuple(bin_[1], right_bin[1]))
