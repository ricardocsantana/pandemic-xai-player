from Constants import CITIES, COLORS
import networkx as nx
import matplotlib.pyplot as plt

class Renderer:
    """
    Responsible for rendering the game map, including cities, players, infection information, and decks.
    Utilizes networkx to generate the city network and matplotlib for drawing.
    """
    
    def __init__(self):
        """
        Initialize the Renderer by creating the network graph of cities.
        """
        self.graph = self.create_graph()

    def create_graph(self):
        """
        Create a network graph of the cities based on their connections.

        Returns:
            networkx.Graph: A graph with cities as nodes and connections as edges.
        """
        graph = nx.Graph()
        # Iterate through each city and its neighbors to add edges.
        for city, neighbors in CITIES.items():
            for neighbor in neighbors:
                graph.add_edge(city, neighbor)
        return graph

    def draw_city_labels(self, cities):
        """
        Draw labels for each city on the map.

        Parameters:
            cities (dict): A dictionary of city objects keyed by city name.
        """
        for city in cities.values():
            lon, lat = city.pos
            plt.text(
                lon + 10, lat + 10, city.name,
                ha='center', va='bottom',
                fontsize=10, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor="none", alpha=0.5, boxstyle='round,pad=0.1')
            )

    def draw_infection_info(self, infection_rate, epidemic_count, outbreak_count, player_deck,
                              yellow_cubes, blue_cubes, red_cubes, yellow_cure, blue_cure, red_cure):
        """
        Draw information regarding the infection rate, epidemic/outbreak counts, and remaining disease cubes.

        Parameters:
            infection_rate (int): The current infection rate.
            epidemic_count (int): The number of epidemics occurred.
            outbreak_count (int): The number of outbreaks occurred.
            player_deck (list): The player's deck of cards.
            yellow_cubes (int): Remaining yellow infection cubes.
            blue_cubes (int): Remaining blue infection cubes.
            red_cubes (int): Remaining red infection cubes.
            yellow_cure (bool): Whether the yellow cure has been found.
            blue_cure (bool): Whether the blue cure has been found.
            red_cure (bool): Whether the red cure has been found.
        """
        # Display the infection rate.
        plt.text(-1900, 4700, f"Infection\nrate {infection_rate}",
                 ha='center', va='center', fontsize=12, weight='bold',
                 bbox=dict(facecolor='lightgreen', edgecolor="green", alpha=0.5, boxstyle="circle, pad=.1"))

        # Display epidemic, outbreak counts and number of player cards left.
        plt.text(-1900, 4300,
                 f"{epidemic_count}/3 epidemics\n\n{outbreak_count}/4 outbreaks\n\n{len(player_deck)} player cards left",
                 ha='center', va='center', fontsize=12, weight='bold')

        # Display information for yellow cubes.
        plt.text(x=-1000, y=4700,
                 s=f"{yellow_cubes} yellow cubes left\nTreated={yellow_cure}",
                 ha='center', va='center', fontsize=12,
                 bbox=dict(facecolor='#F1C40F', edgecolor="yellow", alpha=0.3, boxstyle="square, pad=.1"))

        # Display information for blue cubes.
        plt.text(x=-250, y=4700,
                 s=f"{blue_cubes} blue cubes left\nTreated={blue_cure}",
                 ha='center', va='center', fontsize=12,
                 bbox=dict(facecolor='#3498DB', edgecolor="blue", alpha=0.3, boxstyle="square, pad=.1"))

        # Display information for red cubes.
        plt.text(x=450, y=4700,
                 s=f"{red_cubes} red cubes left\nTreated={red_cure}",
                 ha='center', va='center', fontsize=12,
                 bbox=dict(facecolor='#E74C3C', edgecolor="red", alpha=0.3, boxstyle="square, pad=.1"))

    def draw_player_info(self, player_1, player_2):
        """
        Draw player markers and information near their current positions on the map.

        Parameters:
            player_1 (Player): The first player.
            player_2 (Player): The second player.
        """
        # Display Player 1 marker ("A") near their position.
        plt.text(x=player_1.loc.pos[0] + 10, y=player_1.loc.pos[1] + 10,
                 s="A", ha='right', va='top', fontsize=16, weight="bold", color=player_1.color,
                 bbox=dict(facecolor=player_1.color, edgecolor=player_1.color, alpha=0.3,
                           boxstyle=f"{player_1.shape}, pad=.1"))
        
        # Display Player 2 marker ("B") near their position.
        plt.text(x=player_2.loc.pos[0] + 10, y=player_2.loc.pos[1] + 10,
                 s="B", ha='left', va='top', fontsize=16, weight="bold", color=player_2.color,
                 bbox=dict(facecolor=player_2.color, edgecolor=player_2.color, alpha=0.3,
                           boxstyle=f"{player_2.shape}, pad=.1"))

    def draw_disease_cubes_info(self, cities):
        """
        Draw the number of disease cubes present in each city (if any).

        Parameters:
            cities (dict): A dictionary of city objects keyed by city name.
        """
        for city in cities.values():
            # Display yellow infection cubes if present.
            if city.infection_yellow != 0:
                plt.text(x=city.pos[0] + 10, y=city.pos[1] + 75,
                         s=city.infection_yellow, ha='left', va='bottom',
                         fontsize=12, weight="bold",
                         bbox=dict(facecolor="#F1C40F", edgecolor="orange", alpha=0.3,
                                   boxstyle="square, pad=.1"))
            # Display blue infection cubes if present.
            if city.infection_blue != 0:
                plt.text(x=city.pos[0] + 90, y=city.pos[1] + 75,
                         s=city.infection_blue, ha='left', va='bottom',
                         fontsize=12, weight="bold",
                         bbox=dict(facecolor="#3498DB", edgecolor="blue", alpha=0.3,
                                   boxstyle="square, pad=.1"))
            # Display red infection cubes if present.
            if city.infection_red != 0:
                plt.text(x=city.pos[0] + 170, y=city.pos[1] + 75,
                         s=city.infection_red, ha='left', va='bottom',
                         fontsize=12, weight="bold",
                         bbox=dict(facecolor="#E74C3C", edgecolor="red", alpha=0.3,
                                   boxstyle="square, pad=.1"))

    def draw_decks_info(self, infection_discard_pile, player_1, player_2):
        """
        Draw the infection discard pile and the players' decks information.

        Parameters:
            infection_discard_pile (list): List of cards in the infection discard pile.
            player_1 (Player): The first player.
            player_2 (Player): The second player.
        """
        # Draw the infection discard pile.
        plt.text(x=-1900, y=3800,
                 s="Infection discard pile:\n" + "\n".join(infection_discard_pile),
                 ha='center', va='center', fontsize=12, weight="bold")
        
        # Draw Player 1's role and hand.
        plt.text(x=-2200, y=3000,
                 s="Player A: " + str(player_1.role) + "\n" + "\n".join(player_1.hand),
                 ha='center', va='center', color=player_1.color, fontsize=12, weight="bold")
        
        # Draw Player 2's role and hand.
        plt.text(x=-1200, y=3000,
                 s="Player B: " + str(player_2.role) + "\n" + "\n".join(player_2.hand),
                 ha='center', va='center', color=player_2.color, fontsize=12, weight="bold")

    def draw_map(self, cities, player_1, player_2, infection_rate, epidemic_count,
                 outbreak_count, player_deck, infection_discard_pile, yellow_cubes,
                 blue_cubes, red_cubes, yellow_cure, blue_cure, red_cure):
        """
        Draw the complete game map including the city network, labels, infection info, player info, and decks info.

        Parameters:
            cities (dict): A dictionary of city objects keyed by city name.
            player_1 (Player): The first player.
            player_2 (Player): The second player.
            infection_rate (int): The current infection rate.
            epidemic_count (int): The number of epidemics occurred.
            outbreak_count (int): The number of outbreaks occurred.
            player_deck (list): The list of player cards.
            infection_discard_pile (list): The infection discard pile.
            yellow_cubes (int): Remaining yellow infection cubes.
            blue_cubes (int): Remaining blue infection cubes.
            red_cubes (int): Remaining red infection cubes.
            yellow_cure (bool): Whether the yellow cure has been found.
            blue_cure (bool): Whether the blue cure has been found.
            red_cure (bool): Whether the red cure has been found.
        """
        # Prepare positions for drawing the city network.
        pos = {name: city.pos for name, city in cities.items()}
        # Determine node colors based on the city's color using the COLORS mapping.
        node_colors = [COLORS[city] for city in self.graph.nodes]
        
        # Draw the city network graph.
        nx.draw(self.graph, pos, node_color=node_colors, node_size=350,
                node_shape="o", alpha=0.7, linewidths=5)

        # Draw additional elements on the map.
        self.draw_city_labels(cities)
        self.draw_infection_info(infection_rate, epidemic_count, outbreak_count, player_deck,
                                 yellow_cubes, blue_cubes, red_cubes, yellow_cure, blue_cure, red_cure)
        self.draw_player_info(player_1, player_2)
        self.draw_disease_cubes_info(cities)
        self.draw_decks_info(infection_discard_pile, player_1, player_2)

        # Set the boundaries for the map view.
        plt.xlim(-2750, 3250)
        plt.ylim(1750, 5000)
        plt.draw()
