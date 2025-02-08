import unittest
from Location import City
from Pawn import Player
from Game import Board
from Constants import CITIES, COLORS, POSITIONS
from Render import Renderer

class TestPandemicGame(unittest.TestCase):
    def setUp(self):
        """Initialize a test game board with cities and players."""
        self.board = Board()
        self.cities = {name: City(name, POSITIONS[name], COLORS[name], CITIES[name]) for name in CITIES.keys()}
        self.player1 = Player(1, self.cities["GENÈVE"], role="CONTAINMENT", color="brown", shape="square", init_hand=[], partner=None)
        self.player2 = Player(2, self.cities["GENÈVE"], role="QUARANTINE", color="green", shape="circle", init_hand=[], partner=self.player1)
        self.player1.partner = self.player2

    def test_city_initialization(self):
        """Test that cities are correctly initialized."""
        city = self.cities["PARIS"]
        self.assertEqual(city.name, "PARIS")
        self.assertEqual(city.color, "#3498DB")
        self.assertIn("LONDON", city.connections)

    def test_player_initialization(self):
        """Test player initialization."""
        self.assertEqual(self.player1.loc.name, "GENÈVE")
        self.assertEqual(self.player1.role, "CONTAINMENT")
        self.assertEqual(self.player2.partner, self.player1)

    def test_drive_action(self):
        """Test player movement using the DRIVE action."""
        self.player1.take_action("DRIVE to PARIS", self.board, self.cities)
        self.assertEqual(self.player1.loc.name, "PARIS")
    
    def test_direct_flight_action(self):
        """Test player movement using the DIRECT FLIGHT action."""
        self.player1.hand.append("LONDON")
        self.player1.take_action("DIRECT FLIGHT to LONDON", self.board, self.cities)
        self.assertEqual(self.player1.loc.name, "LONDON")
        self.assertNotIn("LONDON", self.player1.hand)
    
    def test_treat_disease(self):
        """Test treating disease action."""
        self.cities["PARIS"].infection_blue = 2
        self.player1.loc = self.cities["PARIS"]
        self.player1.take_action("TREAT BLUE", self.board, self.cities)
        self.assertEqual(self.cities["PARIS"].infection_blue, 1)
    
    def test_find_cure(self):
        """Test finding a cure action."""
        self.player1.loc = self.cities["GENÈVE"]
        self.player1.hand = ["PARIS", "LONDON", "AMSTERDAM", "BERLIN"]
        self.player1.take_action("FIND CURE BLUE", self.board, self.cities)
        self.assertTrue(self.board.blue_cure)
        self.assertEqual(len(self.player1.hand), 0)
    
    def test_epidemic_spread(self):
        """Test the epidemic spread functionality."""
        self.board.draw_epidemic_deck(self.cities, 1, 3, epidemic_infect=True)
        infected_city = self.board.infection_discard_pile[-1]
        city_obj = self.cities[infected_city]

        # Determine the infection attribute dynamically based on the city's color
        if city_obj.color == "#F1C40F":  # Yellow
            self.assertGreaterEqual(city_obj.infection_yellow, 1)
        elif city_obj.color == "#3498DB":  # Blue
            self.assertGreaterEqual(city_obj.infection_blue, 1)
        elif city_obj.color == "#E74C3C":  # Red
            self.assertGreaterEqual(city_obj.infection_red, 1)

    
    def test_outbreak_trigger(self):
        """Test outbreak spreading infection to connected cities."""
        city = self.cities["PARIS"]
        city.infection_blue = 3
        self.board.outbreak("blue", city, self.cities)
        for neighbor in city.connections:
            self.assertGreaterEqual(self.cities[neighbor].infection_blue, 1)
    
    def test_game_win_condition(self):
        """Test if the game recognizes a win condition."""
        self.board.yellow_cure = True
        self.board.blue_cure = True
        self.board.red_cure = True
        self.assertTrue(self.board.check_win())
    
    def test_game_loss_conditions(self):
        """Test different loss conditions."""
        self.board.outbreak_count = 4
        self.assertTrue(self.board.check_loss())
        
        self.board.outbreak_count = 0
        self.board.yellow_cubes = 0
        self.assertTrue(self.board.check_loss())
    
        self.board.yellow_cubes = 16
        self.board.player_deck = ["PARIS"]
        self.assertTrue(self.board.check_loss())
    
    def test_renderer_graph_creation(self):
        """Test if the Renderer correctly creates a graph of cities."""
        renderer = Renderer(self.cities)
        self.assertIn("PARIS", renderer.graph.nodes)
        self.assertIn(("PARIS", "LONDON"), renderer.graph.edges)

if __name__ == "__main__":
    unittest.main()