import networkx as nx

class StateEvaluator:

    def __init__(self, action, board, current_player, players, graph, cities):
        self.action = action
        self.graph = graph
        self.cities = cities
        self.board = board
        self.current_player = current_player
        self.players = players

    def h_dsurv(self):
        h_dsurv = 0
        total_infection = 0
        for player in self.players:
            for city in self.cities.keys():
                city_infection = self.cities[city].infection_red + self.cities[city].infection_blue + self.cities[city].infection_yellow
                h_dsurv += nx.shortest_path_length(self.graph, city, player.loc.name) * \
                city_infection
                total_infection += city_infection

        return h_dsurv / total_infection

    def h_dcure(self):
        h_dcure = 0
        for player in self.players:
            h_dcure += nx.shortest_path_length(self.graph, "GENÈVE", player.loc.name)

        return h_dcure

    def h_cards(self):
        h_cards = 0
        
        for color, cure_status in [("YELLOW", self.board.yellow_cure), 
                                ("BLUE", self.board.blue_cure), 
                                ("RED", self.board.red_cure)]:
            if not cure_status:
                max_cards = max(
                    (sum(1 for card in player.hand if self.cities[card].color == color) 
                    for player in self.players), 
                    default=0  # Handle the case where no player has cards of this color
                )
                h_cards += max(0, 4 - max_cards)  # Ensure we don't add negative numbers

        return h_cards


    def h_disc(self):
        h_disc = 0
        if not self.board.yellow_cure:
            h_disc += len([card for card in self.board.player_discard_pile if self.cities[card].color == "YELLOW"])

        if not self.board.blue_cure: 
            h_disc += len([card for card in self.board.player_discard_pile if self.cities[card].color == "BLUE"])

        if not self.board.red_cure:
            h_disc += len([card for card in self.board.player_discard_pile if self.cities[card].color == "RED"])

        return h_disc

    def h_inf(self):
        h_inf = 0
        for city in self.cities.keys():
            h_inf += self.cities[city].infection_red + self.cities[city].infection_blue + self.cities[city].infection_yellow
        return h_inf

    def h_cure(self):
        h_cure = 0
        if not self.board.yellow_cure:
            h_cure += 1

        if not self.board.blue_cure:
            h_cure += 1

        if not self.board.red_cure:
            h_cure += 1

        return h_cure

    def h_state(self):
        h_dsurv = self.h_dsurv()
        h_dcure = self.h_dcure()
        h_cards = self.h_cards()
        h_disc = self.h_disc()
        h_inf = self.h_inf()
        h_cure = self.h_cure()

        return 0.5*h_dsurv + 0.5*h_dcure + h_cards + 0.5*h_disc + 0.6*h_inf + 24*h_cure