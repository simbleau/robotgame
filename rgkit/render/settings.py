from rgkit.settings import AttrDict


settings = AttrDict({
    'FPS': 60,  # frames per second
    'turn_interval': 300,  # milliseconds per turn

    # colors
    'colors': [(0.49, 0.14, 0.14), (0.14, 0.14, 0.49)],
    'color_guard': None,  # (0.0, 0.14, 0.0),
    'color_guard_border': (0.0, 0.49, 0.0),
    # 'colors': [(0.9, 0, 0.2), (0, 0.9, 0.2)],
    'obstacle_color': (.2, .2, .2),
    'text_color': (0.6, 0.6, 0.6),  # for labelling rows/columns
    'text_color_dark': (0.1, 0.1, 0.1),  # HP color when bots are bright
    'text_color_bright': (0.9, 0.9, 0.9),  # HP color when bots are dark
    'normal_color': (.9, .9, .9),
    'highlight_color': (0.6, 0.6, 0.6),
    'target_color': (0.6, 0.6, 1),

    # highlighting
    'clear_highlight_between_turns': False,
    # 'clear_highlight_between_turns': True,
    'clear_highlight_target_between_turns': True,
    'highlight_cursor_blink': True,
    'rate_cursor_blink': 1000,
    # 'highlight_cursor_blink': True,
    'highlight_cursor_blink_interval': 0.5,

    'bot_shape': 'square',
    # 'bot_shape': 'circle',
    'draw_movement_arrow': True,
    # 'draw_movement_arrow': False,

    # animations (only enabled if -A is used)
    'bot_die_animation': True,
    'bot_move_animation': False,
    'bot_suicide_animation': False,
    'bot_hp_animation': False,
})
