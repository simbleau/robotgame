from rgkit import rg
from random import choices


class Robot:
    """
    This method needs to return one of:

    ['move', (x, y)]
    ['attack', (x, y)]
    ['guard']
    ['suicide']
    """
    val = ""

    # file = open("log.txt", 'w')
    def act(self, game):

        # print(str(self.location))
        # self.file.write(self.location)
        self.val = self.attack_suicide(game)
        if self.val is not None:
            return self.val

        self.val = self.move_from_spawn(game)
        if self.val is not None:
            return self.val
        self.val = self.move_towards_enemy(game)
        if self.val is not None:
            return self.val
        return ['guard']

    def move_from_spawn(self, game):
        if 'spawn' in rg.loc_types(self.location):
            if rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')):
                # print(rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')))
                return ['move', rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle'))[0]]
        return None

    def move_towards_enemy(self, game):
        t = rg.CENTER_POINT
        x = 99
        for loc, bot in game.robots.items():
            #print(game.robots.items())
            if bot.player_id != self.player_id and rg.wdist(loc, self.location) < x:
                #print(x)
                t = loc
                x = rg.wdist(loc, self.location)
        #print(rg.toward(self.location, t))
        if 'obstacle' not in rg.loc_types(rg.toward(self.location, t)) \
                and 'invalid' not in rg.loc_types(rg.toward(self.location, t)) \
                and 'spawn' not in rg.loc_types(rg.toward(self.location, t)) and x < 50:
            #print("moved", t, x)
            return ['move', (rg.toward(self.location, t))]

        elif rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')):
            return ['move', choices(rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')))[0]]

        return None

    def attack_suicide(self, game):
        for loc, bot in game.robots.items():
            # print(str(bot))
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    if self.hp < max(rg.settings.attack_range):
                        return ['suicide']
                    else:
                        return ['attack', loc]
        return None

    #def __del__(self):
        #print(self.val)
