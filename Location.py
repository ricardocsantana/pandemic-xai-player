class City:
    def __init__(self, name, pos, color, connections):
        self.name = name
        self.pos = pos
        self.color = color
        self.connections=connections
        self.infection_red = 0
        self.infection_blue = 0
        self.infection_yellow = 0