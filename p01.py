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

        if 'spawn' in rg.loc_types(self.location):
            if rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')):
                print("move 5", game.robots[self.location])
                # print(rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')))
                return ['move', rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle'))[0]]
            elif rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                print("move 6", game.robots[self.location])
                return ['move', rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))[0]]


        directions = []
        nearby_enemies_count = 0
        nearby_enemies = []
        for loc, bot in game.robots.items():
            # print(str(bot))
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) <= 1:
                    nearby_enemies_count += 1
                    nearby_enemies += (loc, bot)
        #print(nearby_enemies)
        if nearby_enemies_count:
            if self.hp < 9 * nearby_enemies_count:
                return ['suicide']
            else:
                return ['attack', nearby_enemies[0]]

        t = rg.CENTER_POINT
        x = 99

        for loc, bot in game.robots.items():
            #print(game.robots.items())
            if bot.player_id != self.player_id and rg.wdist(loc, self.location) < x:
                #print(x)
                t = loc
                x = rg.wdist(loc, self.location)
        #print(rg.toward(self.location, t))

        if any(x in ['obstacle', 'invalid', 'spawn'] for x in rg.loc_types(rg.toward(self.location, rg.CENTER_POINT)))\
                and x < 19:
            print("move 1", game.robots[self.location])
            return ['move', (rg.toward(self.location, t))]

        elif any(x in ['obstacle', 'invalid', 'spawn'] for x in rg.loc_types(rg.toward(self.location, rg.CENTER_POINT))):
            print("move 2", game.robots[self.location])
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]

        elif rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')):
            print("move 3", game.robots[self.location])
            return ['move', choices(rg.locs_around(self.location, filter_out=('invalid', 'spawn', 'obstacle')))[0]]


        return ['guard']
