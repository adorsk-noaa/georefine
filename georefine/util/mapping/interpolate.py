from bisect import bisect_left, bisect_right


def lin_interpolate(xs, curve):
    """ Linear interpolation. """
    interpolated_points = []
    sorted_curve = sorted(curve, key=lambda p: p[0])
    sorted_xs = [x for x, y in sorted_curve]
    sorted_ys = [y for x, y in sorted_curve]
    for x in xs:
        x_min_idx = bisect_left(sorted_xs, x)
        x_max_idx = bisect_right(sorted_xs, x)
        x_min = sorted_xs[x_min_idx]
        x_max = sorted_xs[x_max_idx]
        x_range_ = x_min - x_max
        y_min = sorted_curve[x_min_idx][1]
        y_max = sorted_curve[x_max_idx][1]
        y_range_ = y_min - y_max
        if x_range != 0:
            x_normalized = float((x - x_min))/x_range
            y = x_normalized * y_range
        else:
            y = y_min
        interpolated_points.push((x,y,))
    return interpolated_points
