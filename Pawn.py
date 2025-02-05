from Constants import CITIES

class Player:
    def __init__(self, loc, role, color, shape, init_hand, partner):
        self.loc = loc
        self.role = role
        self.color = color
        self.shape = shape
        self.hand = init_hand
        self.all_actions = list(CITIES.keys())+["TREAT YELLOW CUBE", "TREAT BLUE CUBE", "TREAT RED CUBE", "SHARE KNOWLEDGE", "FIND CURE"]
        self.partner = partner

    def action_mask(self, board, cities):
        if self.loc.name in self.hand:
            allowed_cities = list(CITIES.keys())
        else:
            allowed_cities = list(set(self.loc.connections + self.hand))
        allowed_actions = allowed_cities
        if self.loc.infection_yellow>0:
            allowed_actions.append("TREAT YELLOW CUBE")
        if self.loc.infection_blue>0:
            allowed_actions.append("TREAT BLUE CUBE")
        if self.loc.infection_red>0:
            allowed_actions.append("TREAT RED CUBE")
        if self.loc.name == self.partner.loc.name and self.loc.name in self.hand:
            allowed_actions.append("SHARE KNOWLEDGE")
        if self.loc.name == self.partner.loc.name and self.loc.name in self.partner.hand:
            allowed_actions.append("SHARE KNOWLEDGE")
        if self.loc.name == "GENÈVE" and [cities[city].color for city in self.hand].count("YELLOW")>=4 and board.yellow_cure is False:
            allowed_actions.append("FIND CURE")
        if self.loc.name == "GENÈVE" and [cities[city].color for city in self.hand].count("BLUE")>=4 and board.blue_cure is False:
            allowed_actions.append("FIND CURE")
        if self.loc.name == "GENÈVE" and [cities[city].color for city in self.hand].count("RED")>=4 and board.red_cure is False:
            allowed_actions.append("FIND CURE")

        action_mask = [1 if action in allowed_actions else 0 for action in self.all_actions]

        return action_mask
    
    def take_action(self, action, cities):
        if action in list(CITIES.keys()):
            self.move(action, cities)

    def move(self, city_name, cities):
        print(city_name)
        self.loc = cities[city_name]