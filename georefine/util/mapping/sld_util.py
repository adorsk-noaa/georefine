""" Utility functions for working with SLD files. """
from jinja2 import Environment, PackageLoader
import struct


template_env = Environment(
    loader=PackageLoader('georefine.util.mapping', 'templates')
)


def get_polygon_gradient_sld(layer_name="", value_attr="", classes=[]):
    global_min = classes[0][1]
    global_max = classes[-1][0]
    global_range = global_max - global_min

    color_classes = []
    for clazz in classes[1:-1]:
        local_min = clazz[0]
        color_value = float((local_min - global_min))/global_range * 255
        color_classes.append(clazz + [color_value])

    for color_class in color_classes:
        rgb_color = [color_class[2]] * 3
        hex_color = "#%s" % struct.pack('BBB', *rgb_color).encode('hex')
        color_class[2] = hex_color

    tpl = template_env.get_template('polygon_gradient_sld.xml')
    return tpl.render(
        layer_name=layer_name,
        value_attr=value_attr,
        color_classes=color_classes
    )

