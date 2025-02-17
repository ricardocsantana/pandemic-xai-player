import gymnasium as gym
from gymnasium import spaces
import numpy as np
from board import Board
from location import City
from player import Player
from render import Renderer
from dfs_top_k import GreedyAgent
from constants import CITIES, COLORS
import networkx as nx
import itertools
import copy
from state_eval import StateEvaluator

class PandemicEnv(gym.Env):
    """
    Gymnasium-compatible environment for Pandemic: Hot Zone – Europe.
    """

    def __init__(self):
        super(PandemicEnv, self).__init__()

        self.renderer = Renderer()
        self.graph = self.renderer.graph
        self.win_score = []

        # Track the number of actions taken in a turn
        self.actions_taken = 0
        self.game_number = 0

        # Define action space (number of possible actions)
        self.action_space = spaces.Discrete(79)

        # Define observation space (game state representation)
        self.observation_space = spaces.Box(low=0, high=1, shape=(849,), dtype=np.float32)

    def set_share_location(self, current_player_hand_by_color, partner_player_hand_by_color, graph):
        """
        Return:
            share_knowledge (bool) : Whether we can share cards in an advantageous location
            share_knowledge_location (str or None) : The city name where sharing should occur
        """
        # Track best option for (3+1) scenario
        best_option_1_distance = float("inf")
        best_option_1_location = None
        
        # Track best option for (2 + [1..2]) scenario
        best_option_2_distance = float("inf")
        best_option_2_location = None
        
        # Giver/Receiver pairs (in both directions):
        possible_pairs = [
            ("current", current_player_hand_by_color, "partner", partner_player_hand_by_color),
            ("partner", partner_player_hand_by_color, "current", current_player_hand_by_color),
        ]
        
        for giver_name, giver_hand, receiver_name, receiver_hand in possible_pairs:
            for color in ["YELLOW", "BLUE", "RED"]:
                # Skip if cure is already discovered
                if getattr(self.board, f"{color.lower()}_cure"):
                    continue
                
                # Count how many cards of this color each player has
                num_receiver_color = sum(1 for c in receiver_hand.values() if c == color)
                num_giver_color = sum(1 for c in giver_hand.values() if c == color)

                # Potential city cards (of this color) in the giver's hand
                potential_locations = [
                    city for city, card_color in giver_hand.items() if card_color == color
                ]
                if not potential_locations:
                    # If giver has none of these color cards, skip
                    continue

                # We'll calculate the distance for each potential location
                # from that city to both 'current' and 'partner' players.
                for candidate_city in potential_locations:
                    dist_current = nx.shortest_path_length(
                        graph, candidate_city, self.current_player.loc.name
                    )
                    dist_partner = nx.shortest_path_length(
                        graph, candidate_city, self.current_player.partner.loc.name
                    )
                    total_dist = dist_current + dist_partner

                    # ---------------------------------------------------
                    #  Option 1: (receiver has 3 cards, giver has >= 1)
                    # ---------------------------------------------------
                    if num_receiver_color == 3 and num_giver_color >= 1:
                        if total_dist < best_option_1_distance:
                            best_option_1_distance = total_dist
                            best_option_1_location = candidate_city

                    # ---------------------------------------------------
                    #  Option 2: (receiver has 2, giver has 1 or 2)
                    # ---------------------------------------------------
                    elif num_receiver_color == 2 and num_giver_color in [1, 2]:
                        if total_dist < best_option_2_distance:
                            best_option_2_distance = total_dist
                            best_option_2_location = candidate_city
        
        # -----------------------------------------------------------
        # Decide which scenario to return:
        #   - If Option 1 is available anywhere, use that.
        #   - Otherwise, if Option 2 is available, use that.
        #   - Otherwise, no share_knowledge is possible.
        # -----------------------------------------------------------
        if best_option_1_location is not None:
            return True, best_option_1_location
        elif best_option_2_location is not None:
            return True, best_option_2_location
        else:
            return False, None


    def choose_player_goal(self, current_player_hand, partner_player_hand, cities, graph):

        treat_yellow_disease = False
        treat_blue_disease = False
        treat_red_disease = False
        share_knowledge = False
        share_knowledge_location = None

        current_player_hand_by_color = {city: cities[city].color for city in current_player_hand}
        partner_player_hand_by_color = {city: cities[city].color for city in partner_player_hand}

        if not self.board.yellow_cure:
            treat_yellow_disease = 1 if list(current_player_hand_by_color.values()).count("YELLOW") >= 4 else 0
        if not self.board.blue_cure:
            treat_blue_disease = 1 if list(current_player_hand_by_color.values()).count("BLUE") >= 4 else 0
        if not self.board.red_cure:
            treat_red_disease = 1 if list(current_player_hand_by_color.values()).count("RED") >= 4 else 0

        treat_disease = treat_yellow_disease or treat_blue_disease or treat_red_disease

        if treat_disease:
            return treat_disease, share_knowledge, share_knowledge_location
        
        share_knowledge, share_knowledge_location = self.set_share_location(current_player_hand_by_color, partner_player_hand_by_color, graph)
        if share_knowledge:
            return treat_disease, share_knowledge, share_knowledge_location
        
        return treat_disease, share_knowledge, share_knowledge_location
    
    def find_cure_prob(self):
        """
        Returns the probability of finding a cure based on the player's hand.
        """
        cure_prob = {"YELLOW": 0, "BLUE": 0, "RED": 0}

        if self.board.yellow_cure:
            cure_prob["YELLOW"] = 1
        if self.board.blue_cure:
            cure_prob["BLUE"] = 1
        if self.board.red_cure:
            cure_prob["RED"] = 1

        for player in self.players:

            player_hand_by_color = [self.cities[card].color for card in player.hand]

            yellow_prob = min(1, player_hand_by_color.count("YELLOW") / 4)
            blue_prob = min(1, player_hand_by_color.count("BLUE") / 4)
            red_prob = min(1, player_hand_by_color.count("RED") / 4)

            if yellow_prob > cure_prob["YELLOW"]:
                cure_prob["YELLOW"] = yellow_prob
            if blue_prob > cure_prob["BLUE"]:
                cure_prob["BLUE"] = blue_prob
            if red_prob > cure_prob["RED"]:
                cure_prob["RED"] = red_prob
        
        return cure_prob

    def select_discard(self, player_id, player_hand):
        """
        Selects the best cards to discard from the player's hand.
        """
        
        n_discard = len(player_hand) - 6
        best_cards = None
        best_value = float("inf")
        
        for cards in list(itertools.combinations(player_hand, n_discard)):
            temp_env = copy.deepcopy(self)
            temp_env.players[player_id-1].discard_cards(cards, temp_env.board)

            evaluator = StateEvaluator(temp_env.board, temp_env.current_player,
                        temp_env.players, temp_env.graph, temp_env.cities)
            
            h_value = evaluator.h_discard()
            if h_value < best_value:
                best_value = h_value
                best_cards = cards

        return best_cards

    def reset(self, seed=None, options=None):
        """
        Resets the game state to start a new episode.
        """
        super().reset(seed=seed)

        # Initialize the game board
        self.board = Board()
        self.cities = {
            name: City(name, self.board.pos[name], COLORS[name], CITIES[name])
            for name in CITIES.keys()
        }
        
        # Initialize players
        self.player_1 = Player(
            id=1,
            loc=self.cities["GENÈVE"],
            role="CONTAINMENT",
            color="brown",
            shape="square",
            init_hand=self.board.player_1_hand,
            partner=None
        )
        self.player_2 = Player(
            id=2,
            loc=self.cities["GENÈVE"],
            role="QUARANTINE",
            color="green",
            shape="circle",
            init_hand=self.board.player_2_hand,
            partner=self.player_1
        )
        self.player_1.partner = self.player_2
        self.current_player = self.player_1

        self.current_player.goal = self.choose_player_goal(self.current_player.hand, self.player_2.hand, self.cities, self.graph)

        self.players = [self.player_1, self.player_2]

        self.board.draw_epidemic_deck(self.cities, n_draws=2, n_cubes=3)
        self.board.draw_epidemic_deck(self.cities, n_draws=2, n_cubes=2)
        self.board.draw_epidemic_deck(self.cities, n_draws=2, n_cubes=1)
        
        self.current_player = self.player_1
        self.actions_taken = 0  # Reset action counter
        self.game_number += 1  # Increment game number
        self.prev_outbreak_count = 0
        self.high_cure_prob = self.find_cure_prob()
        self.game_round = 0

        return self.get_observation(), {}

    def step(self, action_idx):
        """
        Executes a single action and updates the game state.
        Each player takes 4 actions per turn.
        """
    
        done = False

        self.current_player.previous_loc = self.current_player.loc.name
        
        cure_prob = self.find_cure_prob()
        if cure_prob["YELLOW"] > self.high_cure_prob["YELLOW"]:
            self.high_cure_prob["YELLOW"] = cure_prob["YELLOW"]
        if cure_prob["BLUE"] > self.high_cure_prob["BLUE"]:
            self.high_cure_prob["BLUE"] = cure_prob["BLUE"]
        if cure_prob["RED"] > self.high_cure_prob["RED"]:
            self.high_cure_prob["RED"] = cure_prob["RED"]

        self.prev_outbreak_count = self.board.outbreak_count
        prev_loc = self.current_player.loc.name
        action = self.current_player.all_actions[action_idx]
        self.current_player.take_action(action, self.board, self.cities)

        token = action.split()
        # current_player_hand_by_color = [self.cities[card].color for card in self.current_player.hand]

        # 0: Minimize infection spread

        reward_dict = {}
        reward_dict["Cure disease"] = 0
        reward_dict["Share knowledge"] = 0
        reward_dict["Move"] = 0
        reward = 0

        find_cure, share_knowledge, share_knowledge_location = self.current_player.goal

        if find_cure:
            reward += 0.1 * (nx.shortest_path_length(self.graph, prev_loc, "GENÈVE") - \
            nx.shortest_path_length(self.graph, self.current_player.loc.name, "GENÈVE"))
            reward_dict["Cure disease"] += 0.1 * (nx.shortest_path_length(self.graph, prev_loc, "GENÈVE") - \
            nx.shortest_path_length(self.graph, self.current_player.loc.name, "GENÈVE"))

        if token[0] == "FIND":
            reward += 3
            reward_dict["Cure disease"] += 3

        if share_knowledge:
            reward += 0.1 * (nx.shortest_path_length(self.graph, prev_loc, share_knowledge_location) - \
            nx.shortest_path_length(self.graph, self.current_player.loc.name, share_knowledge_location))
            reward_dict["Cure disease"] += 0.1 * (nx.shortest_path_length(self.graph, prev_loc, share_knowledge_location) - \
            nx.shortest_path_length(self.graph, self.current_player.loc.name, share_knowledge_location))

        if token[0] == "SHARE":
            if self.find_cure_prob()[self.current_player.loc.color] > self.high_cure_prob[self.current_player.loc.color]:
                reward += 1
                reward_dict["Share knowledge"] += 1

        if token[0] == "DIRECT" and not getattr(self.board, f"{COLORS[token[-1]].lower()}_cure"):
            reward += -0.1
            reward_dict["Move"] += -0.1

        if token[0] == "CHARTER" and not getattr(self.board, f"{COLORS[prev_loc].lower()}_cure"):
            reward += -0.1
            reward_dict["Move"] += -0.1

        # C: Treat a disease
        if token[0] == "TREAT": 
            if getattr(self.current_player.loc, f"infection_{token[-1].lower()}") == 2:
                reward += 0.3
                reward_dict["Treat disease"] = 0.3
            elif getattr(self.current_player.loc, f"infection_{token[-1].lower()}") == 1:
                reward += 0.1
                reward_dict["Treat disease"] = 0.1
            elif getattr(self.current_player.loc, f"infection_{token[-1].lower()}") == 0:
                reward += 0.1
                reward_dict["Treat disease"] = 0.1
        
        self.actions_taken += 1  # Increment action count

        if self.board.check_win():
                reward = 10
                done = True

        # If 4 actions have been taken, switch turns and draw player cards
        if self.actions_taken == 4 and not done:
            # Check win/loss conditions
            if self.board.check_loss_player_deck():
                reward = -10
                done = True
            else:
                self.actions_taken = 0  # Reset action counter
                self.board.draw_player_deck(self.current_player, self.cities)
                # After drawing two cards, draw from the epidemic deck as per the current infection rate.
                self.board.draw_epidemic_deck(self.cities, n_draws=self.board.infection_rate_track[self.board.infection_rate], 
                                              n_cubes=1, quarantine_specialist_loc=self.player_2.loc.name)
                self.game_round += 1

            if self.board.check_loss_infection():
                reward = -10
                done = True

            # Switch player turns
            self.current_player = self.player_2 if self.current_player == self.player_1 else self.player_1
            self.current_player.goal = self.choose_player_goal(self.current_player.hand, self.current_player.partner.hand, self.cities, self.graph)

        # Discard cards if player has more than 6
        for player in self.players:
            if len(player.hand) > 6:
                discard = self.select_discard(player.id, player.hand)
                player.discard_cards(discard, self.board)

        if done:
            self.win_score.append(reward)

        return self.get_observation(), reward, done, False, reward_dict
    
    def valid_action_mask(self):
        action_mask, _ = self.current_player.action_mask(self.board, self.cities)
        assert len(action_mask) == 79
        return np.array(action_mask)
    
    def render(self, mode="human"):
        """
        Render the current state of the game after each action.
        """
        
        self.renderer.draw_map(
            self.cities,
            self.player_1,
            self.player_2,
            self.board.infection_rate_track[self.board.infection_rate],
            self.board.epidemic_count,
            self.board.outbreak_count,
            self.board.player_deck,
            self.board.infection_discard_pile,
            self.board.yellow_cubes,
            self.board.blue_cubes,
            self.board.red_cubes,
            self.board.yellow_cure,
            self.board.blue_cure,
            self.board.red_cure,
            self.game_number
        )

    def decode_obs(self, obs):
        """
        Decodes the observation vector into a dictionary representation.
        """
        decoded_obs = {}

        for idx, city in enumerate(self.cities.values()):
            decoded_obs[city.name] = [round(float(elem), 1) for elem in obs[idx*35:(idx+1)*35]]

        decoded_obs["Game round"] = round(float(obs[840]), 1)
        decoded_obs["Player id"] = round(float(obs[841]), 1)
        decoded_obs["Player turn"] = round(float(obs[842]), 1)
        decoded_obs["Outbreak count"] = round(float(obs[843]), 1)
        decoded_obs["Infection rate"] = round(float(obs[844]), 1)
        decoded_obs["Yellow cure"] = round(float(obs[845]), 1)
        decoded_obs["Blue cure"] = round(float(obs[846]), 1)
        decoded_obs["Red cure"] = round(float(obs[847]), 1)
        decoded_obs["Find cure"] = round(float(obs[848]), 1)
        return decoded_obs

    def get_observation(self):
        """
        Returns a vector representation of the game state.
        """
        obs = {}
        find_cure, share_knowledge, share_knowledge_location = self.current_player.goal

        for city in self.cities.values():
            partial_obs = []
            if share_knowledge and share_knowledge_location == city.name:
                partial_obs.append(1)
            else:
                partial_obs.append(0)
            partial_obs.append(city.color_encoder / 2)
            partial_obs.append(city.infection_yellow / 3)
            partial_obs.append(city.infection_blue / 3)
            partial_obs.append(city.infection_red / 3)
            partial_obs.append(1 if city.name in self.player_1.hand else 0)
            partial_obs.append(1 if city.name == self.player_1.loc.name else 0)
            partial_obs.append(1 if city.name in self.player_2.hand else 0)
            partial_obs.append(1 if city.name == self.player_2.loc.name else 0)
            partial_obs.append(1 if city.name in self.board.infection_discard_pile else 0)
            partial_obs.append(1 if city.name in self.board.player_discard_pile else 0)
        
            for other_city in self.cities.values():
                if city.name == other_city.name:
                    partial_obs.append(0)
                else:
                    partial_obs.append(nx.shortest_path_length(self.graph, city.name, other_city.name) / 8)
            
            obs[city.name] = partial_obs

        obs["Game round"] = self.game_round / 10
        obs["Player id"] = self.current_player.id - 1
        obs["Player turn"] = self.actions_taken / 4
        obs["Outbreak count"] = self.board.outbreak_count / 4
        obs["Infection rate"] = self.board.infection_rate / 3
        obs["Yellow cure"] = self.board.yellow_cure
        obs["Blue cure"] = self.board.blue_cure
        obs["Red cure"] = self.board.red_cure
        obs["Find cure"] = (1 if find_cure else 0)

        obs_data = []
        for _, value in obs.items():
            if isinstance(value, list):
                obs_data.extend(value)
            else:
                obs_data.append(value)

        obs_data = np.array(obs_data, dtype=np.float32)

        # print(obs_data)

        # Encode player locations
        return obs_data

def main():

    # Initialize the environment
    env = PandemicEnv()

    # Initialize the greedy agent
    greedy_agent = GreedyAgent(env)

    # Run the greedy agent for 50 episodes
    greedy_agent.play(episodes=100)

    print(f"Win rate: {env.win_score.count(1)*100 / len(env.win_score)}%")
    env.close()

if __name__ == "__main__":
    main()