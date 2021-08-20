from rgkit.settings import settings


CENTER_POINT = (int(settings.board_size / 2), int(settings.board_size / 2))


def dist(p1, p2):
    return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5


def wdist(p1, p2):
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])


def memoize(f):
    """ Memoization decorator for a function taking a single argument """
    class MemoDict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret
    return MemoDict().__getitem__


def memodict(f):
    """Backward compatibility."""
    return memoize(f)


@memoize
def loc_types(loc):
    for i in range(2):
        if not 0 <= loc[i] < settings.board_size:
            return {'invalid'}

    types = {'normal'}
    if loc in settings.spawn_coordinates:
        types.add('spawn')
    if loc in settings.obstacles:
        types.add('obstacle')
    return types


@memoize
def _locs_around(loc):
    x, y = loc
    offsets = ((0, 1), (1, 0), (0, -1), (-1, 0))
    return [(x + dx, y + dy) for dx, dy in offsets]


def locs_around(loc, filter_out=None):
    filter_out = set(filter_out or [])
    return [a_loc for a_loc in _locs_around(loc)
            if len(filter_out & loc_types(a_loc)) == 0]


def _sign(x):
    return x and 1 if x > 0 else -1


def toward(curr, dest):
    if curr == dest:
        return curr

    x0, y0 = curr
    x, y = dest
    x_diff, y_diff = x - x0, y - y0

    move_y = (x0, y0 + _sign(y_diff))
    move_x = (x0 + _sign(x_diff), y0)

    if abs(y_diff) > abs(x_diff):
        if move_y not in settings.obstacles:
            return move_y
        else:
            return move_x
    else:
        if move_x not in settings.obstacles:
            return move_x
        else:
            return move_y
