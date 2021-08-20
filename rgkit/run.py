#!/usr/bin/env python2
from __future__ import print_function

import argparse
from argparse import RawTextHelpFormatter
import ast
import copy
# import imp
import importlib
import inspect
import pkg_resources
import random
import os
import sys
import time

try:
    # imp.find_module('rgkit')
    importlib.import_module('rgkit')
except ImportError:
    # force rgkit to appear as a module when run from current directory
    from os.path import dirname, abspath
    current_dir = dirname(abspath(inspect.getfile(inspect.currentframe())))
    parent_dir = dirname(current_dir)
    sys.path.insert(0, parent_dir)

from rgkit.settings import settings as default_settings
from rgkit import game
from rgkit.game import Player


class Options(object):
    def __init__(self, map_filepath=None, headless=False, print_info=False,
                 animate_render=False, play_in_thread=False, curses=False,
                 game_seed=None, match_seeds=None, quiet=0, symmetric=True,
                 n_of_games=1, start=0):

        if map_filepath is None:
            map_filepath = os.path.join(os.path.dirname(__file__),
                                        'maps/default.py')
        self.animate_render = animate_render
        self.curses = curses
        self.game_seed = game_seed
        self.headless = headless
        self.map_filepath = map_filepath
        self.match_seeds = match_seeds
        self.n_of_games = n_of_games
        self.play_in_thread = play_in_thread
        self.print_info = print_info
        self.quiet = quiet
        self.start = start
        self.symmetric = symmetric

    def __eq__(self, other):
        return (self.animate_render == other.animate_render and
                self.curses == other.curses and
                self.game_seed == other.game_seed and
                self.headless == other.headless and
                self.map_filepath == other.map_filepath and
                self.match_seeds == other.match_seeds and
                self.n_of_games == other.n_of_games and
                self.play_in_thread == other.play_in_thread and
                self.print_info == other.print_info and
                self.quiet == other.quiet and
                self.start == other.start and
                self.symmetric == other.symmetric)


class Runner(object):
    def __init__(self, players=None, player_files=None, settings=None,
                 options=None, delta_callback=None):

        if settings is None:
            settings = Runner.default_settings()
        if options is None:
            options = Options()
        if players is None:
            players = []

        with open(options.map_filepath) as fp:
            self._map_data = ast.literal_eval(fp.read())
        self.settings = settings
        self.settings.init_map(self._map_data)
        # Players can only be initialized from file after initializing settings
        if player_files is not None:
            for player_file in player_files:
                players.append(self._make_player(player_file))
        self._players = players
        self._delta_callback = delta_callback
        self._names = []
        for player in players:
            self._names.append(player.name())
        self.options = options

        if Runner.is_multiprocessing_supported():
            import multiprocessing
            self._rgcurses_lock = multiprocessing.Lock()
        else:
            self._rgcurses_lock = None

    @staticmethod
    def from_robots(robots, settings=None, options=None,
                    delta_callback=None):

        players = []
        for robot in robots:
            players.append(Player(robot=robot))

        return Runner(players,
                      settings=settings, options=options,
                      delta_callback=delta_callback)

    @staticmethod
    def from_command_line_args(args):
        map_name = os.path.join(args.map)

        options = Options(animate_render=args.animate,
                          curses=args.curses,
                          game_seed=args.game_seed,
                          headless=args.headless,
                          map_filepath=map_name,
                          match_seeds=args.match_seeds,
                          n_of_games=args.count,
                          play_in_thread=args.play_in_thread,
                          print_info=not args.headless and args.quiet <= 2,
                          quiet=args.quiet,
                          start=args.start,
                          symmetric=not args.random)
        # TODO: generalize to N player files
        player_files = [args.player1, args.player2]
        return Runner(player_files=player_files, options=options)

    @staticmethod
    def get_function(function_path):
        """
        RMP: helper for getting the robot in a way that allows debugging.

        :param function_path: module.Robot
        :return: the robot
        """
        # https://stackoverflow.com/a/19393328
        import importlib
        module_name, func_name = function_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        f = getattr(module, func_name)
        return f

    @staticmethod
    def _make_player(file_name):
        """
        Changed this to load the robot in the usual way allowing debugging in Pycharm.

        :param file_name: local file containing the robot
        :return: the player.
        """
        module_name = '.'.join(file_name.split('.')[:-1])
        robot = Runner.get_function(f'{module_name}.Robot')()
        return game.Player(robot=robot)
        # try:
        #     return game.Player(file_name=file_name)
        # except IOError as msg:
        #     if pkg_resources.resource_exists('rgkit', file_name):
        #         bot_filename = pkg_resources.resource_filename('rgkit',
        #                                                        file_name)
        #         return game.Player(file_name=bot_filename)
        #     raise IOError(msg)

    @staticmethod
    def default_map():
        map_path = os.path.join(os.path.dirname(__file__), 'maps/default.py')
        return map_path

    @staticmethod
    def default_settings():
        return default_settings

    def game(self, record_actions=False, print_info=False):
        return game.Game(self._players, record_actions=record_actions,
                         print_info=print_info)

    def run(self):
        scores = []
        printed = []
        for i in range(self.options.start,
                       self.options.start + self.options.n_of_games):
            # A sequential, deterministic seed is used for each match that can
            # be overridden by user provided ones.
            match_seed = str(self.options.game_seed) + '-' + str(i)
            if self.options.match_seeds and i < len(self.options.match_seeds):
                match_seed = self.options.match_seeds[i]
            for player in self._players:
                player.load()
            result = self.play(match_seed)
            scores.append(result)
            printed.append('{0} - seed: {1}'.format(result, match_seed))
        if self.options.quiet < 4:
            Muter.unmute_all()
            if printed:
                print('\n'.join(printed))
        return scores

    def play(self, match_seed):
        if self.options.play_in_thread:
            g = game.ThreadedGame(self._players,
                                  print_info=self.options.print_info,
                                  record_actions=not self.options.headless,
                                  record_history=True,
                                  seed=match_seed,
                                  quiet=self.options.quiet,
                                  delta_callback=self._delta_callback,
                                  symmetric=self.options.symmetric)
        else:
            g = game.Game(self._players,
                          print_info=self.options.print_info,
                          record_actions=not self.options.headless,
                          record_history=True,
                          seed=match_seed,
                          quiet=self.options.quiet,
                          delta_callback=self._delta_callback,
                          symmetric=self.options.symmetric)

        if not self.options.headless and not self.options.curses:
            # only import render if we need to render the game;
            # this way, people who don't have tkinter can still
            # run headless
            from rgkit.render import render
            g.run_all_turns()
            # print "rendering %s animations" % ("with"
            #                                    if animate_render
            #                                    else "without")
            render.Render(g, self.options.animate_render, names=self._names)
        else:
            g.run_all_turns()

        # TODO: Displaying multiple games using curses is still a little bit
        # buggy but at least it doesn't completely screw up the state of the
        # terminal anymore.  The plan is to show each game sequentially.
        # Concurrency in run.py needs some more work before the bugs can be
        # fixed. Need to make sure nothing is printing when curses is running.
        if not self.options.headless and self.options.curses:
            from rgkit import rgcurses
            rgc = rgcurses.RGCurses(g, self._names)
            if self._rgcurses_lock:
                self._rgcurses_lock.acquire()
            rgc.run()
            if self._rgcurses_lock:
                self._rgcurses_lock.release()

        return g.get_scores()

    @staticmethod
    def is_multiprocessing_supported():
        is_multiprocessing_supported = True
        try:
            # imp.find_module('multiprocessing')
            importlib.import_module('multiprocessing')
        except ImportError:
            # the OS does not support it. See http://bugs.python.org/issue3770
            is_multiprocessing_supported = False

        return is_multiprocessing_supported


def run_single_from_command_line(args):
    return Runner.from_command_line_args(args).run()


def run_concurrently(args):
    import multiprocessing
    num_cpu = multiprocessing.cpu_count()
    (games_per_cpu, remainder) = divmod(args.count, num_cpu)
    data = []
    start = 0

    for _ in range(num_cpu):
        copy_args = copy.deepcopy(args)

        copy_args.start = start
        copy_args.count = games_per_cpu
        start += games_per_cpu
        # Distribute remainder of games evenly among CPUs
        if remainder > 0:
            copy_args.count += 1
            start += 1
            remainder -= 1

        data.append(copy_args)

    pool = multiprocessing.Pool(num_cpu)
    results = pool.map(run_single_from_command_line, data)
    return [score for scores in results for score in scores]


def get_arg_parser():
    parser = argparse.ArgumentParser(
        description="Robot game execution script.",
        formatter_class=RawTextHelpFormatter)
    parser.add_argument("player1",
                        help="File containing first robot class definition.")
    parser.add_argument("opponents", nargs="+",
                        help="File(s) containing opponent robots.")
    default_map = pkg_resources.resource_filename('rgkit', 'maps/default.py')
    parser.add_argument("-m", "--map",
                        help="User-specified map file.",
                        default=default_map)
    parser.add_argument("-c", "--count", type=int,
                        default=1,
                        help="Game count, default: 1, multithreading if >1")
    parser.add_argument("-A", "--animate", action="store_true",
                        default=False,
                        help="Enable animations in rendering.")
    # noinspection SpellCheckingInspection
    parser.add_argument(
        "-q", "--quiet", action="count", default=0, help="""Quiet execution.
-q : suppresses bot stdout
-qq: suppresses bot stdout and stderr
-qqq: suppresses all rgkit and bot output
-qqqq: final summary only""")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-H", "--headless", action="store_true",
                       default=False,
                       help="Disable rendering game output.")
    group.add_argument("-T", "--play-in-thread", action="store_true",
                       default=False,
                       help="Separate GUI thread from robot move calculations."
                       )
    group.add_argument("-C", "--curses", action="store_true",
                       default=False,
                       help="Display game in command line using curses.")
    parser.add_argument("--game-seed",
                        default=random.randint(0, default_settings.max_seed),
                        help="Appended with game count for per-match seeds.")
    parser.add_argument(
        "--match-seeds", nargs='*',
        help="Used for random seed of the first matches in order.")
    parser.add_argument("-r", "--random", action="store_true",
                        default=False,
                        help="Bots spawn randomly instead of symmetrically.")
    parser.add_argument("-M", "--heatmap", action="store_true",
                        default=False,
                        help="Print heatmap after playing a number of games.")
    parser.add_argument("-s", "--start", type=int, default=0,
                        help="Starting index of matches, useful for resuming.")
    # noinspection PyBroadException
    try:
        os.nice(0)
        parser.add_argument("--nice", type=int, default=5,
                            help="Value for os.nice to lower runner priority.")
    except Exception:
        # Not available on this platform, no need to add the option.
        pass

    return parser


class Muter:
    stdout = None
    stderr = None

    @staticmethod
    def mute_all():
        if Muter.stdout is None and Muter.stderr is None:
            Muter.stdout = sys.stdout
            sys.stdout = game.NullDevice()
            # Muter.stderr = sys.stderr
            # sys.stderr = game.NullDevice()

    @staticmethod
    def unmute_all():
        if Muter.stdout is not None:
            sys.stdout = Muter.stdout
            Muter.stdout = None

        if Muter.stderr is not None:
            sys.stderr = Muter.stderr
            Muter.stderr = None


def print_score_grid(scores, player1, player2, size):
    max_score = 50

    def to_grid(n):
        return int(round(float(n) / max_score * (size - 1)))

    def print_heat(n):
        if n > 9:
            sys.stdout.write(" +")
        else:
            sys.stdout.write(" " + str(n))

    grid = [[0 for _ in range(size)] for _ in range(size)]

    for s1, s2 in scores:
        grid[to_grid(s1)][to_grid(s2)] += 1

    p1won = sum(p1 > p2 for p1, p2 in scores)
    str1 = player1 + " : " + str(p1won)
    if len(str1) + 2 <= 2 * size - len(str1):
        str1 = " " + str1 + " "
        print("*" + str1 + "-" * (2 * size - len(str1)) + "*")
    else:
        print(str1)
        print("*" + "-" * (2 * size) + "*")

    for r in range(size - 1, -1, -1):
        sys.stdout.write("|")
        for c in range(size):
            if grid[r][c] == 0:
                if r == c:
                    sys.stdout.write(". ")
                else:
                    sys.stdout.write("  ")
            else:
                print_heat(grid[r][c])
        sys.stdout.write("|\n")

    p2won = sum(p2 > p1 for p1, p2 in scores)
    str2 = player2 + " : " + str(p2won)
    if len(str2) + 2 <= 2 * size - len(str2):
        str2 = " " + str2 + " "
        print("*" + "-" * (2 * size - len(str2)) + str2 + "*")
    else:
        print("*" + "-" * (2 * size) + "*")
        print(str2)


def main():
    args = get_arg_parser().parse_args()

    if "nice" in args:
        os.nice(args.nice)

    num_opponents = len(args.opponents)
    total_won, total_lost, total_draw, total_avg_score, total_diff = (
        0, 0, 0, (0, 0), 0)
    for opponent in args.opponents:
        args.player2 = opponent
        if args.quiet >= 3:
            Muter.mute_all()
        print('Game seed: {0}'.format(args.game_seed))
        if Runner.is_multiprocessing_supported() and args.count > 1:
            runner = run_concurrently
        else:
            runner = run_single_from_command_line

        start_time = time.time()
        scores = runner(args)
        total_time = time.time() - start_time

        print('{0:6.2f}s per game, {1} games, total {2:.0f}s'.format(
            total_time / args.count, args.count, total_time))
        if args.quiet >= 3:
            Muter.unmute_all()
        p1won = sum(p1 > p2 for p1, p2 in scores)
        p2won = sum(p2 > p1 for p1, p2 in scores)
        draw = args.count - p1won - p2won
        avg_score = [float(sum(x))/len(x) for x in zip(*scores)]
        diff = avg_score[0] - avg_score[1]
        if args.heatmap:
            print_score_grid(scores, args.player1, args.player2, 26)
        total_won += p1won
        total_lost += p2won
        total_draw += draw
        total_avg_score = (total_avg_score[0] + avg_score[0],
                           total_avg_score[1] + avg_score[1])
        total_diff += diff
        avg_score = list(map(int, avg_score))
        diff = int(diff)
        print('{:20} - {:15} - {:8} ({})'.format(
            os.path.basename(opponent)[:20], repr([p1won, p2won, draw]),
            repr(avg_score), diff))

    if num_opponents > 1:
        total_avg_score = list(map(int, (total_avg_score[0] / num_opponents,
                                         total_avg_score[1] / num_opponents)))
        total_diff = int(total_diff / num_opponents)
        win_rate = (100 * float(total_won + 0.5 * total_draw) /
                    (total_won + total_lost + total_draw))
        print('Overall: [{}, {}, {}] WR: {:<5.1f} Score: {} ({})'.format(
            total_won, total_lost, total_draw, win_rate, total_avg_score,
            total_diff))


if __name__ == '__main__':
    main()
