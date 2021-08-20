import random


class Robot:
    def act(self, _):
        return random.choice((['guard'], ['suicide']))
