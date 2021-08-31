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
        # if we're in the center, stay put
        if self.location == rg.CENTER_POINT:
            return ['guard']

        # if there are enemies around, attack them
        for loc, bot in game.robots.items():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]

        # move toward the center
        return ['move', rg.toward(self.location, rg.CENTER_POINT)]
