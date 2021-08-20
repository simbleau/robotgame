from rgkit.render.settings import settings as render_settings
from rgkit.render.utils import rgb_to_hex, blend_colors, compute_color


class HighlightSprite(object):
    def __init__(self, loc, target, render):
        self.location = loc
        self.target = target
        self.renderer = render
        self.hlt_square = None
        self.target_square = None

    def get_bot_color(self, loc):
        display_turn = self.renderer.current_turn_int()
        display_state = self.renderer._game.get_state(display_turn)
        if display_state.is_robot(loc):
            robot = display_state.robots[loc]
            bot_action = self.renderer._game.get_actions_on_turn(
                display_turn)[loc]['name']
            robot_color = compute_color(robot.player_id, robot.hp,
                                        bot_action)
            return robot_color
        return None

    def get_mixed_color(self, color, loc):
        bot_color = self.get_bot_color(loc)
        if bot_color is not None:
            color = blend_colors(color, bot_color, 0.7)
        return rgb_to_hex(*color)

    def clear_target_square(self):
        self.renderer.remove_object(self.target_square)
        self.target_square = None

    def clear(self):
        self.renderer.remove_object(self.hlt_square)
        self.hlt_square = None
        self.clear_target_square()

    def animate(self, delta=0):
        if render_settings.highlight_cursor_blink:
            if not delta < render_settings.highlight_cursor_blink_interval:
                self.clear()
                return

        if self.location is not None:
            if self.hlt_square is None:
                color = render_settings.highlight_color
                color = self.get_mixed_color(color, self.location)
                self.hlt_square = self.renderer.draw_grid_object(
                    self.location, fill=color, layer=3, width=0)
            if not self.renderer.show_arrows.get():
                if self.target is not None and self.target_square is None:
                    color = render_settings.target_color
                    color = self.get_mixed_color(color, self.target)
                    self.target_square = self.renderer.draw_grid_object(
                        self.target, fill=color, layer=3, width=0)
            else:
                self.clear_target_square()
