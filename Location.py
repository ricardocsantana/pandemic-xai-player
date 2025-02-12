class City:
    """
    Represents a city in the game.

    Attributes:
        name (str): The name of the city.
        pos (tuple): The coordinates or position of the city.
        color (str): The color associated with the city.
        connections (list): A list of city names directly connected to this city.
        infection_red (int): The number of red infection cubes present in the city.
        infection_blue (int): The number of blue infection cubes present in the city.
        infection_yellow (int): The number of yellow infection cubes present in the city.
    """

    def __init__(self, name, pos, color, connections):
        """
        Initialize a City instance.

        Parameters:
            name (str): The name of the city.
            pos (tuple): The coordinates (e.g., (x, y)) of the city.
            color (str): The color associated with the city.
            connections (list): A list of city names that are directly connected to this city.
        """
        self.name = name
        self.pos = pos
        self.color = color
        self.connections = connections
        self.ever_infected = False
        self.color_encoder = 0 if self.color == "YELLOW" else 1 if self.color == "BLUE" else 2 if self.color == "RED" else -1
        if self.color_encoder == -1:
            raise ValueError("Invalid color for city")

        # Initialize infection levels for each disease color to zero.
        self.infection_red = 0
        self.infection_blue = 0
        self.infection_yellow = 0