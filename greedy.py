import copy
import itertools
from state_eval import StateEvaluator

class GreedyAgent:
    """
    A greedy agent that picks the action with the lowest heuristic value.
    """

    def __init__(self, env):
        self.env = env

    def choose_player_goal(self, player_hand, cities):

        treat_yellow_disease = False
        treat_blue_disease = False
        treat_red_disease = False

        player_hand_by_color = [cities[city].color for city in player_hand]

        if not self.env.board.yellow_cure:
            treat_yellow_disease = 1 if player_hand_by_color.count("YELLOW") >= 4 else 0
            # print("YELLOW", treat_yellow_disease)
        if not self.env.board.blue_cure:
            treat_blue_disease = 1 if player_hand_by_color.count("BLUE") >= 4 else 0
            # print("BLUE", treat_blue_disease)
        if not self.env.board.red_cure:
            treat_red_disease = 1 if player_hand_by_color.count("RED") >= 4 else 0
            # print("RED", treat_red_disease)

        treat_disease = treat_yellow_disease or treat_blue_disease or treat_red_disease

        # print(treat_disease)
        return treat_disease

    def select_action(self):
        """
        Evaluates all actions and selects the one with the lowest heuristic value.
        """
        best_action = None
        best_action_idx = None
        best_value = float("inf")
        _, allowed_actions = self.env.current_player.action_mask(self.env.board, self.env.cities)
        goal = self.choose_player_goal(self.env.current_player.hand, self.env.cities)
        if goal:
            print(f"Player {self.env.current_player.id} is trying to cure a disease.")

        for idx, action in enumerate(self.env.current_player.all_actions):
            if action not in allowed_actions:
                continue
            temp_env = copy.deepcopy(self.env)
            temp_env.current_player.take_action(action, temp_env.board, temp_env.cities)
            evaluator = StateEvaluator(temp_env.board, temp_env.current_player,
                                        [temp_env.player_1, temp_env.player_2], temp_env.graph, temp_env.cities)
            h_value = evaluator.h_state(goal, action)
            if h_value < best_value:
                best_value = h_value
                best_action = action
                best_action_idx = idx

        # print(best_action)
        
        return best_action_idx

    def play(self, episodes=1):
        """
        Runs the greedy agent for a given number of episodes.
        """
        for i in range(episodes):
            print(f"Starting episode {i + 1}")
            obs = self.env.reset()
            done = False

            while not done:
                for _ in range(4):  # Take 4 actions per turn
                    action = self.select_action()
                    self.env.render()
                    obs, reward, done, _, _ = self.env.step(action)
                    
                    if done:
                        print(f"Game ended with reward: {reward}")
                        break