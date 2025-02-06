from Constants import CITIES

class Player:
    def __init__(self, loc, role, color, shape, init_hand, partner):
        self.loc = loc
        self.role = role
        self.color = color
        self.shape = shape
        self.hand = init_hand
        self.active = False
        self.all_actions = [
            f"{action} to {city}"
            for action in ["DRIVE", "DIRECT FLIGHT", "CHARTER FLIGHT"]
            for city in CITIES.keys()
        ] + [
            "TREAT YELLOW", 
            "TREAT BLUE", 
            "TREAT RED", 
            "SHARE KNOWLEDGE", 
            "FIND CURE"
        ]

        self.partner = partner

    def action_mask(self, board, cities):

        allowed_actions = ["DRIVE to "+city for city in self.loc.connections] + ["DIRECT FLIGHT to "+city for city in self.hand]

        if self.loc.name in self.hand:
            allowed_actions.extend(["CHARTER FLIGHT to "+city for city in CITIES.keys()])

        if self.loc.infection_yellow>0:
            allowed_actions.append("TREAT YELLOW")

        if self.loc.infection_blue>0:
            allowed_actions.append("TREAT BLUE")

        if self.loc.infection_red>0:
            allowed_actions.append("TREAT RED")

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
    
    def take_action(self, action, board, cities):
        action = action.split()
        if action[0] == "DRIVE":
            self.loc = cities[action[-1]]
        if action[0] == "DIRECT":
            self.hand.remove(action[-1])
            self.loc = cities[action[-1]]
        if action[0] == "CHARTER":
            self.hand.remove(self.loc.name)
            self.loc = cities[action[-1]]
        if action[0] == "TREAT":
            if action[-1] == "YELLOW":
                self.loc.infection_yellow -= 1
                board.yellow_cubes += 1
            if action[-1] == "BLUE":
                self.loc.infection_blue -= 1
                board.blue_cubes += 1
            if action[-1] == "RED":
                self.loc.infection_red -= 1
                board.red_cubes += 1
        if action[0] == "SHARE":
            self.hand.remove(self.loc.name)
            self.partner.hand.append(self.loc.name)