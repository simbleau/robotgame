# Dulladob 0.1 by Camelot Chess
# Modified and improved by Spencer Imbleau and Matthias Sterckx
# http://robotgame.net/viewrobot/7641

from rgkit import rg

spawn_param = 8  # which turn to we begin bouncing?

suicide_param = 7  # when to blow ourselves up (param*surrounders>hp)?
suicide_fear_param = 5  # which to fear enemies blowing up?

staying_still_bonus = 0.17  # points for staying put
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
    if this_robot.hp < 30:
        return 'no_action'
    weakest_enemy = 30
    best_move = 'no_action'
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
        if bot.player_id != this_robot.player_id and bot.hp < weakest_enemy:
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
    if this_robot.hp > 25:
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


## SFPAR STARTS HERE

# global variable to store the future moves of each ally robot
# we can use this to avoid friendly collisions
future_moves = []
future_attacks = []
# this is used to store the current turn considered by the future_moves array
future_moves_turn = 0
all_bots = []


def cant_easily_leave_spawn(loc, game):
    """Returns whether a bot would need 2+ moves to exit the spawn area.
    (i.e. the bot is in spawn and all of the locations around it are occupied/
    obstacle/invalid)"""

    if 'spawn' in rg.loc_types(loc):
        adjacent_locs = rg.locs_around(loc,
                                       filter_out=['spawn', 'obstacle', 'invalid'])

        for loc in adjacent_locs:
            if loc in all_bots:
                adjacent_locs.remove(loc)
        return len(adjacent_locs) == 0

    # if the bot is not in spawn, then it can easily leave it
    # by standing still, hehe.
    return False


def bot_is_in_trouble(bot, game):
    """Returns whether a bot is in trouble.
    If a bot could die in the next turn, it is in trouble."""
    return could_die_in_loc(bot.hp, bot.location, bot.player_id, game)


def could_die_in_loc(hp, loc, player_id, game):
    """Returns whether or not a bot could die in a given location,
    based on its hp and player_id.
    Considers the number of enemy bots nearby and whether or not
    the robot is standing on a spawn tile just before more will spawn."""

    adjacent_bots = get_bots_next_to(loc, game)
    adjacent_enemies = [b for b in adjacent_bots if b.player_id != player_id]

    # each adjacent enemy can deal up to 10 damage in a turn
    possible_hp_loss = len(adjacent_enemies) * 10
    if possible_hp_loss >= hp:
        # could die if all of the adjacent_enemies attack
        return True

    if 'spawn' in rg.loc_types(loc):
        if game['turn'] % 10 == 0:
            # next turn, if we remain on the spawn square, it could die
            return True

    return False


def get_weakest_bot(bots):
    """Returns the weakest bot out of a list of bots."""
    assert len(bots) != 0

    # bots have 50 hp max
    least_hp = 51
    weakest_bot = None

    for bot in bots:
        if bot.hp < least_hp:
            weakest_bot = bot
            least_hp = bot.hp

    return weakest_bot


def get_bots_next_to(location, game):
    """Returns all bots next to a location.
    old version called locs_around every single
    time it looped, now it does once per call
    """
    around = rg.locs_around(location)
    return [all_bots[x] for x in all_bots.keys() if x in around]


def get_bot_in_location(location, game):
    """Returns the bot in the given location."""
    if location in all_bots.keys():
        return all_bots[location]
    else:
        return None


def is_possible_suicider(bot, game):
    """Returns whether a bot is a possible suicider based on a kinda
    restrictive algorithm.

    Returns true if the sum of the hp of all enemy bots is greater than
    the bot's hp and there are more than 1 adjacent enemy bots and
    there is at least one adjacent bot that would die."""

    # get all adjacent enemies of suicider
    adjacent_bots = get_bots_next_to(bot.location, game)
    for bot2 in adjacent_bots:
        if bot2.player_id == bot.player_id:
            adjacent_bots.remove(bot2)

    # whether the total possible hp hit would outweigh the
    # hp lost
    if len(adjacent_bots) > 1:
        if sum([min(bot2.hp, 15) for bot2 in adjacent_bots]) > bot.hp:
            for bot2 in adjacent_bots:
                if bot2.hp <= 15:
                    return True
    return False


class Robot:

    def sort_bots_closest_first(self, bots):
        """Sorts a list of bots sorted closest to farthest away."""
        return sorted(bots, key=lambda b: rg.wdist(self.location, b.location))

    def get_enemy_bots_next_to(self, location, game):
        """Returns the enemy bots next to a location."""
        enemies = []

        for loc in rg.locs_around(location):
            bot = get_bot_in_location(loc, game)
            if bot and (bot.player_id != self.player_id):
                enemies.append(bot)

        return enemies

    def get_friendlies_next_to(self, location, game):
        """Returns the friendly bots next to a location.
        Note: does not return /this/ robot.(filters out any robot whose
        location is equal to this robot's location)"""
        friendlies = []

        for loc in rg.locs_around(location):
            bot = get_bot_in_location(loc, game)
            if bot and (bot.player_id == self.player_id) and bot.location != self.location:
                friendlies.append(bot)

        return friendlies

    def get_adjacent_enemy_bots(self, game):
        """Returns a list of the adjacent enemy bots."""
        return self.get_enemy_bots_next_to(self.location, game)

    def is_suiciding_beneficial(self, game):
        """Returns whether or not the bot should suicide on this turn."""
        # get the adjacent bots
        adjacent_bots = self.get_adjacent_enemy_bots(game)

        if sum([min(bot.hp, 15) for bot in adjacent_bots]) > self.hp:

            # see if the bot can escape to any adjacent location
            for loc in rg.locs_around(self.location,
                                      filter_out=['invalid', 'obstacle']):
                # the bot can't escape to the location if there's an enemy in it
                if not could_die_in_loc(self.hp, loc, self.player_id, game):
                    bot_in_loc = get_bot_in_location(loc, game)
                    if bot_in_loc and bot_in_loc.player_id != self.player_id:
                        continue
                    else:
                        return False
            return True

    def get_distance_to_closest_bot(self, game, loc=None,
                                    friendly=False, enemy=False):
        """Returns the distance from the given location (or, by default,
        this robot's location) to the nearest enemy."""
        if not loc:
            loc = self.location
        shortest_distance = 99999

        for bot in all_bots.values():
            if bot.location != loc and bot.location != self.location:
                if (friendly == enemy == False) or \
                        (enemy and (bot.player_id != self.player_id)) or \
                        (friendly and (bot.player_id == self.player_id)):
                    dist = rg.wdist(loc, bot.location)
                    shortest_distance = min(dist, shortest_distance)
        return shortest_distance

    def get_best_loc(self, locs, game):
        """Returns the best location out of a list.
        The 'goodness' of a tile is determined by get_tile_goodness()."""
        best_loc_weight = -9999
        best_loc = None
        for loc in locs:
            loc_weight = self.get_tile_goodness(loc, game)
            if loc_weight > best_loc_weight:
                best_loc = loc
                best_loc_weight = loc_weight
        assert best_loc
        return best_loc

    def get_tile_goodness(self, loc, game):
        """Returns how 'good' a tile is to move to or stay on.
        Based on a whole bunch of factors. Fine-tuning necessary."""

        types = rg.loc_types(loc)
        enemies_next_to_loc = self.get_enemy_bots_next_to(loc, game)
        enemies_next_to_loc_fighting_friendlies = []
        for enemy in enemies_next_to_loc:
            if self.get_friendlies_next_to(enemy.location, game):
                enemies_next_to_loc_fighting_friendlies.append(enemy)

        # enemies_next_to_loc_to_fight_friendlies = []
        # for enemy in enemies_next_to_loc:
        #     for pos in rg.locs_around(enemy.location):
        #         if pos in future_moves:
        #             enemies_next_to_loc_to_fight_friendlies.append(enemy)
        #             break

        friendlies_next_to_loc = self.get_friendlies_next_to(loc, game)

        nearby_friendlies_in_spawn = []
        nearby_friendlies_in_deep_spawn = []
        for friendly in friendlies_next_to_loc:
            if 'spawn' in rg.loc_types(friendly.location):
                nearby_friendlies_in_spawn.append(friendly)
                if cant_easily_leave_spawn(friendly.location, game):
                    nearby_friendlies_in_deep_spawn.append(friendly)

        friendly_in_loc = enemy_in_loc = False
        if loc != self.location:
            bot_in_location = get_bot_in_location(loc, game)
            if bot_in_location:
                if bot_in_location.player_id == self.player_id:
                    friendly_in_loc = True
                else:
                    enemy_in_loc = True

        else:
            bot_in_location = None
        # distance_to_closest_enemy = self.get_distance_to_closest_bot(game,
        #                                                              loc=loc, enemy=True)
        #
        # distance_to_closest_friendly = self.get_distance_to_closest_bot(game,
        #                                                                 loc=loc, friendly=True)

        nearby_friendlies_in_trouble = []
        for friendly in friendlies_next_to_loc:
            if bot_is_in_trouble(friendly, game):
                nearby_friendlies_in_trouble.append(friendly)

        goodness = 0
        # get out of spawn areas, especially if things are about to spawn
        # highest priority: +20 pts if things are about to spawn
        if game['turn'] <= 90:
            goodness -= ('spawn' in types) * ((game['turn'] % 10 == 0) * 20 + 1)
        # if the bot can't easily leave spawn (e.g. has to move through
        # more spawn area or an enemy to get out) in the location, that's bad
        # the closer to the spawn timer we are, the worse this is, so
        # multiply it by the game turn % 10
        if game['turn'] <= 90:
            goodness -= cant_easily_leave_spawn(loc, game) * (
                    game['turn'] % 10) * 0.5

        # if enemies next to the location are fighting or will fight
        # other friendlies, help them
        goodness += len(enemies_next_to_loc_fighting_friendlies) * 2.5

        # goodness += len(enemies_next_to_loc_to_fight_friendlies) * 0.5

        # more enemies next to a location, the worse.
        # even worse if a friendly is already in the location
        #    (so the enemies will target that loc)
        # even worse if our hp is low
        goodness -= len(enemies_next_to_loc) ** 2 + friendly_in_loc

        goodness -= friendly_in_loc * 4

        # slight bias towards NOT moving right next to friendlies
        # a sort of lattices, like
        # X X X X
        #  X X X
        # X X X X
        # is the best shape, I think
        # goodness -= len(friendlies_next_to_loc) * 0.05

        # nearby friendlies in trouble will definitely want to escape this turn
        goodness -= len(nearby_friendlies_in_trouble) * 9

        if could_die_in_loc(self.hp, loc, self.player_id, game):
            # /try/ not to go where the bot can die
            # seriously
            goodness -= 20

        # all else remaining the same, move towards the center
        goodness -= rg.dist(loc, rg.CENTER_POINT) * 0.01

        # bias towards remaining in place and attacking
        goodness += (loc == self.location) * \
                    (0.25 + 0.75 * (len(enemies_next_to_loc) == 1))
        # especially if we're only fighting one bot

        # if self.hp > 15:
        #     # if we are strong enough, move close to (2 squares away) the
        #     # nearest enemy
        #     goodness -= max(distance_to_closest_enemy, 2)
        # else:
        #     # otherwise, run away from the nearest enemy, up to 2 squares away
        #     goodness += min(distance_to_closest_enemy, 2)

        # friendlies should group together
        # if a bot is caught alone, bots that actively hunt and surround,
        # e.g. Chaos Witch Quelaang, will murder them
        # so move up to two tiles from the nearest friendly
        # goodness -= min(distance_to_closest_friendly, 2) * 0.5

        # don't move into an enemy
        # it's slightly more ok to move into an enemy that could die in the
        # next turn by staying here, cause he's likely to either run or die
        # it's perfectly alright, maybe even encouraged, to move into a bot
        # that would die from bumping into you anyways (<=5hp)
        if enemy_in_loc:
            goodness -= enemy_in_loc * (30 - 29 * bot_is_in_trouble(bot_in_location, game))
            goodness += 3 * (bot_in_location.hp <= 5)

        # don't block friendlies trying to move out of spawn!
        # only matters when things will still spawn in the future, of course
        if game['turn'] <= 90:
            # if they can escape through us
            if not 'spawn' in types:
                goodness -= len(nearby_friendlies_in_spawn) * 2
            # especially don't block those who can't easily leave spawn
            # (the two lists overlap, so no extra weighting needed)
            goodness -= len(nearby_friendlies_in_deep_spawn) * 2

        # don't move next to possible suiciders if our hp is low enough to die
        # from them
        for enemy in enemies_next_to_loc_fighting_friendlies:
            if is_possible_suicider(enemy, game) and (self.hp <= 15):
                goodness -= 2

        # the more enemies that could move next to the loc, the worse
        # (the more this bot could be surrounded)
        # goodness -= min(len(self.get_enemies_that_could_move_next_to(
        #     loc, game)), 1) * 0.5

        # don't move into a square if another bot already plans to move there
        goodness -= 999 * (loc in future_moves)

        # allies attacking the same spot is bad, but not the end of the world..
        # e.g. if a robot needs to go through a spot being attacked by an
        # ally to leave spawn, he DEFINITELY still needs to move there
        goodness -= 9 * (loc in future_attacks)

        return goodness

    def get_enemies_that_could_move_next_to(self, loc, game):
        enemies = []
        for bot in all_bots.values():
            if bot.player_id != self.player_id:
                if rg.wdist(bot.location, loc) == 2:
                    enemies.append(bot)
        return enemies

    def get_attack_goodness(self, loc, game):
        """Returns how 'good' attacking a certain location is.
        Based upon the number of friendlies and enemies next to the location,
        any bot that is in the location, etc."""
        # types = rg.loc_types(loc)
        enemies_next_to_loc = self.get_enemy_bots_next_to(loc, game)
        friendlies_next_to_loc = self.get_friendlies_next_to(loc, game)
        # nearby_friendlies_in_trouble = []
        # for friendly in friendlies_next_to_loc:
        #     if bot_is_in_trouble(friendly, game):
        #         nearby_friendlies_in_trouble.append(friendly)
        nearby_enemies_in_trouble = []
        for enemy in enemies_next_to_loc:
            if bot_is_in_trouble(enemy, game):
                nearby_enemies_in_trouble.append(enemy)
        robot = get_bot_in_location(loc, game)

        goodness = 0

        if robot:
            if robot.player_id == self.player_id:
                # we're attacking a friendly's location
                # no enemy's gonna move into them...
                goodness -= 5
            else:
                # attacking an enemy is good
                goodness += (100 - robot.hp) / 50.0 * 20
        else:
            # no bot is at the location
            # so base the goodness on how likely it is for bots to move there

            # more enemies that can move into the location, the better
            # weighted by 3 because even if there are two other friendlies
            # next to the loc, we still want to attack if it's the only square
            # an enemy is next to
            goodness += len(enemies_next_to_loc) * 3

            # enemies aren't too likely to move next to a friendly
            # goodness -= len(friendlies_next_to_loc)

            # if there are enemies in trouble nearby, we want to try and catch
            # them escaping!
            goodness += len(nearby_enemies_in_trouble) * 5

            # nearby friendlies in trouble will definitely want to escape this
            # turn
            # maybe to this square
            # goodness -= len(nearby_friendlies_in_trouble)

            # don't attack where an ally is already moving to
            # or attacking, at least not too much
            if loc in future_moves:
                goodness -= 20
            elif loc in future_attacks:
                goodness -= 3
        return goodness

    def get_best_attack_loc(self, locs, game):
        """Determines the best location to attack out of a list of locations.
        Uses get_attack_goodness() to weigh the locations."""
        best_loc_weight = -9999
        best_loc = None
        for loc in locs:
            loc_weight = self.get_attack_goodness(loc, game)
            if loc_weight > best_loc_weight:
                best_loc = loc
                best_loc_weight = loc_weight
        return best_loc

    def sfpar_turn(self, game):
        """The function called by game.py itself: returns the action the robot
              should take this turn."""
        action = []

        # update the future_moves array if necessary
        # only the first robot will do this
        global future_moves_turn, future_moves, future_attacks, all_bots
        if future_moves_turn != game['turn']:
            future_moves = []
            future_attacks = []
            future_moves_turn = game['turn']
            all_bots = game.get('robots')

        # adjacent_bots = self.get_adjacent_enemy_bots(game)
        if self.is_suiciding_beneficial(game):
            action = ['suicide']
        else:
            locs = [self.location] + rg.locs_around(self.location,
                                                    filter_out=['invalid', 'obstacle'])
            target_loc = self.get_best_loc(locs, game)
            if target_loc != self.location:
                action = ['move', target_loc]
            else:
                attack_locs = rg.locs_around(self.location,
                                             filter_out=['invalid', 'obstacle'])
                action = ['attack', self.get_best_attack_loc(attack_locs, game)]

        if action[0] == 'move':
            # assert not action[1] in future_moves
            future_moves.append(action[1])
            if action[1] == self.location:
                action = ['guard']
        if action[0] == 'attack':
            future_attacks.append(action[1])

        return action

    ## Better Than The Rest Bot
    def bttr_turn(self, game):
        bestEnemy = 999
        bestAlly = 999
        closestEnemy = (0, 0)
        closestAlly = (0, 0)
        badGuys = 0
        allyDistance = 999
        enemyDistance = 5

        def guessShot():
            for potentialShot in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                allyCount = 0
                enemyCount = 0
                if potentialShot not in game['robots']:
                    for enemy in rg.locs_around(potentialShot, filter_out=('invalid', 'obstacle')):
                        if enemy in game['robots']:
                            if game['robots'][enemy].player_id != self.player_id:
                                enemyCount += 1
                    if enemyCount > 0:
                        return ['attack', potentialShot]
            return ['attack', rg.toward(self.location, closestEnemy)]

        def gtfo():
            for friend in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                if friend in game['robots']:
                    if game['robots'][friend].player_id == self.player_id:
                        if 'spawn' in rg.loc_types(friend):
                            escapes = 1
                            for escape in rg.locs_around(friend, filter_out=('invalid', 'obstacle', 'spawn')):
                                if escape not in game['robots']:
                                    escapes += 1
                            if escapes == 1:
                                for gtfo in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                                    if gtfo not in game['robots']:
                                        safer = 0
                                        for safe in rg.locs_around(gtfo, filter_out=('invalid', 'obstacle', 'spawn')):
                                            if safe in game['robots']:
                                                if game['robots'][safe].player_id == self.player_id:
                                                    safer += 1
                                        if safer == 0:
                                            return ['move', gtfo]
                                for gtfo in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                                    if gtfo not in game['robots']:
                                        return ['move', gtfo]

            return "nope"

        if 'spawn' in rg.loc_types(self.location):
            goodPlaces = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))
        else:
            goodPlaces = rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn'))
        if (3, 3) in goodPlaces:
            goodPlaces.remove((3, 3))
        if (15, 3) in goodPlaces:
            goodPlaces.remove((15, 3))
        if (3, 15) in goodPlaces:
            goodPlaces.remove((3, 15))
        if (15, 15) in goodPlaces:
            goodPlaces.remove((15, 15))

        for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
            if loc in game['robots']:
                if game['robots'][loc].player_id != self.player_id:
                    badGuys += 1
        if game['turn'] % 10 == 0:
            if 'spawn' in rg.loc_types(self.location):
                for escape in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                    if escape not in game['robots']:
                        return ['move', escape]
                for escape in rg.locs_around(self.location, filter_out=('invalid', 'obstacle', 'spawn')):
                    if game['robots'][escape].player_id == self.player_id:
                        return ['move', escape]
                return ['suicide']
            escape = gtfo()
            if escape != "nope":
                return gtfo()

        for loc, bot in game['robots'].items():
            if bot.player_id != self.player_id:
                if rg.wdist(loc, self.location) < bestEnemy:
                    bestEnemy = rg.wdist(loc, self.location)
                    closestEnemy = loc
            else:
                if rg.wdist(loc, self.location) < bestAlly:
                    bestAlly = rg.wdist(loc, self.location)
                    closestAlly = loc

        if game['robots'][self.location].hp <= 15 or game['robots'][self.location].hp <= badGuys * 10 or badGuys == 3:
            if rg.wdist(closestEnemy, self.location) == 1:
                for loc in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                    if loc not in game['robots']:
                        bad = False
                        for enemy in rg.locs_around(loc, filter_out=('invalid', 'obstacle')):
                            if enemy in game['robots']:
                                if game['robots'][enemy].player_id != self.player_id:
                                    bad = True
                        if loc not in goodPlaces:
                            bad = True
                        if not bad:
                            return ['move', loc]
                if bestAlly > 5:
                    for noBoom in rg.locs_around(self.location, filter_out=('invalid', 'obstacle')):
                        if noBoom not in game['robots']:
                            enemyCount = 0
                            for noBang in rg.locs_around(noBoom, filter_out=('invalid', 'obstacle')):
                                if noBang in game['robots']:
                                    if game['robots'][noBang].player_id != self.player_id:
                                        enemyCount += 1
                            if enemyCount * 10 < game['robots'][self.location].hp:
                                return ['move', noBoom]
                if game['robots'][self.location].hp <= badGuys * 10:
                    if badGuys > 1:
                        return ['suicide']
            if rg.wdist(closestEnemy, self.location) == 2:
                return guessShot()
        if badGuys == 0:
            if bestEnemy == 2:
                if bestAlly > 4:
                    return guessShot()

        if rg.wdist(closestEnemy, self.location) == 1:
            return ['attack', closestEnemy]
        if game['robots'][self.location].hp > 15:
            for fightHelp in goodPlaces:
                if fightHelp not in game['robots']:
                    for enemy in rg.locs_around(fightHelp, filter_out=('invalid', 'obstacle')):
                        if enemy in game['robots']:
                            if game['robots'][enemy].player_id != self.player_id:
                                for ally in rg.locs_around(enemy, filter_out=('invalid', 'obstacle')):
                                    if ally in game['robots']:
                                        if game['robots'][ally].player_id == self.player_id:
                                            return ['move', fightHelp]

        if rg.wdist(closestEnemy, self.location) <= enemyDistance:
            place = rg.toward(self.location, closestEnemy)
            if place == self.location:
                return ['guard']
            else:
                badEnemies = 0
                for badGuy in rg.locs_around(place, filter_out=('invalid', 'obstacle')):
                    if badGuy in game['robots']:
                        badEnemies += 1
                if place in goodPlaces:
                    if badEnemies < 3:
                        return ['move', place]

        if rg.wdist(closestAlly, self.location) <= allyDistance:
            if rg.toward(self.location, loc) != self.location:
                if rg.toward(self.location, loc) in goodPlaces:
                    return ['move', rg.toward(self.location, loc)]
                else:
                    return ['guard']
        if self.location == rg.CENTER_POINT:
            return ['guard']
        if rg.toward(rg.toward(self.location, rg.CENTER_POINT), loc) in goodPlaces:
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]
        return ['guard']

    def act(self, game):
        global last_turn
        global moves_to
        global illegals_global
        # Init round turn
        if last_turn != game.turn:
            last_turn = game.turn
            moves_to = {}  # Reset moves_to for each new round
            illegals_global = set()

        # Use BTTR for up to round 5 for the aggressive opening
        the_action = None
        if game.turn < 5:
            the_action = self.bttr_turn(game)
        # Use sfpar on spawn waves as it has better logic
        elif game.turn % 10 == 1 or game.turn % 10 == 2:
            the_action = self.sfpar_turn(game)
        # Use dullodob otherwise
        else:
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

        return the_action