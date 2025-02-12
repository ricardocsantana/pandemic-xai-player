import gymnasium as gym
from gymnasium import spaces
import numpy as np
from board import Board
from location import City
from player import Player
from render import Renderer
from greedy import GreedyAgent
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
        self.observation_space = spaces.Box(low=0, high=1, shape=(248,), dtype=np.float32)

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
            
            h_value = evaluator.h_state(1, None)
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

        self.players = [self.player_1, self.player_2]

        self.board.draw_epidemic_deck(self.cities, n_draws=2, n_cubes=3)
        self.board.draw_epidemic_deck(self.cities, n_draws=2, n_cubes=2)
        self.board.draw_epidemic_deck(self.cities, n_draws=2, n_cubes=1)
        
        self.current_player = self.player_1
        self.actions_taken = 0  # Reset action counter
        self.game_number += 1  # Increment game number
        self.prev_outbreak_count = 0
        self.prev_cure_prob = self.find_cure_prob()
        self.game_round = 0

        return self.get_observation(), {}

    def step(self, action_idx):
        """
        Executes a single action and updates the game state.
        Each player takes 4 actions per turn.
        """
    
        done = False

        self.current_player.previous_loc = self.current_player.loc.name
        self.prev_cure_prob = self.find_cure_prob()

        action = self.current_player.all_actions[action_idx]
        self.current_player.take_action(action, self.board, self.cities)

        token = action.split()
        current_player_hand_by_color = [self.cities[card].color for card in self.current_player.hand]

        # 0: Minimize infection spread

        reward_dict = {}
        reward = 0

        #reward = - 0.05 * ((16-self.board.yellow_cubes) + (16 - self.#board.blue_cubes) + (16 - self.board.red_cubes))  # Penalize the player for not curing diseases

        # reward_dict["Infection spread"] = reward

        # A: Cure a disease
        reward_dict["Cure disease"] = 0
        
        if (current_player_hand_by_color.count("YELLOW") >= 4 and not self.board.yellow_cure) or \
            (current_player_hand_by_color.count("BLUE") >= 4 and not self.board.blue_cure) or \
            (current_player_hand_by_color.count("RED") >= 4 and not self.board.red_cure):
            advantage = nx.shortest_path_length(self.graph, self.current_player.previous_loc, "GENÈVE") - nx.shortest_path_length(self.graph, self.current_player.loc.name, "GENÈVE")
            if advantage > 0:
                reward += 0.2 * advantage
                reward_dict["Cure disease"] = 0.2 * advantage
            else:
                reward += 0.2 * advantage
                reward_dict["Cure disease"] = 0.2 * advantage

        if token[0] == "FIND":
            reward += 10
            reward_dict["Cure disease"] = 10

        # B: Find a cure

        elif token[0] == "SHARE":
            if self.find_cure_prob()[self.current_player.loc.color] > self.prev_cure_prob[self.current_player.loc.color]:
                reward_dict["Share know"] = 0.5
                reward += 0.5
            else:
                reward_dict["Share know"] = - 0.5
                reward -= 0.5
        elif token[0] == "DIRECT":
            if self.find_cure_prob()[COLORS[token[-1]]] < self.prev_cure_prob[COLORS[token[-1]]]:
                reward += - 0.5
                reward_dict["Direct fly"] = - 0.5
            elif not getattr(self.board, f"{COLORS[token[-1]].lower()}_cure"):
                reward += - 0.2
                reward_dict["Direct fly"] = - 0.2

        elif token[0] == "CHARTER":
            if self.find_cure_prob()[self.current_player.loc.color] < self.prev_cure_prob[self.current_player.loc.color]:
                reward += - 0.5
                reward_dict["Charter fly"] = - 0.5
            elif not getattr(self.board, f"{self.current_player.loc.color.lower()}_cure"):
                reward += - 0.2
                reward_dict["Charter fly"] = - 0.2

        # C: Treat a disease
        elif token[0] == "TREAT": 
            if getattr(self.current_player.loc, f"infection_{token[-1].lower()}") == 2:
                reward += 0.3
                reward_dict["Treat disease"] = 0.3
            elif getattr(self.current_player.loc, f"infection_{token[-1].lower()}") == 1:
                reward += 0.2
                reward_dict["Treat disease"] = 0.2
            elif getattr(self.current_player.loc, f"infection_{token[-1].lower()}") == 0:
                reward += 0.2
                reward_dict["Treat disease"] = 0.2
            else:
                raise ValueError(f"Invalid infection level: {getattr(self.current_player.loc, f'infection_{token[-1].lower()}')}", [token, self.current_player.loc.name])
        
        # D: Prevent outbreaks
        if self.board.outbreak_count > self.prev_outbreak_count:
            reward += - (self.board.outbreak_count - self.prev_outbreak_count)
            self.prev_outbreak_count = self.board.outbreak_count

        self.actions_taken += 1  # Increment action count

        # If 4 actions have been taken, switch turns and draw player cards
        if self.actions_taken == 4:
            self.actions_taken = 0  # Reset action counter
            self.board.draw_player_deck(self.current_player, self.cities)
            self.game_round += 1

            # Switch player turns
            self.current_player = self.player_2 if self.current_player == self.player_1 else self.player_1

            for city in self.cities.values():
                if city.infection_yellow > 3 \
                    or city.infection_blue > 3 \
                    or city.infection_red > 3:
                    print(action)
                    self.render()
                    raise ValueError(f"Invalid infection level: {self.board.player_deck, city.name, city.infection_yellow, city.infection_blue, city.infection_red}")
                    

            # reward += 0.01  # Reward the player for surviving a turn

        # Check win/loss conditions
        if self.board.check_win():
            reward = 10
            done = True
        elif self.board.check_loss():
            reward = -10
            done = True

        #for player in self.players:
            #if len(player.hand) > 6:
                #discard = self.select_discard(player.id, player.hand)
                #player.discard_cards(discard, self.board)

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
            decoded_obs[city.name] = [round(float(elem), 1) for elem in obs[idx*10:(idx+1)*10]]

        decoded_obs["Game round"] = round(float(obs[240]), 1)
        decoded_obs["Player id"] = round(float(obs[241]), 1)
        decoded_obs["Player turn"] = round(float(obs[242]), 1)
        decoded_obs["Outbreak count"] = round(float(obs[243]), 1)
        decoded_obs["Infection rate"] = round(float(obs[244]), 1)
        decoded_obs["Yellow cure"] = round(float(obs[245]), 1)
        decoded_obs["Blue cure"] = round(float(obs[246]), 1)
        decoded_obs["Red cure"] = round(float(obs[247]), 1)

        return decoded_obs

    def get_observation(self):
        """
        Returns a vector representation of the game state.
        """
        obs = {}

        for city in self.cities.values():
            partial_obs = []
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
            obs[city.name] = partial_obs

        obs["Game round"] = self.game_round / 10
        obs["Player id"] = self.current_player.id - 1
        obs["Player turn"] = self.actions_taken / 4
        obs["Outbreak count"] = self.board.outbreak_count / 4
        obs["Infection rate"] = self.board.infection_rate / 3
        obs["Yellow cure"] = self.board.yellow_cure
        obs["Blue cure"] = self.board.blue_cure
        obs["Red cure"] = self.board.red_cure

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