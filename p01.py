from rgkit import rg

"""
A bot which explores quadrant domination.
Authors: Matt Sterckx, Spencer Imbleau
"""

"""
TODO - Average the quadrant sizes during turns.

Pseudo code below.

avg = find_quadrant_avg();
for quadrant in quadrants:
    quadrant_total = find_quadrant_total(quadrant)
    quadrant_difference = avg - quadrant_total # will be positive if there are less than avg
    while (quadrant_difference > 1):
        # this quadrant has not enough bots
        bot_to_move = find_closest_ally(quadrant) # do not accept allies from this quadrant
        move(bot_to_move, quadrant)
        quadrant_difference -= 1
"""


class Robot:
    def __init__(self):
        self.turn = -1
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

        # TODO put this in a "round_init()" method
        # If the turn has updated, run init code for the round
        if game.turn != self.turn:
            self.turn = game.turn
            player_bots = []
            for robot in game.robots:
                if 'robot_id' in game.robots[robot].keys():
                    player_bots.append(game.robots[robot])
            bots_per_quadrant = len(player_bots) / 4
            q_bots = {0: [], 1: [], 2: [], 3: []}
            for bot in player_bots:
                q_bots[find_nearest_quadrant(bot['location'])].append(bot)
            for q in q_bots:
                while bots_per_quadrant - len(q_bots[q]) > 1:
                    q_bots = move_closest_bot(q, q_bots, bots_per_quadrant, self.formation_n_bots[q][min(7, int(bots_per_quadrant))])

            self.maze = game_to_maze(game)
            self.formation_locations = {}
            for q in q_bots:
                if len(q_bots[q]) > 0:
                    locations = self.formation_n_bots[q][min(len(q_bots[q]), 7)]
                    for b in range(len(q_bots[q])):
                        if b < 7:
                            self.formation_locations[q_bots[q][b]['robot_id']] = locations[b]
                        else:
                            self.formation_locations[q_bots[q][b]['robot_id']] = None

        # TODO better attack routine and rules
        # If no formation is found for this bot, suicide
        if self.formation_locations[self.robot_id] is None:
            return ['suicide']
        # Determine when to attack enemies
        for robot in game.robots:
            # Do not attack friendly robots
            if game.robots[robot]['player_id'] == self.player_id:
                continue
            # Attack bots that are close enough
            robot_loc = game.robots[robot]['location']
            dist = rg.dist(self.location, robot_loc)
            if dist == 1:
                return ["attack", robot_loc]

        # TODO better guard logic
        if self.location == self.formation_locations[self.robot_id]:
            return ['guard']

        # TODO better logic on *when* to path-find
        # Path-find to formation
        dest = self.formation_locations[self.robot_id]
        last_state = self.maze[dest[0]][dest[1]]
        self.maze[dest[0]][dest[1]] = 0
        path = astar(self.maze, self.location, self.formation_locations[self.robot_id])
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

    def formation_routine(self):
        # TODO
        pass

    def attack_routine(self):
        # TODO
        pass

    def init_round(self):
        # TODO
        pass


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


def move_closest_bot(q_move_to, quadrants, bots_per_quadrant, formation):
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
    while len(open_list) > 0:
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
