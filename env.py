import gymnasium as gym
from gymnasium import spaces
import numpy as np
from board import Board
from location import City
from player import Player
from render import Renderer
from greedy import GreedyAgent
from constants import CITIES, COLORS

class PandemicEnv(gym.Env):
    """
    Gymnasium-compatible environment for Pandemic: Hot Zone – Europe.
    """

    def __init__(self):
        super(PandemicEnv, self).__init__()

        self.renderer = Renderer()
        self.graph = self.renderer.graph
        self.win_score =[]

        # Track the number of actions taken in a turn
        self.actions_taken = 0
        self.game_number = 0

        # Define action space (number of possible actions)
        self.action_space = spaces.Discrete(24*3+7)

        # Define observation space (game state representation)
        self.observation_space = spaces.Box(low=0, high=1, shape=(222,), dtype=np.float32)

    def reset(self):
        """
        Resets the game state to start a new episode.
        """
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

        return self.get_observation()

    def step(self, action_idx):
        """
        Executes a single action and updates the game state.
        Each player takes 4 actions per turn.
        """

        # Render the state after each action
        self.render()

        action = self.current_player.all_actions[action_idx]
        self.current_player.take_action(action, self.board, self.cities)

        self.actions_taken += 1  # Increment action count

        # If 4 actions have been taken, switch turns and draw player cards
        if self.actions_taken == 4:
            self.actions_taken = 0  # Reset action counter
            self.board.draw_player_deck(self.current_player, self.cities)
            
            # Switch player turns
            self.current_player = self.player_2 if self.current_player == self.player_1 else self.player_1

        # Check win/loss conditions
        done = self.board.check_win() or self.board.check_loss()
        reward = 1 if self.board.check_win() else -1 if self.board.check_loss() else 0

        if done:
            self.win_score.append(reward)

        return self.get_observation(), reward, done, {}

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

    def get_observation(self):
        """
        Returns a vector representation of the game state.
        """
        obs = {}

        for city in self.cities.values():
            partial_obs = []
            partial_obs.append(city.infection_yellow / 3)
            partial_obs.append(city.infection_blue / 3)
            partial_obs.append(city.infection_red / 3)
            partial_obs.append(1 if city.name in self.player_1.hand else 0)
            partial_obs.append(1 if city == self.player_1.loc else 0)
            partial_obs.append(1 if city.name in self.player_2.hand else 0)
            partial_obs.append(1 if city == self.player_2.loc else 0)
            partial_obs.append(1 if city.name in self.board.infection_discard_pile else 0)
            partial_obs.append(1 if city.name in self.board.player_discard_pile else 0)
            obs[city.name] = partial_obs

        obs["Player turn"] = self.current_player.id - 1
        obs["Outbreak count"] = self.board.outbreak_count / 3
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