from rgkit import rg


class Robot:
    def __init__(self):
        self.turn = -1
        self.formation_n_bots = {
                            0: {1: [(8, 8)],
                                2: [(8, 7), (7, 8)],
                                3: [(8, 6), (7, 7), (6, 8)],
                                4: [(8, 5), (7, 6), (6, 7), (5, 8)],
                                5: [(8, 4), (7, 5), (6, 6), (5, 7), (4, 8)],
                                6: [(8, 3), (7, 4), (6, 5), (5, 6), (4, 7), (3, 8)],
                                7: [(8, 2), (7, 3), (6, 4), (5, 5), (4, 6), (3, 7), (2, 8)]},
                            1: {1: [(10, 8)],
                                2: [(10, 7), (11, 8)],
                                3: [(10, 6), (11, 7), (12, 8)],
                                4: [(10, 5), (11, 6), (12, 7), (13, 8)],
                                5: [(10, 4), (11, 5), (12, 6), (13, 7), (14, 8)],
                                6: [(10, 3), (11, 4), (12, 5), (13, 6), (14, 7), (15, 8)],
                                7: [(10, 2), (11, 3), (12, 4), (13, 5), (14, 6), (15, 7), (16, 8)]},
                            2: {1: [(8, 10)],
                                2: [(7, 10), (8, 11)],
                                3: [(6, 10), (7, 11), (8, 12)],
                                4: [(5, 10), (6, 11), (7, 12), (8, 13)],
                                5: [(4, 10), (5, 11), (6, 12), (7, 13), (8, 14)],
                                6: [(3, 10), (4, 11), (5, 12), (6, 13), (7, 14), (8, 15)],
                                7: [(2, 10), (3, 11), (4, 12), (5, 13), (6, 14), (7, 15), (8, 16)]},
                            3: {1: [(10, 10)],
                                2: [(10, 11), (11, 10)],
                                3: [(10, 12), (11, 11), (12, 10)],
                                4: [(10, 13), (11, 12), (12, 11), (13, 10)],
                                5: [(10, 14), (11, 13), (12, 12), (13, 11), (14, 10)],
                                6: [(10, 15), (11, 14), (12, 13), (13, 12), (14, 11), (15, 10)],
                                7: [(10, 16), (11, 15), (12, 14), (13, 13), (14, 12), (15, 11), (16, 10)]}}
    """
    This method needs to return one of:

    ['move', (x, y)]
    ['attack', (x, y)]
    ['guard']
    ['suicide']
    """
    def act(self, game):
        if game.turn != self.turn:
            self.turn = game.turn
            self.formation_locations = {}
            self.taken_moves = set()
            q_bots = {0: [], 1: [], 2: [], 3: []}
            for robot in game.robots:
                if 'robot_id' in game.robots[robot].keys():
                    quadrant = find_nearest_quadrant(game.robots[robot]['location'])
                    q_bots[quadrant].append(game.robots[robot]['robot_id'])
            for q in q_bots:
                if len(q_bots[q]) > 0:
                    locations = self.formation_n_bots[q][min(len(q_bots[q]), 7)]
                    for b in range(len(q_bots[q])):
                        if b < 7:
                            self.formation_locations[q_bots[q][b]] = locations[b]
                        else:
                            self.formation_locations[q_bots[q][b]] = None
        if self.formation_locations[self.robot_id] is None:
            return ['suicide']
        if self.location == self.formation_locations[self.robot_id]:
            return ['guard']
        move_to_take = rg.toward(self.location, self.formation_locations[self.robot_id])
        if move_to_take in self.taken_moves:
            return ['guard']
        self.taken_moves.add(move_to_take)
        return ['move', move_to_take]


def find_nearest_quadrant(loc):
    if loc[0] < 9:
        if loc[1] < 9:
            return 0
        else:
            return 2
    else:
        if loc[1] < 9:
            return 1
        else:
            return 3
