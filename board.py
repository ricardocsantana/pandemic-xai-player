import random
from constants import POSITIONS, CITIES

SCALING_FACTOR = 75


class Board:
    """
    Represents the game board, maintaining the state of epidemics, outbreaks, disease cubes,
    cure statuses, and various decks (player and infection decks).
    """

    def __init__(self):
        """
        Initialize the game board with default epidemic counters, disease cube counts,
        cure statuses, city positions, and decks.
        """
        self.epidemic_count = 0
        self.outbreak_count = 0
        self.infection_rate = 0
        self.infection_rate_track = [2, 2, 3, 4]  # Infection rate increases with each epidemic.
        self.yellow_cubes = 16
        self.blue_cubes = 16
        self.red_cubes = 16
        self.yellow_cure = False
        self.blue_cure = False
        self.red_cure = False

        # Scale city positions according to the SCALING_FACTOR.
        self.pos = self.calculate_positions()

        # Create the player deck and assign initial hands to both players.
        self.player_1_hand, self.player_2_hand, self.player_deck = self.create_player_deck()

        # Create and shuffle the infection deck.
        self.infection_deck = self.create_infection_deck()

        # Initialize the infection discard pile and outbreak tracking.
        self.infection_discard_pile = []
        self.player_discard_pile = []
        self.outbreak_track = []

    def calculate_positions(self):
        """
        Scale the geographic coordinates of cities based on the SCALING_FACTOR.

        Returns:
            dict: A mapping from city names to scaled (x, y) positions.
        """
        return {
            city: (SCALING_FACTOR * lon, SCALING_FACTOR * lat)
            for city, (lon, lat) in POSITIONS.items()
        }

    def draw_player_deck(self, player, cities):
        """
        Draw two cards from the player deck and handle Epidemic cards.

        For each drawn card:
          - If it is not an "Epidemic", add it to the player's hand.
          - If it is an "Epidemic":
              * Increment the epidemic count and infection rate.
              * Immediately trigger an epidemic event.
              * Shuffle the infection discard pile back into the infection deck.

        After drawing two cards, perform an additional epidemic deck draw based on
        the current infection rate.

        Parameters:
            player (Player): The player drawing cards.
            cities (dict): Mapping from city names to City objects.
        """
        for _ in range(2):
            drawn_card = self.player_deck.pop()
            if drawn_card != "Epidemic":
                player.hand.append(drawn_card)
            else:
                # Handle the Epidemic card.
                self.epidemic_count += 1
                self.infection_rate += 1
                self.draw_epidemic_deck(cities, n_draws=1, n_cubes=3, epidemic_infect=True)
                # Shuffle the infection discard pile in-place and add it back to the infection deck.
                random.shuffle(self.infection_discard_pile)
                self.infection_deck.extend(self.infection_discard_pile)
                self.infection_discard_pile = []

    def draw_epidemic_deck(self, cities, n_draws, n_cubes, epidemic_infect=False, quarantine_specialist_loc=None):
        """
        Draw cards from the infection deck to simulate an epidemic spread.

        For each draw:
          - If epidemic_infect is True, pop a card from the front of the infection deck.
          - Otherwise, pop a card from the end.
          - Add the drawn card to the infection discard pile.
          - Find the corresponding city and add infection cubes.
          - If the city already has 3 cubes of that color, trigger an outbreak.

        Parameters:
            cities (dict): Mapping from city names to City objects.
            n_draws (int): Number of cards to draw.
            n_cubes (int): Number of cubes to add to the infected city.
            epidemic_infect (bool): If True, pop from the beginning of the infection deck.
        """
        for _ in range(n_draws):
            if epidemic_infect:
                target_city = self.infection_deck.pop(0)
                assert not cities[target_city].ever_infected, f"Bottom pile city {target_city} has been infected before!"
            else:
                target_city = self.infection_deck.pop()
            self.infection_discard_pile.append(target_city)

            # Infect the target city.
            for city in cities.values():
                if (city.name == target_city and epidemic_infect) or \
                (city.name == target_city and quarantine_specialist_loc is None) or \
                (city.name == target_city and not epidemic_infect \
                and quarantine_specialist_loc is not None \
                and city.name != quarantine_specialist_loc \
                and quarantine_specialist_loc not in city.connections):
                    
                    if not city.ever_infected:
                        city.ever_infected = True
                    # Reset outbreak tracking for this epidemic event.
                    self.outbreak_track = []
                    # Check the city's color and apply infection.
                    if city.color == "YELLOW":  # Yellow city.
                        if city.infection_yellow + n_cubes > 3:
                            self.yellow_cubes -= 3 - city.infection_yellow
                            city.infection_yellow = 3
                            self.outbreak("yellow", city, cities)
                        else:
                            city.infection_yellow += n_cubes
                            # assert self.yellow_cubes < n_cubes, "Not enough yellow cubes!"
                            assert city.infection_yellow <= 3, f"Hey {city.infection_yellow} {n_cubes} {epidemic_infect}"
                            self.yellow_cubes -= n_cubes
                    if city.color == "BLUE":  # Blue city.
                        if city.infection_blue + n_cubes > 3:
                            self.blue_cubes -= 3 - city.infection_blue
                            city.infection_blue = 3
                            self.outbreak("blue", city, cities)
                        else:
                            city.infection_blue += n_cubes
                            assert city.infection_blue <= 3, f"Hey {city.infection_blue} {n_cubes} {epidemic_infect}"
                            self.blue_cubes -= n_cubes
                    if city.color == "RED":  # Red city.
                        if city.infection_red + n_cubes > 3:
                            self.red_cubes -= 3 - city.infection_red
                            city.infection_red = 3
                            self.outbreak("red", city, cities)
                        else:
                            city.infection_red += n_cubes
                            assert city.infection_red <= 3, f"Hey {city.infection_red} {n_cubes} {epidemic_infect}"
                            self.red_cubes -= n_cubes
                    # If any outbreak occurred, print the outbreak track.
                    #if len(self.outbreak_track) > 0:
                        #print(self.outbreak_track)
                    break

    def outbreak(self, color, city, cities):
        """
        Trigger an outbreak in the specified city and recursively infect connected cities.

        This method uses outbreak_track to avoid infinite loops.

        Parameters:
            color (str): The color of the infection ("yellow", "blue", or "red").
            city (City): The city where the outbreak is occurring.
            cities (dict): Mapping from city names to City objects.
        """
        # Add the current city to the outbreak tracking list.
        self.outbreak_track.append(city.name)
        self.outbreak_count += 1

        # Infect each neighboring city.
        for neighbor in city.connections:
            if neighbor in self.outbreak_track:
                continue
            else:
                # Get the current infection count for the neighbor in the given color.
                current_infections = getattr(cities[neighbor], f"infection_{color.lower()}")
                if current_infections == 3:
                    # If the neighbor already has 3 cubes, trigger a recursive outbreak.
                    self.outbreak(color, cities[neighbor], cities)
                else:
                    # Otherwise, add one infection cube.
                    setattr(cities[neighbor], f"infection_{color.lower()}", current_infections + 1)

    def create_infection_deck(self):
        """
        Create and shuffle the infection deck from the list of city names.

        Returns:
            list: A shuffled list of city names representing the infection deck.
        """
        city_cards = list(CITIES.keys())
        random.shuffle(city_cards)
        return city_cards

    def create_player_deck(self):
        """
        Create the player deck, deal initial hands to two players, and insert Epidemic cards.

        The process:
          - Shuffle the city cards.
          - Deal 3 initial cards to each player.
          - Divide the remaining cards into three piles, each receiving an Epidemic card.
          - Shuffle each pile and stack them to form the final player deck.

        Returns:
            tuple: A tuple containing player 1's initial hand, player 2's initial hand, and the final player deck.
        """
        city_cards = list(CITIES.keys())
        random.shuffle(city_cards)

        # Deal 3 initial cards to each player.
        init_hand_1, init_hand_2 = city_cards[:3], city_cards[3:6]


        # Create three piles, each with an Epidemic card inserted.
        piles = [
            city_cards[6:12], #+ ["Epidemic"],
            city_cards[12:18], #+ ["Epidemic"],
            city_cards[18:] #+ ["Epidemic"]
        ]

        # Shuffle each pile individually.
        for pile in piles:
            random.shuffle(pile)

        # Combine the piles to form the final player deck.
        player_deck = sum(piles, [])  # Flatten the list of piles.
        return init_hand_1, init_hand_2, player_deck
    
    def check_win(self):
        """
        Check if the players have won the game by curing all diseases.

        Returns:
            bool: True if all diseases are cured, False otherwise.
        """
        return self.yellow_cure and self.blue_cure and self.red_cure

    def check_loss_infection(self):
        """
        Check if the players have lost the game due to outbreaks, running out of cubes, or running out of player cards.

        Returns:
            bool: True if the players have lost, False otherwise.
        """
        return self.outbreak_count >= 4 or self.yellow_cubes < 0 \
    or self.blue_cubes < 0 or self.red_cubes < 0

    def check_loss_player_deck(self):
        """
        Check if the players have lost the game due to running out of player cards.

        Returns:
            bool: True if the players have lost, False otherwise.
        """
        return len(self.player_deck) <= 1