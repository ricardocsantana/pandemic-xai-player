import networkx as nx

class StateEvaluator:
    """
    Evaluates the current game state using multiple heuristics.
    The computed heuristic provides a measure of how favorable the current state is
    with respect to disease survival, cure progress, and resource deficits.
    """

    def __init__(self, board, current_player, players, graph, cities):
        # Initialize the evaluator with the relevant game state components.
        self.graph = graph              # Graph representing city connections.
        self.cities = cities            # Mapping of city names to City objects.
        self.board = board              # The game board with global state.
        self.current_player = current_player  # The player taking the action.
        self.players = players          # List of all players.
    
    def h_dsurv(self):
        """
        Heuristic for disease survival.
        Calculates the weighted average of distances from each player's location to every city,
        weighted by the infection level at the city.
        Lower values indicate better chances to keep infections under control.
        """
        h_dsurv = 0
        total_infection = 0
        # For each player and each city, calculate:
        #   (distance from player to city) * (total infection level in the city)
        for player in self.players:
            for city in self.cities.keys():
                city_infection = (
                    self.cities[city].infection_red +
                    self.cities[city].infection_blue +
                    self.cities[city].infection_yellow
                )
                h_dsurv += nx.shortest_path_length(self.graph, city, player.loc.name) * city_infection
                total_infection += city_infection

        # Prevent division by zero.
        return h_dsurv / total_infection if total_infection != 0 else 0

    def h_dcure(self):
        """
        Heuristic for cure effort.
        Sums up the distances from the research station ("GENÈVE") to each player's location.
        Lower values indicate players are nearer to the cure hub.
        """
        h_dcure = 0
        for player in self.players:
            h_dcure += nx.shortest_path_length(self.graph, "GENÈVE", player.loc.name)
        return h_dcure

    def h_cards(self):
        """
        Heuristic for card collection.
        For each disease that has not been cured, determine the deficit of cards needed (to reach 4).
        It finds the maximum number of cards of each color held by any player and computes the shortfall.
        """
        h_cards = 0
        for color, cure_status in [("YELLOW", self.board.yellow_cure), 
                                   ("BLUE", self.board.blue_cure), 
                                   ("RED", self.board.red_cure)]:
            if not cure_status:
                # Determine the maximum number of cards of this disease color among all players.
                max_cards = max(
                    (sum(1 for card in player.hand if self.cities[card].color == color) 
                     for player in self.players), 
                    default=0  # In case no player holds any cards of that color.
                )
                # Add the deficit (if any) required to reach 4 cards.
                h_cards += max(0, 4 - max_cards)
        return h_cards

    def h_disc(self):
        """
        Heuristic based on the discard pile.
        For each uncured disease, counts the relevant cards that have been discarded,
        as these are no longer available to players.
        """
        h_disc = 0
        if not self.board.yellow_cure:
            h_disc += len([card for card in self.board.player_discard_pile if self.cities[card].color == "YELLOW"])

        if not self.board.blue_cure:
            h_disc += len([card for card in self.board.player_discard_pile if self.cities[card].color == "BLUE"])

        if not self.board.red_cure:
            h_disc += len([card for card in self.board.player_discard_pile if self.cities[card].color == "RED"])

        return h_disc

    def h_inf(self):
        """
        Heuristic for overall infection.
        Sums the total number of infection cubes across all cities.
        Higher values indicate a more severe outbreak.
        """
        h_inf = 0
        for city in self.cities.keys():
            h_inf += (
                self.cities[city].infection_red +
                self.cities[city].infection_blue +
                self.cities[city].infection_yellow
            )
        return h_inf

    def h_cure(self):
        """
        Heuristic for cure progress.
        Adds a penalty for each disease type for which a cure has not yet been found.
        """
        h_cure = 0
        if not self.board.yellow_cure:
            h_cure += 1

        if not self.board.blue_cure:
            h_cure += 1

        if not self.board.red_cure:
            h_cure += 1

        return h_cure

    def h_state(self, goal):
        """
        Combines all heuristics into a single state evaluation metric using fixed weights.
        The formula is:
          0.5 * h_dsurv + 0.5 * h_dcure + h_cards + 0.5 * h_disc + 0.6 * h_inf + 24 * h_cure
        A lower score typically indicates a more favorable game state.
        """
        h_dsurv = self.h_dsurv()
        h_dcure = self.h_dcure()
        h_cards = self.h_cards()
        h_disc = self.h_disc()
        h_inf = self.h_inf()
        h_cure = self.h_cure()

        if goal:

            return 0 * h_dsurv + 0.5 * h_dcure + h_cards + 0.5 * h_disc + 0.6 * h_inf + 24 * h_cure
        
        else:

            return 0.5 * h_dsurv + 0 * h_dcure + h_cards + 0.5 * h_disc + 0.6 * h_inf + 24 * h_cure