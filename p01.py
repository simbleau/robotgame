# Dulladob 0.1 by Camelot Chess
# Modified and improved by Spencer Imbleau and Matthias Sterckx
# http://robotgame.net/viewrobot/7641

from rgkit import rg
import math

spawn_param = 8  # which turn to we begin bouncing?

suicide_param = 6  # when to blow ourselves up (param*surrounders>hp)?
suicide_fear_param = 6  # which to fear enemies blowing up?

staying_still_bonus = 0.34  # points for staying put
best_center_distance_param = 6  # ideal distance from the center
best_center_distance_weight = 1.01  # points lost for every square off
spawn_weight = 0.34  # points lost being spawn; multiplied by turns since death
adjacent_robot_penalty = 1  # NO NEED TO CHANGE - points lost for adjacent robots
adjacent_friendly_penalty = 0.51  # NO NEED TO CHANGE - points lost for adjacent robots
main_axis_weight = 0.5

# parameters controlling how much hp we need to pin an enemy to spawn. Arguably
# should depend on their hp, and/or happen before running, particularly on first
# turn.
hp_to_pin = {0: 6, 1: 11, 2: 51, 3: 51, 4: 51, 5: 51, 6: 51, 7: 51, 8: 51, 9: 51, 10: 51}

quadrant_centers = {0: (5, 5), 1: (13, 5), 2: (5, 13), 3: (13, 13)}
worst_ratio_quadrant = 0

# Strong hunt the weak variable
weakest_enemy_hp = 30
strong_hunt_the_weak_hp_limit = 30

#Empty Space
empty_score_hp = 25

canonical_spawn_locs = []
for spawn_x in range(10):
    for spawn_y in range(10):
        if 'spawn' in rg.loc_types((spawn_x, spawn_y)):
            canonical_spawn_locs.append((spawn_x, spawn_y))
# TTD:
# - vary some priorities

one_robots = []
two_robots = []
moves_to = {}
illegals_global = set()
last_turn = -1


def urgency(bot1):
    return 100000 * rg.dist(bot1.location, rg.CENTER_POINT) + 100 * bot1.hp + bot1.location[0]


def greater(bot1, bot2):
    if urgency(bot1) > urgency(bot2):
        return 1
    #    if urgency(bot2) > urgency(bot1):
    return 0
    # deliberately runs off the edge; this should be impossible.


def valid(move):
    types = rg.loc_types(move)
    if 'invalid' in types or 'obstacle' in types:
        return 0
    return 1


def not_spawn(move):
    if 'spawn' in rg.loc_types(move):
        return 0
    return 1


def spawn(move):
    return 1 - not_spawn(move)


def surrounded_spawn(move):
    if len(rg.locs_around(move, filter_out=('obstacle', 'invalid', 'spawn'))) > 0:
        return 0
    return 1


def equal(bot1, bot2):
    if bot1.location == bot2.location:
        return 1
    return 0


def surrounders(this_robot, game, loc):
    number_found = 0
    for loc2 in rg.locs_around(loc):
        if loc2 in game.robots and game.robots[loc2].player_id != this_robot.player_id:
            number_found += 1
    return number_found


def distance_from_spawn(square):
    # canonise the square
    canonical_x = square[0]
    canonical_y = square[1]
    if canonical_x > 9:
        canonical_x = 18 - canonical_x
    if canonical_y > 9:
        canonical_y = 18 - canonical_y
    if canonical_x > canonical_y:
        canonical_square = (canonical_y, canonical_x)
    else:
        canonical_square = (canonical_x, canonical_y)
    distance = 10
    for loc in canonical_spawn_locs:
        if rg.wdist(loc, canonical_square) < distance:
            distance = rg.wdist(loc, canonical_square)
    return distance


def move_towards_if_no_ally(loc, dest, game, illegals):
    xmove = towardsx_if_not_spawn(loc, dest)
    ymove = towardsy_if_not_spawn(loc, dest)
    if xmove != 'no_move' and not (xmove in illegals) and not (xmove in game.robots):
        return xmove
    if ymove != 'no_move' and not (ymove in illegals) and not (ymove in game.robots):
        return ymove
    return 'no_action'


def towardsy_if_not_spawn(loc, dest):
    tentative_move = (loc[0], loc[1] + 1)
    if dest[1] < loc[1]:
        tentative_move = (loc[0], loc[1] - 1)
    if dest[1] != loc[1] and valid(tentative_move) and (not_spawn(tentative_move) or spawn(loc)):
        return tentative_move
    return 'no_move'


def towardsx_if_not_spawn(loc, dest):
    tentative_move = (loc[0] + 1, loc[1])
    if dest[0] < loc[0]:
        tentative_move = (loc[0] - 1, loc[1])
    if dest[0] != loc[0] and valid(tentative_move) and (not_spawn(tentative_move) or spawn(loc)):
        return tentative_move
    return 'no_move'


def towardy(loc, dest):
    tentative_move = (loc[0], loc[1] + 1)
    if dest[1] < loc[1]:
        tentative_move = (loc[0], loc[1] - 1)
    if dest[1] != loc[1] and valid(tentative_move):
        return tentative_move
    return 'no_move'


def towardx(loc, dest):
    tentative_move = (loc[0] + 1, loc[1])
    if dest[0] < loc[0]:
        tentative_move = (loc[0] - 1, loc[1])
    if dest[0] != loc[0] and valid(tentative_move):
        return tentative_move
    return 'no_move'


def move_towards_either_axis(loc, dest, turn):
    targetx = towardsx_if_not_spawn(loc, dest)
    targety = towardsy_if_not_spawn(loc, dest)
    if targetx == 'no_move':
        return targety
    if targety == 'no_move':
        return targetx
    if turn % 2 == 0:
        return targetx
    else:
        return targety


def destruct_if_doomed_us(this_robot, game, illegals):
    if this_robot.location in illegals or surrounders(this_robot, game,
                                                      this_robot.location) * suicide_param <= this_robot.hp:
        return 'no_action'
    return ['suicide']


def destruct_if_doomed_enemy(this_robot, game):
    if surrounders(this_robot, game, this_robot.location) * suicide_fear_param > this_robot.hp:
        return ['suicide']
    return 'no_action'


def attack_moving_enemy(this_robot, game, illegals):
    if this_robot.location in illegals:
        return 'no_action'
    square_dictionary = {}
    for square in rg.locs_around(this_robot.location):
        square_dictionary[square] = 0
        if square in game.robots:
            square_dictionary[square] -= 40  # don't fire if our robot is there, they probably won't move there
    for bot in two_robots:
        if bot.player_id != this_robot.player_id:
            loc = bot.location
            targetx = towardx(this_robot.location, loc)
            targety = towardy(this_robot.location, loc)
            if targetx != 'no_move':
                square_dictionary[targetx] += 70 - bot.hp - rg.dist(rg.CENTER_POINT, targetx)
            if targety != 'no_move':
                square_dictionary[targety] += 70 - bot.hp - rg.dist(rg.CENTER_POINT, targety)
    best_score = 0
    best_move = 'no_action'
    for square in rg.locs_around(this_robot.location):
        if square_dictionary[square] > best_score:
            best_score = square_dictionary[square]
            best_move = ['attack', square]
    return best_move


def attack_if_possible(this_robot, illegals):
    if this_robot.location in illegals:
        return 'no_action'
    besthp = 1000
    bestloc = 'none'
    for bot in one_robots:
        if bot.player_id != this_robot.player_id:
            if bot.hp < besthp:
                besthp = bot.hp
                bestloc = bot.location
    if besthp < 1000:
        return ['attack', bestloc]
    return 'no_action'


def strong_hunt_the_weak(this_robot, game, illegals):
    if this_robot.hp < strong_hunt_the_weak_hp_limit:
        return 'no_action'
    best_move = 'no_action'
    weakest_enemy = weakest_enemy_hp
    for bot in one_robots:
        if bot.player_id != this_robot.player_id:
            if bot.hp < weakest_enemy:
                weakest_enemy = bot.hp
                if bot.hp <= 5 and not (bot.location in illegals) and (
                        not surrounders(this_robot, game, bot.location) > 1):
                    best_move = ['move', bot.location]
                    weakest_enemy = bot.hp
                elif this_robot.location not in illegals:
                    best_move = ['attack', bot.location]
                    weakest_enemy = bot.hp
    for bot in two_robots:
        if bot.player_id != this_robot.player_id and bot.hp < weakest_enemy_hp:
            targetx = towardsx_if_not_spawn(this_robot.location, bot.location)
            targety = towardsy_if_not_spawn(this_robot.location, bot.location)
            if targetx != 'no_move' and not (targetx in illegals or surrounders(this_robot, game, targetx) > 1):
                best_move = ['move', targetx]
                weakest_enemy = bot.hp
            if targety != 'no_move' and not (targety in illegals or surrounders(this_robot, game, targety) > 1):
                if targetx == 'no_move' or rg.dist(targetx, rg.CENTER_POINT) > rg.dist(targety, rg.CENTER_POINT):
                    best_move = ['move', targety]
                    weakest_enemy = bot.hp
    return best_move


def safe(this_robot, loc, game):
    turns_left = (10 - game.turn) % 10
    if turns_left <= 2 and spawn(loc):
        return 0
    for bot in one_robots:
        if loc == bot.location and bot.player_id != this_robot.player_id:
            return 0
    for bot in two_robots:
        if bot.player_id != this_robot.player_id and rg.wdist(loc, bot.location) == 1:
            return 0
    return 1


def scared(this_robot, game):
    #################################################################
    # Added by Spencer, Matt - Never stay in spawn for the first turn
    if (10 - game.turn) % 10 < 3 and 'spawn' in rg.loc_types(this_robot.location):
        return 1
    #################################################################
    num_surrounders = 0
    for bot in one_robots:
        if bot.player_id != this_robot.player_id:
            num_surrounders += 1
            if destruct_if_doomed_enemy(bot, game) != 'no_action' or (
                    bot.hp > this_robot.hp and (surrounders(bot, game, bot.location) == 1 or this_robot.hp < 16)):
                return 1
    if num_surrounders > 1:
        return 1
    return 0


def run_if_scared_and_safe(this_robot, game, illegals):
    global moves_to
    if not scared(this_robot, game):
        return 'no_action'
    best_distance = 1000
    move = 'no_action'

    # # Make a list of scared friendly locations
    # friendly_scared = set()
    # for robot in game.robots:
    #     if scared(game.robots[robot], game):
    #         friendly_scared.add(robot)
    # print(friendly_scared)

    for loc in rg.locs_around(this_robot.location, filter_out=('obstacle', 'invalid', 'spawn')):
        # check if friendlies are scared. filter those out too
        if not (loc in illegals) and (loc not in moves_to or moves_to[loc] != this_robot.location) and safe(this_robot,
                                                                                                            loc,
                                                                                                            game) == 1 and rg.dist(
            loc, rg.CENTER_POINT) < best_distance:
            best_distance = rg.dist(loc, rg.CENTER_POINT)
            move = ['move', loc]
    return move


def empty_score(this_robot, loc, game):
    score = 0
    if this_robot.hp > empty_score_hp:
        score -= abs(rg.dist(loc, rg.CENTER_POINT) - best_center_distance_param) * best_center_distance_weight
    else:
        score -= rg.dist(loc, rg.CENTER_POINT) * best_center_distance_weight
    for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
        if loc2 in game.robots:
            if game.robots[loc2].player_id != this_robot.player_id:
                score -= adjacent_robot_penalty
            else:
                score -= adjacent_friendly_penalty
    # if we are trying to run away from spawn, non-spawn adjacent squares with no enemies by them are good, because we need to move
    if spawn(loc) & game.turn < 91:
        for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
            clear_square = 1
            for loc3 in rg.locs_around(loc2, filter_out=('obstacle', 'invalid', 'spawn')):
                if loc3 in game.robots and game.robots[loc3].player_id != this_robot.player_id:
                    clear_square = 0
            score += ((game.turn + 1) % 10) * spawn_weight * clear_square / 2
    if spawn(loc) & game.turn < 91:
        score -= ((game.turn + 1) % 10) * spawn_weight
    if surrounded_spawn(loc) & game.turn < 91:
        score -= (game.turn % 10) * spawn_weight
    return score


def find_empty_space(this_robot, game, illegals):
    global moves_to
    loc = this_robot.location
    best_score = empty_score(this_robot, loc, game) + staying_still_bonus
    move = ['guard']
    if loc in illegals:
        best_score = -10000
    for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
        score = empty_score(this_robot, loc2, game)
        if loc2 in illegals or (loc2 in moves_to and moves_to[loc2] == loc) or (loc2 in game.robots and loc2 not in moves_to):
            score -= 10000
        if score > best_score:
            best_score = score
            move = ['move', loc2]
    return move


def pin_to_spawn(this_robot, game, illegals):
    global moves_to
    turns_left = (10 - game.turn) % 10
    if game.turn > 95 or this_robot.hp < hp_to_pin[turns_left]:

    # if game.turn > 95 or turns_left > 2:
        return 'no_action'
    loc = this_robot.location
    for bot in one_robots:
        if bot.player_id != this_robot.player_id and (spawn(bot.location) and not_spawn(loc) and not (loc in illegals)):
            # sacrifice_to_guard = turns_left * 5
            # sacrifice_to_kill = math.ceil(bot.hp / 9)
            # if sacrifice_to_kill >= sacrifice_to_guard:
            return ['guard']
            # else:
            #     return ['attack', bot.location]
            # return ['guard']
    for bot in two_robots:
        if bot.player_id != this_robot.player_id and spawn(bot.location):
            block_square = move_towards_either_axis(loc, bot.location, game.turn)
            if block_square == 'no_move':
                return 'no_action'
            if not_spawn(block_square) and not (
                    block_square in illegals or (block_square in moves_to and moves_to[block_square] == loc)):
                return ['move', block_square]
    return 'no_action'


def tentative_act(this_robot, game, illegals):
    global one_robots
    global two_robots
    global moves_to
    one_robots = []
    two_robots = []
    locx = this_robot.location[0]
    locy = this_robot.location[1]
    for x in range(-2, 3):
        for y in range(-2, 3):
            if abs(x) + abs(y) in range(1, 3):
                checkx = locx + x
                checky = locy + y
                if (checkx, checky) in game.robots:
                    bot = game.robots[(checkx, checky)]
                    if abs(x) + abs(y) == 1:
                        one_robots.append(bot)
                    else:
                        two_robots.append(bot)
    possible_move = strong_hunt_the_weak(this_robot, game, illegals)
    if possible_move != 'no_action':
        return possible_move
    possible_move = run_if_scared_and_safe(this_robot, game, illegals)
    if possible_move != 'no_action':
        return possible_move
    possible_move = destruct_if_doomed_us(this_robot, game, illegals)
    if possible_move != 'no_action':
        return possible_move
    possible_move = pin_to_spawn(this_robot, game, illegals)
    if possible_move != 'no_action':
        return possible_move
    possible_move = attack_if_possible(this_robot, illegals)
    if possible_move != 'no_action':
        return possible_move
    if spawn(this_robot.location):
        possible_move = find_empty_space(this_robot, game, illegals)
        if possible_move[0] != 'guard':
            return possible_move
    possible_move = attack_moving_enemy(this_robot, game, illegals)
    if possible_move != 'no_action':
        return possible_move
    actual_move = find_empty_space(this_robot, game, illegals)
    return actual_move


def empty_score_punish_spawn(this_robot, loc, game):
    score = empty_score(this_robot, loc, game)
    if spawn(loc):
        score -= 100
    if surrounded_spawn(loc):
        score -= 100
    return score


def find_empty_space_punish_spawn(this_robot, game, illegals):
    global moves_to
    loc = this_robot.location
    best_score = empty_score_punish_spawn(this_robot, loc, game) + staying_still_bonus
    move = ['guard']
    if loc in illegals:
        best_score = -10000
    for loc2 in rg.locs_around(loc, filter_out=('obstacle', 'invalid')):
        score = empty_score_punish_spawn(this_robot, loc2, game)
        if loc2 in illegals or (loc2 in moves_to and moves_to[loc2] == loc):
            score = -10000
        if score > best_score:
            best_score = score
            move = ['move', loc2]
    return move


def run_from_spawn(this_robot, game, illegals):
    return find_empty_space_punish_spawn(this_robot, game, illegals)


def at_spawn_after_move(this_robot, move):
    if move[0] != 'move':
        return spawn(this_robot.location)
    else:
        return spawn(move[1])


def act_with_illegals(this_robot, game, illegals):
    tentative_move = tentative_act(this_robot, game, illegals)
    if 9 > game.turn % 10 > 0:
        return tentative_move
    if game.turn > 95:
        return tentative_move
    if not at_spawn_after_move(this_robot, tentative_move):
        return tentative_move
    return run_from_spawn(this_robot, game, illegals)


def destination_square(bot, move):
    if move[0] == 'move':
        return move[1]
    else:
        return bot.location


def act_with_consideration(this_robot, game, illegals):
    bots_to_consider = [this_robot]
    new_bots = [this_robot]
    while len(new_bots):
        last_bots = new_bots
        new_bots = []
        for bot in last_bots:
            locx = bot.location[0]
            locy = bot.location[1]
            for x in range(-2, 3):
                for y in range(-2, 3):
                    if abs(x) + abs(y) in range(1, 3):
                        checkx = locx + x
                        checky = locy + y
                        if (checkx, checky) in game.robots:
                            cand = game.robots[(checkx, checky)]
                            if (cand.player_id == this_robot.player_id and greater(cand, bot) and not (
                                    cand in bots_to_consider)):
                                new_bots.append(cand)
                                bots_to_consider.append(cand)
    sorted_bots = sorted(bots_to_consider, key=lambda b: -urgency(b))
    for bot in sorted_bots:
        move = act_with_illegals(bot, game, illegals)
        square = destination_square(bot, move)
        illegals.add(square)
        if bot == this_robot:
            return move


class Robot:
    def act(self, game):
        global last_turn
        global moves_to
        global illegals_global
        global worst_ratio_quadrant
        # Init round turn
        if last_turn != game.turn:
            last_turn = game.turn
            moves_to = {}  # Reset moves_to for each new round
            illegals_global = set()
            quadrants = {0: [0, 0], 1: [0, 0], 2: [0, 0], 3: [0, 0]}
            worst_ratio_quadrant = 0
            for bot in game.robots:
                if bot[0] <= 9:
                    if bot[1] <= 9:
                        if game.robots[bot].player_id != self.player_id:
                            quadrants[0][1] += 1
                        else:
                            quadrants[0][0] += 1
                    else:
                        if game.robots[bot].player_id != self.player_id:
                            quadrants[2][1] += 1
                        else:
                            quadrants[2][0] += 1
                else:
                    if bot[1] <= 9:
                        if game.robots[bot].player_id != self.player_id:
                            quadrants[1][1] += 1
                        else:
                            quadrants[1][0] += 1
                    else:
                        if game.robots[bot].player_id != self.player_id:
                            quadrants[3][1] += 1
                        else:
                            quadrants[3][0] += 1
            worst_ratio = 100
            for i in range(4):
                if quadrants[i][1] > 0 and quadrants[i][0] / quadrants[i][1] < worst_ratio:
                    worst_ratio = quadrants[i][0] / quadrants[i][1]
                    worst_ratio_quadrant = i

        # Capture friendly moves to avoid team collisions
        the_action = act_with_consideration(self, game, set())
        if the_action[0] == 'move':
            moves_to[self.location] = the_action[1]
        # else:
        #    illegals_global.add(self.location)
        if the_action[0] == 'guard':
            max_tile_score = 0
            for loc2 in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                if loc2 in game.robots and game.robots[loc2].player_id != self.player_id:
                    return ['attack', loc2]
                elif loc2 not in game.robots:
                    tile_score = 0
                    for loc3 in rg.locs_around(loc2, filter_out=('invalid', 'obstacle')):
                        if loc3 in game.robots and game.robots[loc3].player_id != self.player_id:
                            tile_score += 1
                    if tile_score > max_tile_score:
                        max_tile_score = tile_score
                        the_action = ['attack', loc2]
            if the_action[0] != 'guard':
                return the_action
            # quadrant_center = quadrant_centers[worst_ratio_quadrant]
            # move = move_towards_either_axis(self.location, quadrant_center, game.turn)
            # if move != 'no_move' and move != self.location:
            #     the_action = ['move', move]
        return the_action
