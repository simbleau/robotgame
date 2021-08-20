import curses as cs
from rgkit.settings import settings


class RGCurses(object):
    def __init__(self, game_inst, names):
        self._game = game_inst
        self._names = names
        self._turn = 0
        self._done = False
        self._paused = False
        self._selected = [settings.board_size // 2, settings.board_size // 2]

        # *** Edit settings below this line ***

        self._manual_text = """Exit            q, <esc>
Play/Pause      p, <space>
Next turn       j
Prev turn       k
Rewind turns    r
Cursor up       w, <up>
Cursor left     a, <left>
Cursor down     s, <down>
Cursor right    d, <right>"""

        self._turn_delay = 250

        # Positions
        self._game_grid_pos = (1, 2)
        self._score_pos = (19, 41)
        self._final_score_pos = (1, 41)
        self._manual_pos = (3, 41)
        self._cell_info_pos = (13, 41)
        self._turn_pos = (18, 41)

        # Keybindings
        self._exit_keys = [ord('q'), 27]
        self._pause_keys = [ord('p'), ord(' ')]
        self._step_keys = [ord('j')]
        self._back_keys = [ord('k')]
        self._rewind_keys = [ord('r')]
        self._up_keys = [ord('w'), cs.KEY_UP]
        self._left_keys = [ord('a'), cs.KEY_LEFT]
        self._down_keys = [ord('s'), cs.KEY_DOWN]
        self._right_keys = [ord('d'), cs.KEY_RIGHT]

    def _init_curses(self):

        # Colors and attributes

        colors_empty = 1
        colors_obstacle = 2
        colors_bot1 = 3
        colors_bot2 = 4
        # Selected
        colors_empty_s = 5
        colors_obstacle_s = 6
        colors_bot1_s = 7
        colors_bot2_s = 8
        # Other
        colors_text = 9

        # (Color pair, Foreground, Background)
        cs.init_pair(colors_empty, cs.COLOR_WHITE, cs.COLOR_BLACK)
        cs.init_pair(colors_obstacle, cs.COLOR_BLACK, cs.COLOR_WHITE)
        cs.init_pair(colors_bot1, cs.COLOR_WHITE, cs.COLOR_RED)
        cs.init_pair(colors_bot2, cs.COLOR_WHITE, cs.COLOR_BLUE)
        cs.init_pair(colors_empty_s, cs.COLOR_WHITE, cs.COLOR_YELLOW)
        cs.init_pair(colors_obstacle_s, cs.COLOR_BLACK, cs.COLOR_YELLOW)
        cs.init_pair(colors_bot1_s, cs.COLOR_WHITE, cs.COLOR_MAGENTA)
        cs.init_pair(colors_bot2_s, cs.COLOR_WHITE, cs.COLOR_CYAN)
        cs.init_pair(colors_text, cs.COLOR_WHITE, cs.COLOR_BLACK)

        # Attributes
        attr_empty = cs.A_NORMAL
        attr_obstacle = cs.A_NORMAL
        attr_bot1 = cs.A_BOLD
        attr_bot2 = cs.A_BOLD
        attr_empty_s = cs.A_NORMAL
        attr_obstacle_s = cs.A_NORMAL
        attr_bot1_s = cs.A_BOLD
        attr_bot2_s = cs.A_BOLD
        attr_text = cs.A_NORMAL

        # **** Do not edit settings below this line ***

        cs.curs_set(0)
        self._attr_empty = cs.color_pair(colors_empty) | attr_empty
        self._attr_obstacle = cs.color_pair(colors_obstacle) | attr_obstacle
        self._attr_bot1 = cs.color_pair(colors_bot1) | attr_bot1
        self._attr_bot2 = cs.color_pair(colors_bot2) | attr_bot2
        self._attr_empty_s = cs.color_pair(colors_empty_s) | attr_empty_s
        self._attr_obstacle_s = cs.color_pair(colors_obstacle_s) \
            | attr_obstacle_s
        self._attr_bot1_s = cs.color_pair(colors_bot1_s) | attr_bot1_s
        self._attr_bot2_s = cs.color_pair(colors_bot2_s) | attr_bot2_s
        self._attr_text = cs.color_pair(colors_text) | attr_text

    def run(self):
        # TODO: handle off-screen draws gracefully, instead of try-catch
        # noinspection PyBroadException
        try:
            cs.wrapper(self._main)
        except Exception:
            pass

    @staticmethod
    def _grid_num_to_str(n):
        if -9 <= n <= -1:
            return str(n)
        elif 0 <= n <= 9:
            return ' ' + str(n)
        elif 10 <= n <= 99:
            return str(n)
        else:
            return 'EE'     # Error! number too big for one cell

    def _draw_grid_empty(self, r, c):
        if [r, c] == self._selected:
            attr = self._attr_empty_s
        else:
            attr = self._attr_empty
        r = self._game_grid_pos[0] + 2 * r
        c = self._game_grid_pos[1] + c
        self._standard_screen.addstr(c, r, '  ', attr)

    def _draw_grid_obstacle(self, r, c):
        if [r, c] == self._selected:
            attr = self._attr_obstacle_s
        else:
            attr = self._attr_obstacle
        if r == 0 and c % 2 == 0:
            show_str = self._grid_num_to_str(c)
        elif c == 0 and r % 2 == 0:
            show_str = self._grid_num_to_str(r)
        else:
            show_str = '  '
        r = self._game_grid_pos[0] + 2 * r
        c = self._game_grid_pos[1] + c
        self._standard_screen.addstr(c, r, show_str, attr)

    def _draw_grid_bot1(self, r, c, hp):
        if [r, c] == self._selected:
            attr = self._attr_bot1_s
        else:
            attr = self._attr_bot1
        r = self._game_grid_pos[0] + 2 * r
        c = self._game_grid_pos[1] + c
        show_str = self._grid_num_to_str(hp)
        self._standard_screen.addstr(c, r, show_str, attr)

    def _draw_grid_bot2(self, r, c, hp):
        if [r, c] == self._selected:
            attr = self._attr_bot2_s
        else:
            attr = self._attr_bot2
        r = self._game_grid_pos[0] + 2 * r
        c = self._game_grid_pos[1] + c
        show_str = self._grid_num_to_str(hp)
        self._standard_screen.addstr(c, r, show_str, attr)

    def _draw_game_grid(self):
        state = self._game.get_state(self._turn)
        for r in range(settings.board_size):
            for c in range(settings.board_size):
                if (r, c) in settings.obstacles:
                    self._draw_grid_obstacle(r, c)
                elif state.is_robot((r, c)):
                    robot = state.robots[(r, c)]
                    if robot.player_id == 0:
                        self._draw_grid_bot1(r, c, robot.hp)
                    else:
                        self._draw_grid_bot2(r, c, robot.hp)
                else:
                    self._draw_grid_empty(r, c)

    def _draw_manual(self):
        r, c = self._manual_pos
        for line in self._manual_text.split("\n"):
            self._standard_screen.addstr(r, c, line, self._attr_text)
            r += 1

    def _draw_cell_info(self):
        state = self._game.get_state(self._turn)
        actions = self._game.get_actions_on_turn(self._turn)
        r, c = self._selected
        s = "Selected: " + str((r, c))
        if (r, c) in settings.obstacles:
            s += "\nObstacle"
        elif state.is_robot((r, c)):
            robot = state.robots[(r, c)]
            s += "\nRobot:  " + self._names[robot.player_id]
            s += "\nHP:     " + str(robot.hp)
            s += "\nAction: " + actions[(r, c)]['name']
            if actions[(r, c)]['name'] in ['move', 'attack']:
                s += " " + str(actions[(r, c)]['target'])
        else:
            s += "\nEmpty"
        r, c = self._cell_info_pos
        for line in s.split("\n"):
            self._standard_screen.addstr(r, c, line, self._attr_text)
            r += 1

    def _draw_score(self):
        state = self._game.get_state(self._turn)
        score = [0, 0]
        for bot in state.robots.values():
            score[bot.player_id] += 1
        r, c = self._score_pos
        if score[0] >= score[1]:
            s = self._names[0]
            self._standard_screen.addstr(r, c, s, self._attr_bot1)
            c += len(s)
            s = " " + str(score[0]) + " : " + str(score[1]) + " "
            self._standard_screen.addstr(r, c, s, self._attr_text)
            c += len(s)
            s = self._names[1]
            self._standard_screen.addstr(r, c, s, self._attr_bot2)
        else:
            s = self._names[1]
            self._standard_screen.addstr(r, c, s, self._attr_bot2)
            c += len(s)
            s = " " + str(score[1]) + " : " + str(score[0]) + " "
            self._standard_screen.addstr(r, c, s, self._attr_text)
            c += len(s)
            s = self._names[0]
            self._standard_screen.addstr(r, c, s, self._attr_bot1)

    def _draw_final_score(self):
        state = self._game.get_state(settings.max_turns)
        score = [0, 0]
        for bot in state.robots.values():
            score[bot.player_id] += 1
        r, c = self._final_score_pos
        if score[0] > score[1]:
            s = self._names[0]
            self._standard_screen.addstr(r, c, s, self._attr_bot1)
            c += len(s)
            s = " won: " + str(score[0]) + " : " + str(score[1])
            self._standard_screen.addstr(r, c, s, self._attr_text)
        elif score[1] > score[0]:
            s = self._names[1]
            self._standard_screen.addstr(r, c, s, self._attr_bot2)
            c += len(s)
            s = " won: " + str(score[1]) + " : " + str(score[0])
            self._standard_screen.addstr(r, c, s, self._attr_text)
        else:
            s = "Tie game: " + str(score[0]) + " : " + str(score[1])
            self._standard_screen.addstr(r, c, s, self._attr_text)

    def _draw_turn(self):
        r, c = self._turn_pos
        s = "Turn: " + str(self._turn)
        self._standard_screen.addstr(r, c, s, self._attr_text)

    def _draw_screen(self):
        self._draw_game_grid()
        self._draw_manual()
        self._draw_cell_info()
        self._draw_score()
        self._draw_final_score()
        self._draw_turn()

    def _increase_turn(self):
        if self._turn < settings.max_turns:
            self._turn += 1
            return True
        else:
            return False

    def _decrease_turn(self):
        if self._turn > 0:
            self._turn -= 1
            return True
        else:
            return False

    def _move_selected_up(self):
        self._selected[1] = max(self._selected[1] - 1, 0)

    def _move_selected_left(self):
        self._selected[0] = max(self._selected[0] - 1, 0)

    def _move_selected_down(self):
        self._selected[1] = min(self._selected[1] + 1,
                                settings.board_size - 1)

    def _move_selected_right(self):
        self._selected[0] = min(self._selected[0] + 1,
                                settings.board_size - 1)

    def _handle_key(self, key):
        if key in self._pause_keys:
            self._paused = not self._paused
        elif key in self._exit_keys:
            self._done = True
        elif key in self._step_keys:
            self._increase_turn()
            self._paused = True
        elif key in self._back_keys:
            self._decrease_turn()
            self._paused = True
        elif key in self._rewind_keys:
            self._turn = 0
            self._paused = True
        elif key in self._up_keys:
            self._move_selected_up()
            self._paused = True
        elif key in self._left_keys:
            self._move_selected_left()
            self._paused = True
        elif key in self._down_keys:
            self._move_selected_down()
            self._paused = True
        elif key in self._right_keys:
            self._move_selected_right()
            self._paused = True

    def _main_loop(self):
        self._done = False
        self._turn = 0
        while not self._done:
            if self._paused:
                # When paused, block until a key is pressed
                self._standard_screen.timeout(-1)
                c = self._standard_screen.getch()
                self._handle_key(c)
            else:
                # When playing, block until a key a pressed or time to
                # advance to the next turn. Since it unblocks on ANY key press,
                # pressing random keys when the game is playing will prevent
                # it from advancing to the next turn for a short while. A
                # solution might be to use the time module to only wait the
                # time difference from the last turn advance, but this may
                # introduce cross-platform issues due to inconsistencies in
                # time resolution.
                self._standard_screen.timeout(self._turn_delay)
                c = self._standard_screen.getch()
                if c == cs.ERR:
                    if not self._increase_turn():
                        self._paused = True
                else:
                    self._handle_key(c)
            # TODO: Not every cell need to be cleared. Clearing everything
            #       creates flicker.
            self._standard_screen.clear()
            self._draw_screen()
            self._standard_screen.refresh()

    def _main(self, standard_screen):
        self._init_curses()
        self._standard_screen = standard_screen

        # Start loop
        self._main_loop()
