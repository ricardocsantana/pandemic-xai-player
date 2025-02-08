from matplotlib import pyplot as plt
import random
from Pawn import Player
from Location import City
from Render import Renderer
from Constants import POSITIONS, CITIES, COLORS

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

        # After drawing two cards, draw from the epidemic deck as per the current infection rate.
        self.draw_epidemic_deck(cities, n_draws=self.infection_rate_track[self.infection_rate], n_cubes=1)

    def draw_epidemic_deck(self, cities, n_draws, n_cubes, epidemic_infect=False):
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
            else:
                target_city = self.infection_deck.pop()
            self.infection_discard_pile.append(target_city)

            # Infect the target city.
            for city in cities.values():
                if city.name == target_city:
                    # Reset outbreak tracking for this epidemic event.
                    self.outbreak_track = []
                    # Check the city's color and apply infection.
                    if city.color == "#F1C40F":  # Yellow city.
                        if city.infection_yellow == 3:
                            self.outbreak("yellow", city, cities)
                        else:
                            city.infection_yellow += n_cubes
                            self.yellow_cubes -= n_cubes
                    if city.color == "#3498DB":  # Blue city.
                        if city.infection_blue == 3:
                            self.outbreak("blue", city, cities)
                        else:
                            city.infection_blue += n_cubes
                            self.blue_cubes -= n_cubes
                    if city.color == "#E74C3C":  # Red city.
                        if city.infection_red == 3:
                            self.outbreak("red", city, cities)
                        else:
                            city.infection_red += n_cubes
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
            city_cards[6:10] + ["Epidemic"],
            city_cards[10:14] + ["Epidemic"],
            city_cards[14:] + ["Epidemic"]
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

    def check_loss(self):
        """
        Check if the players have lost the game due to outbreaks, running out of cubes, or running out of player cards.

        Returns:
            bool: True if the players have lost, False otherwise.
        """
        return self.outbreak_count >= 4 or self.yellow_cubes <= 0 \
    or self.blue_cubes <= 0 or self.red_cubes <= 0 or len(self.player_deck) <= 1

def main():
    """
    Main function to initialize the game board, cities, players, and start the game loop.
    
    The game loop:
      - Sets up the game state including drawing initial epidemic cards.
      - Enters an interactive loop with matplotlib for rendering.
      - Alternates between players, drawing cards, and taking actions.
      - Listens for a 'q' key press to quit the loop.
    """

    render_mode = int(input("Choose render mode: 0 for train, 1 for human: "))


    for _ in range(100):

        #print("Starting a new game...")

        # Initialize the game board.
        board = Board()

        # Create City objects for each city using scaled positions, predefined colors, and connections.
        cities = {
            name: City(name, board.pos[name], COLORS[name], CITIES[name])
            for name in CITIES.keys()
        }

        # Initialize two players, both starting in "GENÈVE".
        player_1 = Player(
            cities["GENÈVE"],
            role="CONTAINMENT",
            color="brown",
            shape="square",
            init_hand=board.player_1_hand,
            partner=None
        )
        player_2 = Player(
            cities["GENÈVE"],
            role="QUARANTINE",
            color="green",
            shape="circle",
            init_hand=board.player_2_hand,
            partner=player_1
        )
        player_1.partner = player_2

        # Prepare the epidemic decks by drawing epidemic cards with varying cube counts.
        board.draw_epidemic_deck(cities, n_draws=2, n_cubes=3)
        board.draw_epidemic_deck(cities, n_draws=2, n_cubes=2)
        board.draw_epidemic_deck(cities, n_draws=2, n_cubes=1)

        if render_mode == 1:
            # Initialize the renderer for drawing the game map.
            renderer = Renderer(cities)

            # Enable interactive mode in matplotlib and create a figure.
            plt.ion()
            fig = plt.figure(figsize=(18, 12))

            # Control flag to handle quitting the game loop.
            control = {"quit": False}

            # Define an event handler to listen for key presses (specifically 'q' to quit).
            def on_key(event):
                if event.key == 'q':
                    control["quit"] = True

            # Connect the key press event handler to the figure.
            cid = fig.canvas.mpl_connect('key_press_event', on_key)

        # Player 1 starts the game.
        player_1.active = True

        # Animation loop: run for up to 100 iterations or until 'q' is pressed.
        for n in range(100):

            if render_mode == 1:
                # Quit the loop if the 'q' key has been pressed.
                if control["quit"]:
                    print("Quitting the animation loop.")
                    break
            
            # Check for game over conditions.
            if board.check_win():
                # print("Players have won the game!")
                break
            if board.check_loss():
                # print("Players have lost the game!")
                break

            # Every 4 iterations (except the first), draw cards for the active player and toggle turns.
            if n % 4 == 0 and n != 0:
                if player_1.active:
                    board.draw_player_deck(player_1, cities)
                else:
                    board.draw_player_deck(player_2, cities)
                # Toggle active status between players.
                player_1.active = not player_1.active
                player_2.active = not player_2.active

            if render_mode == 1:
                # Clear the current figure and redraw the game map.
                plt.clf()
                renderer.draw_map(
                    cities,
                    player_1,
                    player_2,
                    board.infection_rate_track[board.infection_rate],
                    board.epidemic_count,
                    board.outbreak_count,
                    board.player_deck,
                    board.infection_discard_pile,
                    board.yellow_cubes,
                    board.blue_cubes,
                    board.red_cubes,
                    board.yellow_cure,
                    board.blue_cure,
                    board.red_cure
                )

            if player_1.active:
                player_1.step(board, cities)
            else:
                player_2.step(board, cities)

            if render_mode == 1:
                # Wait for a button press (key or mouse click) before continuing.
                plt.waitforbuttonpress()

        if render_mode == 1:
            # Disconnect the event handler and disable interactive mode.
            fig.canvas.mpl_disconnect(cid)
            plt.ioff()
            plt.show()


if __name__ == "__main__":
    main()

