try:
    import Tkinter
except ImportError:
    import tkinter as Tkinter
from rgkit.settings import settings
from rgkit.render.settings import settings as render_settings
from rgkit.render.utils import rgb_to_hex, rgb_tuple_to_hex, blend_colors
from rgkit.render.utils import compute_color


class RobotSprite(object):
    def __init__(self, action_info, render):
        self.location = action_info['loc']
        self.location_next = action_info['loc_end']
        self.action = action_info['name']
        self.target = action_info['target']
        self.hp = max(0, action_info['hp'])
        self.hp_next = max(0, action_info['hp_end'])
        self.id = action_info['player']
        self.renderer = render
        self.animation_offset = (0, 0)

        # Tkinter objects
        self.square = None
        self.border = None
        self.circle = None
        self.overlay = None
        self.text = None

    def animate(self, delta=0):
        """Animate this sprite.

           Delta is between 0 and 1. It tells us how far along to render (0.5
           is halfway through animation). This allows animation logic to be
           separate from timing logic.
        """
        # fix delta to between 0 and 1
        delta = max(0, min(delta, 1))
        bot_rgb_base = compute_color(self.id, self.hp,
                                     self.action)

        # default settings
        alpha_hack = 1
        bot_rgb = bot_rgb_base

        # if spawn, fade in
        normal_color = render_settings.normal_color
        if render_settings.bot_die_animation:
            if self.action == 'spawn':
                alpha_hack = delta
                bot_rgb = blend_colors(bot_rgb_base,
                                       normal_color, alpha_hack)
            # if dying, fade out
            elif self.hp_next <= 0:
                alpha_hack = 1 - delta
                bot_rgb = blend_colors(bot_rgb_base,
                                       normal_color, alpha_hack)

        x, y = self.location
        bot_size = self.renderer._blocksize
        self.animation_offset = (0, 0)
        arrow_fill = None

        # move animations
        if self.action == 'move' and self.target is not None:
            if (self.renderer._animations and
                    render_settings.bot_move_animation):
                # If normal move, start at bot location and move to next
                # location (note that first half of all move animations is the
                # same).
                if delta < 0.5 or self.location_next == self.target:
                    x, y = self.location
                    tx, ty = self.target
                # If we're halfway through this animation AND the movement
                # didn't succeed, reverse it (bounce back).
                else:
                    # starting where we wanted to go
                    x, y = self.target
                    # and ending where we are now
                    tx, ty = self.location
                dx = tx - x
                dy = ty - y
                off_x = dx * delta * self.renderer._blocksize
                off_y = dy * delta * self.renderer._blocksize
                self.animation_offset = (off_x, off_y)
            if render_settings.draw_movement_arrow:
                arrow_fill = 'lightblue'

        # attack animations
        elif self.action == 'attack' and self.target is not None:
            arrow_fill = 'orange'

        # guard animations
        elif self.action == 'guard':
            pass

        # suicide animations
        elif self.action == 'suicide':
            if (self.renderer._animations and
                    render_settings.bot_suicide_animation):
                # explosion animation
                # expand size (up to 1.5x original size)
                bot_size = self.renderer._blocksize * (1 + delta / 2)
                # color fade to yellow
                bot_rgb = blend_colors(bot_rgb, (1, 1, 0), 1 - delta)

        # DRAW ARROWS AND BORDER AND CIRCLE
        if self.renderer.show_arrows.get():
            if arrow_fill is not None and self.overlay is None:
                offset = (self.renderer._blocksize / 2,
                          self.renderer._blocksize / 2)
                self.overlay = self.renderer.draw_line(
                    self.location, self.target, layer=5, fill=arrow_fill,
                    offset=offset, width=3.0, arrow=Tkinter.LAST)
            if self.action == 'guard' and self.border is None:
                self.border = self.renderer.draw_grid_object(
                    self.location, shape=render_settings.bot_shape, layer=4,
                    outline=rgb_tuple_to_hex(
                        render_settings.color_guard_border),
                    width=2)
            if self.action == 'suicide' and self.circle is None:
                self.circle = self.renderer.draw_grid_object(
                    self.location, shape="circle", layer=4,
                    outline="yellow",
                    width=2)
        else:
            if self.overlay is not None:
                self.renderer.remove_object(self.overlay)
                self.overlay = None
            if self.border is not None:
                self.renderer.remove_object(self.border)
                self.border = None
            if self.circle is not None:
                self.renderer.remove_object(self.circle)
                self.circle = None

        # DRAW BOTS WITH HP
        bot_hex = rgb_to_hex(*bot_rgb)
        self.draw_bot((x, y), bot_hex, bot_size)
        if render_settings.bot_hp_animation:
            self.draw_bot_hp(delta, (x, y), bot_rgb, alpha_hack)
        else:
            self.draw_bot_hp(0, (x, y), bot_rgb, alpha_hack)

    def draw_bot(self, loc, color, size):
        x, y, rx, ry = self.renderer.grid_bbox(loc)
        ox, oy = self.animation_offset
        if self.square is None:
            self.square = self.renderer.draw_grid_object(
                self.location, shape=render_settings.bot_shape, layer=3,
                fill=color, width=0)
        self.renderer._win.itemconfig(self.square, fill=color)
        self.renderer._win.coords(self.square,
                                  (x + ox, y + oy, rx + ox, ry + oy))

    def draw_bot_hp(self, delta, loc, bot_color, alpha):
        x, y = self.renderer.grid_to_xy(loc)
        ox, oy = self.animation_offset
        tex_rgb = render_settings.text_color_bright \
            if self.hp > settings.robot_hp / 4 \
            else render_settings.text_color_dark
        tex_rgb = blend_colors(tex_rgb, bot_color, alpha)
        tex_hex = rgb_to_hex(*tex_rgb)
        val = int(self.hp * (1 - delta) + self.hp_next * delta)
        if self.text is None:
            self.text = self.renderer.draw_text(self.location, val, tex_hex)
        self.renderer._win.itemconfig(self.text, text=val, fill=tex_hex)
        self.renderer._win.coords(
            self.text,
            (x + ox +
                (self.renderer._blocksize -
                    self.renderer.cell_border_width) / 2,
             y + oy +
                (self.renderer._blocksize -
                    self.renderer.cell_border_width) / 2))

    def clear(self):
        self.renderer.remove_object(self.square)
        self.renderer.remove_object(self.border)
        self.renderer.remove_object(self.circle)
        self.renderer.remove_object(self.overlay)
        self.renderer.remove_object(self.text)
        self.square = None
        self.border = None
        self.circle = None
        self.overlay = None
        self.text = None
