import time
from rgkit.render.settings import settings as render_settings


def millis():
    return int(time.time() * 1000)


def rgb_to_hex(r, g, b, normalized=True):
    if normalized:
        return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
    else:
        return '#%02x%02x%02x' % (int(r), int(g), int(b))


def rgb_tuple_to_hex(rgb, normalized=True):
    return rgb_to_hex(rgb[0], rgb[1], rgb[2], normalized)


def blend_colors(color1, color2, weight):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = r1 * weight + r2 * (1 - weight)
    g = g1 * weight + g2 * (1 - weight)
    b = b1 * weight + b2 * (1 - weight)
    return (r, g, b)


def compute_color(player_id, hp, action):
    r, g, b = render_settings.colors[player_id]
    maxclr = min(hp, 50)
    r += (100 - maxclr * 1.75) / 255
    g += (100 - maxclr * 1.75) / 255
    b += (100 - maxclr * 1.75) / 255
    color = (r, g, b)
    if action is 'guard' and render_settings.color_guard is not None:
        color = blend_colors(color, render_settings.color_guard, 0.65)
    return color
