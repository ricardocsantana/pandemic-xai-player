import random
from Constants import CITIES

class Player:
    """
    Represents a player in the game, holding state such as location, role, hand, and partner.

    Attributes:
        loc: The current city (object) where the player is located.
        role: The role assigned to the player.
        color: The player's color.
        shape: The player's shape.
        hand: A list of city cards held by the player.
        active: A flag indicating if the player is currently active (e.g., it's their turn).
        all_actions: A pre-computed list of all possible actions the player might take.
        partner: The partner player with whom knowledge sharing is possible.
    """

    def __init__(self, id, loc, role, color, shape, init_hand, partner):
        """
        Initialize the Player with its attributes.

        Parameters:
            id: The player's ID.
            loc: The starting location (city object) of the player.
            role: The player's role.
            color: The player's color.
            shape: The player's shape.
            init_hand: The initial list of city cards in the player's hand.
            partner: The partner Player object.
        """
        self.id = id
        self.loc = loc
        self.role = role
        self.color = color
        self.shape = shape
        self.hand = init_hand
        self.active = False  # Indicates if it's the player's turn

        # Build the list of all possible actions.
        # The first list comprehension generates movement actions:
        # - "DRIVE to <city>" for each neighboring city.
        # - "DIRECT FLIGHT to <city>" for each city card in hand.
        # - "CHARTER FLIGHT to <city>" for each city (if the player's hand contains the current city).
        self.all_actions = [
            f"{action} to {city}"
            for action in ["DRIVE", "DIRECT FLIGHT", "CHARTER FLIGHT"]
            for city in CITIES.keys()
        ] + [
            "TREAT YELLOW", 
            "TREAT BLUE", 
            "TREAT RED", 
            "SHARE KNOWLEDGE", 
            "FIND CURE YELLOW",
            "FIND CURE BLUE",
            "FIND CURE RED"
        ]

        self.partner = partner

    def action_mask(self, board, cities):
        """
        Create an action mask for the player indicating which actions are allowed.

        The action mask is a list of 1's and 0's corresponding to each action in `self.all_actions`
        (1 if the action is allowed, 0 otherwise).

        Parameters:
            board: The game board object, containing global game state (e.g., cures, cube counts).
            cities: A dictionary mapping city names to city objects.

        Returns:
            A list of integers (1 or 0) representing allowed actions.
        """
        allowed_actions = []

        # DRIVE: Allowed to move to any directly connected city.
        allowed_actions.extend([f"DRIVE to {city}" for city in self.loc.connections])

        # DIRECT FLIGHT: Allowed to fly to any city for which the player holds the corresponding card.
        allowed_actions.extend([f"DIRECT FLIGHT to {city}" for city in self.hand])

        # CHARTER FLIGHT: If the player holds the card of their current city, they may fly anywhere.
        if self.loc.name in self.hand:
            allowed_actions.extend([f"CHARTER FLIGHT to {city}" for city in CITIES.keys()])

        # TREAT: Allowed if the current city has infection cubes.
        if self.loc.infection_yellow > 0:
            allowed_actions.append("TREAT YELLOW")
        if self.loc.infection_blue > 0:
            allowed_actions.append("TREAT BLUE")
        if self.loc.infection_red > 0:
            allowed_actions.append("TREAT RED")

        # SHARE KNOWLEDGE: Allowed if both players are in the same city and one of them holds the card for that city.
        if self.loc.name == self.partner.loc.name:
            if self.loc.name in self.hand:
                allowed_actions.append("SHARE KNOWLEDGE")
            if self.loc.name in self.partner.hand:
                allowed_actions.append("SHARE KNOWLEDGE")

        # FIND CURE: Allowed if at the research station ("GENÈVE"), the player has at least 4 cards of a color,
        # and a cure for that color has not been found.
        if self.loc.name == "GENÈVE":
            # Create a list of colors corresponding to the player's hand cards.
            hand_colors = [cities[card].color for card in self.hand]
            if hand_colors.count("YELLOW") >= 4 and not board.yellow_cure:
                allowed_actions.append("FIND CURE YELLOW")
            if hand_colors.count("BLUE") >= 4 and not board.blue_cure:
                allowed_actions.append("FIND CURE BLUE")
            if hand_colors.count("RED") >= 4 and not board.red_cure:
                allowed_actions.append("FIND CURE RED")

        # Build the action mask: mark each action in all_actions as allowed (1) or not allowed (0).
        action_mask = [1 if action in allowed_actions else 0 for action in self.all_actions]

        return action_mask, allowed_actions
    
    def random_action(self, action_mask):
        """
        Randomly select an action from the allowed actions, based on the action mask.

        Parameters:
            action_mask: A list of integers (1 or 0) representing allowed actions.

        Returns:
            A string representing the selected action.
        """
        action_mask, _ = action_mask
        # Select a random action from the allowed actions.
        action_idx = random.choice([i for i, v in enumerate(action_mask) if v == 1])
        action = self.all_actions[action_idx]
        return action

    def take_action(self, action, board, cities):
        """
        Execute the given action, updating the player's state and the game board accordingly.

        Parameters:
            action (str): The action string to be executed.
            board: The game board object, containing global game state.
            cities: A dictionary mapping city names to city objects.
        """
        tokens = action.split()
        action_type = tokens[0]
        init_board = board
        init_cities = cities
        init_hand = self.hand
        init_loc = self.loc
        init_partner_hand = self.partner.hand

        if action_type == "DRIVE":
            # For a DRIVE action, move the player to the target city (must be directly connected).
            target_city_name = tokens[-1]
            self.loc = cities[target_city_name]

        elif action_type == "DIRECT":
            # For a DIRECT FLIGHT, remove the target city card from the player's hand and move there.
            target_city_name = tokens[-1]
            self.hand.remove(target_city_name)
            self.loc = cities[target_city_name]
            board.player_discard_pile.append(target_city_name)  # Add the card to the discard pile

        elif action_type == "CHARTER":
            # For a CHARTER FLIGHT, remove the card corresponding to the current city and fly to any city.
            self.hand.remove(self.loc.name)
            target_city_name = tokens[-1]
            self.loc = cities[target_city_name]
            board.player_discard_pile.append(self.loc.name)  # Add the card to the discard pile

        elif action_type == "TREAT":
            # For a TREAT action, remove infection cubes from the current city.
            # If a cure has not been found for that color, only one cube is removed.
            # Otherwise, all cubes are removed.
            color = tokens[-1]
            if color == "YELLOW":
                if not board.yellow_cure:
                    self.loc.infection_yellow -= 1
                    board.yellow_cubes += 1
                else:
                    board.yellow_cubes += self.loc.infection_yellow
                    self.loc.infection_yellow = 0
            elif color == "BLUE":
                if not board.blue_cure:
                    self.loc.infection_blue -= 1
                    board.blue_cubes += 1
                else:
                    board.blue_cubes += self.loc.infection_blue
                    self.loc.infection_blue = 0
            elif color == "RED":
                if not board.red_cure:
                    self.loc.infection_red -= 1
                    board.red_cubes += 1
                else:
                    board.red_cubes += self.loc.infection_red
                    self.loc.infection_red = 0

        elif action_type == "SHARE":
            # For SHARE KNOWLEDGE, the player who holds the card for the current city gives it to their partner.
            if self.loc.name in self.hand:
                self.hand.remove(self.loc.name)
                self.partner.hand.append(self.loc.name)
            else:
                self.partner.hand.remove(self.loc.name)
                self.hand.append(self.loc.name)

        elif action_type == "FIND":
            # For FIND CURE, mark the cure as found for the specified disease color.
            color = tokens[-1]
            if color == "YELLOW":
                board.yellow_cure = True
            elif color == "BLUE":
                board.blue_cure = True
            elif color == "RED":
                board.red_cure = True

            # Remove the 4 cards of the same color from the player's hand.
            cities_to_remove = []
            for card in self.hand:
                if cities[card].color == color:
                    cities_to_remove.append(card)
                    board.player_discard_pile.append(card)  # Add the card to the discard pile
                if len(cities_to_remove) == 4:
                    break
            
            self.hand = [city for city in self.hand if city not in cities_to_remove]

        return init_board, init_cities, init_hand, init_loc, init_partner_hand

    def step(self, board, cities, action=None):
        """
        Take a step in the game, selecting and executing one action.

        Parameters:
            board: The game board object, containing global game state.
            cities: A dictionary mapping city names to city objects.

        """

        action_mask = self.action_mask(board, cities)
        if action is None:
            action = self.random_action(action_mask)
        print(self.id, action)
        self.take_action(action, board, cities)
