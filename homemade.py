from rgkit import rg

"""
A bot which explores quadrant domination.
Authors: Matt Sterckx, Spencer Imbleau
"""


class Robot:
    def __init__(self):
        self.turn = -1
        self.last_act = None
        # TODO self.formation_n_bots should be based on dynamic input
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
        self.checkerboard = []
        x = 0
        y = -1
        direction = 'up'
        limit = 1
        while -9 < x < 9 and -9 < y < 9:
            self.checkerboard.append((x + 9, y + 9))
            if direction == 'up':
                if x + 2 > limit:
                    direction = 'right'
                    x += 1
                    y += 1
                else:
                    x += 2
            elif direction == 'right':
                if y + 2 > limit:
                    direction = 'down'
                    x -= 1
                    y += 1
                else:
                    y += 2
            elif direction == 'down':
                if abs(x - 2) > limit:
                    direction = 'left'
                    x -= 1
                    y -= 1
                else:
                    x -= 2
            else:
                if abs(y - 2) > limit:
                    direction = 'up'
                    limit += 1
                    y -= 2
                else:
                    y -= 2
        print(self.checkerboard)

    def submit_act(self, act):
        self.last_act = act
        return act

    def act(self, game):
        """
        This method determines the action of a robot for Robot Game.

        This method needs to return one of:
        ['move', (x, y)]
        ['attack', (x, y)]
        ['guard']
        ['suicide']
        """
        # TODO modularize this code into methods

        # If the turn has updated, run init code for the round
        if game.turn != self.turn:
            self.init_round(game)

        # Scan for enemies with a view length
        view_length = 2  # The amount of tiles away our robots will search for enemies
        seen_enemies = []
        for robot in game.robots:
            # Do not consider friendly robots
            if game.robots[robot]['player_id'] == self.player_id:
                continue
            # Attack bots that are close enough
            robot_loc = game.robots[robot]['location']
            dist = rg.dist(self.location, robot_loc)
            if dist <= view_length:
                seen_enemies.append(game.robots[robot])

        # Suicide routine
        # Reduce seen enemies to only those which can attack us
        potential_attackers = self.reduce_to_adjacent(seen_enemies)
        potential_damage_intake = len(potential_attackers) * 9  # Robots do 8-10 damage per turn. Avg is 9.
        # Suicide if we can die to the attackers around us
        if (self.hp - potential_damage_intake) <= 0:
            return self.submit_act(['suicide'])  # This deals 15 damage

        # Attack routine
        # If we are not suiciding, check if we should attack anyone.
        weakest_enemy = self.reduce_to_weakest(seen_enemies)
        if weakest_enemy is not None:
            weakest_loc = weakest_enemy['location']
            dist_to_weakest = rg.dist(self.location, weakest_loc)
            if dist_to_weakest == 1:
                return self.submit_act(['attack', weakest_loc])
            else:
                # move towards enemy
                return self.submit_act(self.move_to(weakest_loc))
        else:
            # move towards formation
            dest = self.formation_locations[self.robot_id]
            return self.submit_act(self.move_to(dest))

    def formation_routine(self):
        # TODO
        pass

    def attack_routine(self):
        # TODO
        pass

    def move_to(self, dest):
        # TODO Only continue if the last move-to worked
        #if len(self.last_act) == 2 and self.last_act[0] == 'move':
        #    pass

        # Path-find to formation
        last_state = self.maze[dest[0]][dest[1]]
        self.maze[dest[0]][dest[1]] = 0
        path = astar(self.maze, self.location, dest)
        self.maze[dest[0]][dest[1]] = last_state
        if path is None:
            # No path found - Guard (or potentially suicide here?)
            return ['guard']
        else:
            if len(path) > 1:
                path.pop(0)
            else:
                return ['guard']
            # Move towards formation
            step_to_take = path[0]  # The step in the path found to formation
            # Treat the step as an obstacle for future robots during pathfinding (avoid self-collisions)
            self.maze[step_to_take[0]][step_to_take[1]] = 1  # 1 = Obstacle
            # Submit move turn
            return ['move', step_to_take]

    def reduce_to_adjacent(self, robots):
        """
        Given an array of robots, return the robots immediately adjacent to self.
        """
        adjacent = []
        for robot in robots:
            dist = rg.dist(self.location, robot['location'])
            if dist <= 1:
                adjacent.append(robot)
        return adjacent

    def reduce_to_weakest(self, robots):
        """
        Given an array of robots, prioritizing health, then distance in the list.
        """
        weakest = None
        for robot in robots:
            if weakest is None:
                weakest = robot
                continue
            if robot['hp'] < weakest['hp']:
                weakest = robot
            elif robot['hp'] == weakest['hp']:
                dist_to_robot = rg.dist(self.location, robot['location'])
                dist_to_weakest = rg.dist(self.location, weakest['location'])
                if dist_to_robot < dist_to_weakest:
                    weakest = robot
        return weakest

    def init_round(self, game):
        # TODO assign formation locations to bots based on closest distance instead of randomly
        self.turn = game.turn
        player_bots = []
        for robot in game.robots:
            if 'robot_id' in game.robots[robot].keys():
                player_bots.append(game.robots[robot])
        # bots_per_quadrant = len(player_bots) / 4
        # q_bots = {0: [], 1: [], 2: [], 3: []}
        # for bot in player_bots:
        #     q_bots[find_nearest_quadrant(bot['location'])].append(bot)
        # for q in q_bots:
        #     while abs(bots_per_quadrant - len(q_bots[q])) > 1:
        #         if bots_per_quadrant > len(q_bots[q]):
        #             q_bots = move_from_closest_quadrant(q, q_bots, bots_per_quadrant,
        #                                                 self.formation_n_bots[q][min(7, int(bots_per_quadrant))])
        #         else:
        #             q_bots = move_to_closest_quadrant(q, q_bots, bots_per_quadrant)
        #
        self.maze = game_to_maze(game)
        self.formation_locations = {}
        # for q in q_bots:
        #     if len(q_bots[q]) > 0:
        #         locations = self.formation_n_bots[q][min(len(q_bots[q]), 7)]
        #         for b in range(len(q_bots[q])):
        #             if b < 7:
        #                 self.formation_locations[q_bots[q][b]['robot_id']] = locations[b]
        #             else:
        #                 self.formation_locations[q_bots[q][b]['robot_id']] = None
        for bot in range(len(player_bots)):
            self.formation_locations[player_bots[bot]['robot_id']] = self.checkerboard[bot]


def find_nearest_quadrant(loc):
    """
    Find the nearest quadrant to a location tuple (x,y)
    """
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


def move_from_closest_quadrant(q_move_to, quadrants, bots_per_quadrant, formation):
    """
    TODO Document
    """
    closest_bot = None
    closest_bot_distance = -1
    closest_bot_index = 0
    closest_bot_quadrant = 0
    for q in quadrants:
        if q != q_move_to and len(quadrants[q]) > bots_per_quadrant:
            for bot in range(len(quadrants[q])):
                for loc in formation:
                    if closest_bot is None or rg.dist(quadrants[q][bot]['location'], loc) < closest_bot_distance:
                        closest_bot = quadrants[q][bot]
                        closest_bot_distance = rg.dist(quadrants[q][bot]['location'], loc)
                        closest_bot_quadrant = q
                        closest_bot_index = bot
    quadrants[q_move_to].append(closest_bot)
    quadrants[closest_bot_quadrant].pop(closest_bot_index)
    return quadrants


def move_to_closest_quadrant(q_move_from, quadrants, bots_per_quadrant):
    # TODO improve logic to choose quadrant to move to
    for q in quadrants:
        if len(quadrants[q]) < bots_per_quadrant:
            quadrants[q].append(quadrants[q_move_from][0])
            quadrants[q_move_from].pop(0)
            return quadrants


def game_to_maze(game):
    """
    Convert the game to a maze digestible for the A* pathfinding algorithm
    """
    #        0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5  6  7  8
    maze = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # 0
            [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],  # 1
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],  # 2
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # 3
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # 4
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # 5
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # 6
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 7
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 8
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 9
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 10
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 11
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # 12
            [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # 13
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # 14
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # 15
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],  # 16
            [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1],  # 17
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]  # 18
    # Add robots to maze
    for robot in game.robots:
        loc = game.robots[robot]['location']
        x = loc[0]
        y = loc[1]
        maze[x][y] = 1
    # Return maze
    return maze

# A-STAR ALGORITHM STUFF BELOW


class Node:
    """
    A node class for A* Pathfinding
    """
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position


def astar(maze, start, end):
    """
    Returns a list of tuples as a path from the given start to the given end in the given maze
    """
    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Loop until you find the end
    recursion = 0
    while len(open_list) > 0 and recursion < 50:
        recursion += 1

        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Return reversed path

        # Generate children
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # Only check adjacent squares

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range
            if node_position[0] > (len(maze) - 1) or node_position[0] < 0 or node_position[1] > (len(maze[len(maze)-1]) -1) or node_position[1] < 0:
                continue

            # Make sure walkable terrain
            if maze[node_position[0]][node_position[1]] != 0:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)
        # Loop through children
        for child in children:
            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)
    else:
        return None
