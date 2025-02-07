from matplotlib import pyplot as plt
import random
from Pawn import Player
from Location import City
from Render import Renderer
from Constants import POSITIONS, CITIES, COLORS

SCALING_FACTOR = 75

class Board:

    def __init__(self):
        self.epidemic_count = 0
        self.outbreak_count = 0
        self.infection_rate = 0
        self.infection_rate_track = [2, 2, 3, 4]
        self.yellow_cubes = 16
        self.blue_cubes = 16
        self.red_cubes = 16
        self.yellow_cure = False
        self.blue_cure = False
        self.red_cure = False
        self.pos = self.calculate_positions()
        self.player_1_hand, self.player_2_hand, self.player_deck=self.create_player_deck()
        self.infection_deck = self.create_infection_deck()
        self.infection_discard_pile=[]
        self.outbreak_track = []

    def calculate_positions(self):
        """Map the positions of cities to scaled geographic coordinates."""
        return {
            city: (SCALING_FACTOR * lon, SCALING_FACTOR * lat)
            for city, (lon, lat) in POSITIONS.items()
        }
    
    def draw_player_deck(self, player, cities):
        """Draw from the player deck."""
        for _ in range(2):
            drawn_card = self.player_deck.pop()
            if drawn_card != "Epidemic":
                player.hand.append(drawn_card)
            else:
                self.epidemic_count += 1
                self.infection_rate += 1
                self.draw_epidemic_deck(cities, 1, 3, epidemic_infect=True)
                self.infection_discard_pile = random.shuffle(self.infection_discard_pile) or self.infection_discard_pile
                self.infection_deck.extend(self.infection_discard_pile)
                self.infection_discard_pile = []

        self.draw_epidemic_deck(cities, self.infection_rate_track[self.infection_rate], 1)

    def draw_epidemic_deck(self, cities, n_draws, n_cubes, epidemic_infect=False):
        """Draw from the epidemic deck."""
        for _ in range(n_draws):
            if epidemic_infect:
                target_city = self.infection_deck.pop(0)
            else:
                target_city=self.infection_deck.pop()
            self.infection_discard_pile.append(target_city)
            for city in cities.values():
                if city.name==target_city:
                    self.outbreak_track = []
                    if city.color=="#F1C40F":
                        if city.infection_yellow==3:
                            self.outbreak("yellow", city, cities)
                        else:
                            city.infection_yellow += n_cubes
                            self.yellow_cubes -= n_cubes
                    if city.color=="#3498DB":
                        if city.infection_blue==3:
                            self.outbreak("blue", city, cities)
                        else:
                            city.infection_blue += n_cubes
                            self.blue_cubes -= n_cubes
                    if city.color=="#E74C3C":
                        if city.infection_red==3:
                            self.outbreak("red", city, cities)
                        else:
                            city.infection_red += n_cubes
                            self.red_cubes -= n_cubes
                    if len(self.outbreak_track)>0:
                        print(self.outbreak_track)
                    break

    def outbreak(self, color, city, cities):
        self.outbreak_track.append(city.name)
        self.outbreak_count += 1
        for neighbor in city.connections:
            if neighbor in self.outbreak_track:
                continue
            else:
                current_infections = getattr(cities[neighbor], f"infection_{color.lower()}")
                if current_infections == 3:
                    self.outbreak(color, cities[neighbor], cities)
                else:
                    setattr(cities[neighbor], f"infection_{color.lower()}", current_infections + 1)

    def create_infection_deck(self):
        city_cards = list(CITIES.keys())
        random.shuffle(city_cards)
        return city_cards

    def create_player_deck(self):
        city_cards = list(CITIES.keys())
        random.shuffle(city_cards)

        # Deal 3 initial cards to each player
        init_hand_1, init_hand_2 = city_cards[:3], city_cards[3:6]

        # Create three piles with an Epidemic card in each
        piles = [city_cards[6:10] + ["Epidemic"],
                 city_cards[10:14] + ["Epidemic"],
                 city_cards[14:] + ["Epidemic"]]

        # Shuffle each pile
        for pile in piles:
            random.shuffle(pile)

        # Stack piles to form the final player deck
        player_deck = sum(piles, [])  # Flatten the list of lists

        return init_hand_1, init_hand_2, player_deck

def main():
    board = Board()
    cities = {name: City(name, board.pos[name], COLORS[name], CITIES[name]) for name in CITIES.keys()}
    player_1 = Player(cities["GENÈVE"], role="CONTAINMENT", color="brown", shape="square",
                      init_hand=board.player_1_hand, partner=None)
    player_2 = Player(cities["GENÈVE"], role="QUARANTINE", color="green", shape="circle",
                      init_hand=board.player_2_hand, partner=player_1)
    player_1.partner = player_2

    action_space = player_1.all_actions

    # Prepare the epidemic decks as before
    board.draw_epidemic_deck(cities, 2, 3)
    board.draw_epidemic_deck(cities, 2, 2)
    board.draw_epidemic_deck(cities, 2, 1)

    renderer = Renderer()
    
    # Enable interactive mode and create a figure
    plt.ion()
    fig = plt.figure(figsize=(18, 12))
    
    # Dictionary to hold a control flag for quitting
    control = {"quit": False}

    # Define an event handler to listen for key presses
    def on_key(event):
        if event.key == 'q':
            control["quit"] = True
    
    # Connect the key press event handler to the figure
    cid = fig.canvas.mpl_connect('key_press_event', on_key)
    player_1.active = True # Player 1 starts the game
    # Animation loop: run for a number of frames (adjust as needed)
    for n in range(100):
        # Check if the "q" key was pressed to quit the loop
        if control["quit"]:
            print("Quitting the animation loop.")
            break


        if n % 4 == 0 and n != 0:

            if player_1.active:
                board.draw_player_deck(player_1, cities)
            else:
                board.draw_player_deck(player_2, cities)

            player_1.active = not player_1.active
            player_2.active = not player_2.active

        # Clear the current figure and redraw the map
        plt.clf()
        renderer.draw_map(cities, player_1, player_2, board.infection_rate_track[board.infection_rate], board.epidemic_count, 
                 board.outbreak_count, board.player_deck, board.infection_discard_pile, board.yellow_cubes, 
                 board.blue_cubes, board.red_cubes, board.yellow_cure, board.blue_cure, board.red_cure)
        
        if player_1.active:
            possible_actions_player_1 = player_1.action_mask(board, cities)
            action_player_1 = action_space[random.choice([index for index, value in enumerate(possible_actions_player_1) if value == 1])]
            player_1.take_action(action_player_1, board, cities)
            print("1: ", action_player_1)

        if player_2.active:
            possible_actions_player_2 = player_2.action_mask(board, cities)
            action_player_2 = action_space[random.choice([index for index, value in enumerate(possible_actions_player_2) if value == 1])]
            player_2.take_action(action_player_2, board, cities)
            print("2: ", action_player_2)

        # Wait for a button press (key or mouse click) before continuing.
        # If the user presses 'q', the on_key callback will set control["quit"] to True.
        plt.waitforbuttonpress()
    
    # Disconnect the event handler
    fig.canvas.mpl_disconnect(cid)
    plt.ioff()
    plt.show()


if __name__ == "__main__":
    main()
