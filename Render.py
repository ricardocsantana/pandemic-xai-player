from Constants import CITIES, COLORS
import networkx as nx
import matplotlib.pyplot as plt

class Renderer:
    def __init__(self):
        self.graph = self.create_graph()

    def create_graph(self):
        """Create a network graph of the cities."""
        graph = nx.Graph()
        for city, neighbors in CITIES.items():
            for neighbor in neighbors:
                graph.add_edge(city, neighbor)
        return graph

    def draw_city_labels(self, cities):
        """Label the cities with their names on the map."""
        for city in cities.values():
            lon, lat = city.pos
            plt.text(
                lon + 10, lat + 10, city.name,
                ha='center', va='bottom',
                fontsize=10, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor="none", alpha=0.5, boxstyle='round,pad=0.1')
            )

    def draw_infection_info(self, infection_rate, epidemic_count, outbreak_count, 
                            player_deck, yellow_cubes, blue_cubes, red_cubes, yellow_cure, blue_cure, red_cure):
        """Draw infection rate and outbreak info."""

        plt.text(-1900, 4700, "Infection\nrate {}".format(infection_rate),
                 ha='center', va='center', fontsize=12,
                 weight='bold',
                 bbox=dict(facecolor='lightgreen', edgecolor="green", alpha=0.5, boxstyle="circle, pad=.1"))

        plt.text(-1900, 4300, "{}/3 epidemics\n\n{}/4 outbreaks\n\n{} player cards left".format(epidemic_count,
                                    outbreak_count, len(player_deck)), ha='center', va='center', fontsize=12, weight='bold')

        plt.text(x=-1000, y=4700, s="{} yellow cubes left\nTreated={}".format(yellow_cubes, yellow_cure), ha='center', va='center', fontsize=12,
                 bbox=dict(facecolor='#F1C40F', edgecolor="yellow", alpha=0.3, boxstyle="square, pad=.1"))

        plt.text(x=-250, y=4700, s="{} blue cubes left\nTreated={}".format(blue_cubes, blue_cure), ha='center', va='center', fontsize=12,
                 bbox=dict(facecolor='#3498DB', edgecolor="blue", alpha=0.3, boxstyle="square, pad=.1"))

        plt.text(x=450, y=4700, s="{} red cubes left\nTreated={}".format(red_cubes, red_cure), ha='center', va='center', fontsize=12,
                 bbox=dict(facecolor='#E74C3C', edgecolor="red", alpha=0.3, boxstyle="square, pad=.1"))

    def draw_player_info(self, player_1, player_2):
        """Draw player info."""
        plt.text(x=player_1.loc.pos[0]+10, y=player_1.loc.pos[1]+10, s="A", ha='right', va='top', fontsize=16,
                 weight="bold", color=player_1.color,
                 bbox=dict(facecolor=player_1.color, edgecolor=player_1.color, alpha=0.3, boxstyle="{}, pad=.1".format(player_1.shape)))

        plt.text(x=player_2.loc.pos[0] + 10, y=player_2.loc.pos[1] + 10, s="B", ha='left', va='top',
                 fontsize=16,
                 weight="bold", color=player_2.color,
                 bbox=dict(facecolor=player_2.color, edgecolor=player_2.color, alpha=0.3,
                           boxstyle="{}, pad=.1".format(player_2.shape)))

    def draw_disease_cubes_info(self, cities):
        for city in cities.values():
            if city.infection_yellow != 0:
                plt.text(x=city.pos[0] + 10, y=city.pos[1] + 75, s=city.infection_yellow, ha='left', va='bottom',
                         fontsize=12, weight="bold",
                         bbox=dict(facecolor="#F1C40F", edgecolor="orange", alpha=0.3,
                                   boxstyle="square, pad=.1"))
            if city.infection_blue != 0:
                plt.text(x=city.pos[0] + 90, y=city.pos[1] + 75, s=city.infection_blue, ha='left',
                         va='bottom',
                         fontsize=12, weight="bold",
                         bbox=dict(facecolor="#3498DB", edgecolor="blue", alpha=0.3,
                                   boxstyle="square, pad=.1"))
            if city.infection_red != 0:
                plt.text(x=city.pos[0] + 170, y=city.pos[1] + 75, s=city.infection_red, ha='left',
                         va='bottom',
                         fontsize=12, weight="bold",
                         bbox=dict(facecolor="#E74C3C", edgecolor="red", alpha=0.3,
                                   boxstyle="square, pad=.1"))

    def draw_decks_info(self, infection_discard_pile, player_1, player_2):
        plt.text(x=-1900, y=3800, s="Infection discard pile:\n"+"\n".join(infection_discard_pile), ha='center',
                 va='center',
                 fontsize=12, weight="bold",
                 )
        plt.text(x=-2200, y=3000, s="Player A: "+str(player_1.role)+"\n"+"\n".join(player_1.hand), ha='center',
                 va='center', color=player_1.color,
                 fontsize=12, weight="bold"
                 )
        plt.text(x=-1200, y=3000, s="Player B: " + str(player_2.role) + "\n" + "\n".join(player_2.hand), ha='center',
                 va='center', color=player_2.color,
                 fontsize=12, weight="bold"
                 )

    def draw_map(self, cities, player_1, player_2, infection_rate, epidemic_count, 
                 outbreak_count, player_deck, infection_discard_pile, yellow_cubes, 
                 blue_cubes, red_cubes, yellow_cure, blue_cure, red_cure):
        """Draw the map and the city network."""
        
        # Draw the network of cities
        nx.draw(self.graph, {name: city.pos for name, city in cities.items()}, node_color=[COLORS[city] for city in self.graph.nodes], node_size=350,
                node_shape="o", alpha=0.7, linewidths=5)

        self.draw_city_labels(cities)
        self.draw_infection_info(infection_rate, epidemic_count, outbreak_count, 
                                 player_deck, yellow_cubes, blue_cubes, red_cubes,
                                 yellow_cure, blue_cure, red_cure)
        self.draw_player_info(player_1, player_2)
        self.draw_disease_cubes_info(cities)
        self.draw_decks_info(infection_discard_pile, player_1, player_2)

        plt.xlim(-2750, 3250)
        plt.ylim(1750, 5000)
        plt.draw()