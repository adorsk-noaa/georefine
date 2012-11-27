from bisect import bisect


def lin_interpolate(xs, curve, clip=False):
    """ Linear interpolation. """
    interpolated_points = []
    sorted_curve = sorted(curve, key=lambda p: p[0])
    sorted_xs = [x for x, y in sorted_curve]
    for x in xs:
        x_min_idx = min(bisect(sorted_xs, x) - 1, len(sorted_xs) - 1)
        x_min = sorted_xs[x_min_idx]
        if x == x_min:
            interpolated_points.append(sorted_curve[x_min_idx])
            continue
        x_max_idx = min(bisect(sorted_xs, x), len(sorted_xs) - 1)
        x_max = sorted_xs[x_max_idx]
        if x == x_max:
            interpolated_points.append(sorted_curve[x_max_idx])
            continue
        if not clip:
            pass
            #@TODO: calculate slope here for points that go off the end.
        x_range = x_max - x_min
        y_min = sorted_curve[x_min_idx][1]
        y_max = sorted_curve[x_max_idx][1]
        y_range = y_max - y_min
        if x_range != 0:
            x_normalized = float((x - x_min))/x_range
            y = x_normalized * y_range
        else:
            y = y_min
        interpolated_points.append((x,y,))
    return interpolated_points
