class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class Settings(AttrDict):
    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self.spawn_coordinates = None
        self.obstacles = None
        self.player_count = None
        self.start = None

    def init_map(self, map_data):
        self.spawn_coordinates = map_data['spawn']
        self.obstacles = map_data['obstacle']
        self.player_count = map_data.get('player_count', 2)
        self.start = map_data.get('start', None)


settings = Settings({
    'spawn_every': 10,
    'spawn_per_player': 5,
    'board_size': 19,
    'robot_hp': 50,
    'attack_range': (8, 10),
    'collision_damage': 5,
    'suicide_damage': 15,
    'max_turns': 100,
    'str_limit': 50,  # limit on length of representation of action
    'max_seed': 2147483647,

    # rating systems
    'default_rating': 1200,

    # user-scripting
    'max_time_initialization': 2000,
    'max_time_first_act': 1500,
    'max_time_per_act': 300,
    'exposed_properties': ('location', 'hp', 'player_id'),
    'player_only_properties': ('robot_id',),
    'user_obj_types': ('Robot',),
    'valid_commands': ('move', 'attack', 'guard', 'suicide')
})
