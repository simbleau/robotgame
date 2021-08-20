from rgkit import rg


class Robot:
    """
    This method needs to return one of:

    ['move', (x, y)]
    ['attack', (x, y)]
    ['guard']
    ['suicide']
    """

    def act(self, game):
        return ['guard']
