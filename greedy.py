import copy
from state_eval import StateEvaluator

class GreedyAgent:
    """
    A greedy agent that picks the action with the lowest heuristic value.
    """

    def __init__(self, env):
        self.env = env

    def select_action(self):
        """
        Evaluates all actions and selects the one with the lowest heuristic value.
        """
        best_action = None
        best_value = float("inf")
        _, allowed_actions = self.env.current_player.action_mask(self.env.board, self.env.cities)

        for idx, action in enumerate(self.env.current_player.all_actions):
            if action not in allowed_actions:
                continue
            temp_env = copy.deepcopy(self.env)
            temp_env.current_player.take_action(action, temp_env.board, temp_env.cities)
            evaluator = StateEvaluator(action, temp_env.board, temp_env.current_player,
                                       [temp_env.player_1, temp_env.player_2], temp_env.graph, temp_env.cities)
            h_value = evaluator.h_state()
            if h_value < best_value:
                best_value = h_value
                best_action = idx

        return best_action

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
                    obs, reward, done, _ = self.env.step(action)
                    
                    if done:
                        print(f"Game ended with reward: {reward}")
                        break