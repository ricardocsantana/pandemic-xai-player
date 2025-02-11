import copy
import itertools
from state_eval import StateEvaluator

class GreedyAgent:
    """
    A greedy agent that picks the action with the lowest heuristic value.
    """

    def __init__(self, env):
        self.env = env

    def check_hands(self, player_1, player_2, color, cities):

        player_1_hand_by_color = [cities[city].color for city in player_1.hand]
        player_2_hand_by_color = [cities[city].color for city in player_2.hand]

        if player_1_hand_by_color.count(color) >= 4:
            return True
        elif player_1_hand_by_color.count(color) == 3 and player_2_hand_by_color.count(color) >= 1:
            return True
        elif player_2_hand_by_color.count(color) >= 4:
            return True
        elif player_2_hand_by_color.count(color) == 3 and player_1_hand_by_color.count(color) >= 1:
            return True
        else:
            return False

    def choose_player_goal(self):

        treat_yellow_disease = False
        treat_blue_disease = False
        treat_red_disease = False

        if not self.env.board.yellow_cure:
            treat_yellow_disease = self.check_hands(self.env.player_1, self.env.player_2, "YELLOW", self.env.cities)
            # print("YELLOW", treat_yellow_disease)
        if not self.env.board.blue_cure:
            treat_blue_disease = self.check_hands(self.env.player_1, self.env.player_2, "BLUE", self.env.cities)
            # print("BLUE", treat_blue_disease)
        if not self.env.board.red_cure:
            treat_red_disease = self.check_hands(self.env.player_1, self.env.player_2, "RED", self.env.cities)
            # print("RED", treat_red_disease)

        treat_disease = treat_yellow_disease or treat_blue_disease or treat_red_disease

        # print(treat_disease)
        return treat_disease
    
    def select_discard(self, player_id, player_hand):
        n_discard = len(player_hand) - 6
        best_cards = None
        best_value = float("inf")
        
        for cards in list(itertools.combinations(player_hand, n_discard)):
            temp_env = copy.deepcopy(self.env)
            temp_env.players[player_id-1].discard_cards(cards, temp_env.board)

            evaluator = StateEvaluator(temp_env.board, temp_env.current_player,
                        temp_env.players, temp_env.graph, temp_env.cities)
            
            h_value = evaluator.h_state(1)
            if h_value < best_value:
                best_value = h_value
                best_cards = cards

        return best_cards
        

    def select_action(self):
        """
        Evaluates all actions and selects the one with the lowest heuristic value.
        """
        best_action = None
        best_value = float("inf")
        _, allowed_actions = self.env.current_player.action_mask(self.env.board, self.env.cities)
        goal = self.choose_player_goal()

        for idx, action in enumerate(self.env.current_player.all_actions):
            if action not in allowed_actions:
                continue
            temp_env = copy.deepcopy(self.env)
            temp_env.current_player.take_action(action, temp_env.board, temp_env.cities)
            evaluator = StateEvaluator(temp_env.board, temp_env.current_player,
                                       [temp_env.player_1, temp_env.player_2], temp_env.graph, temp_env.cities)
            h_value = evaluator.h_state(goal)
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

                    for player in self.env.players:
                        if len(player.hand) > 6:
                            discard = self.select_discard(player.id, player.hand)
                            player.discard_cards(discard, self.env.board)
                            print(f"Player {player.id} discarded {discard}")
                    
                    if done:
                        print(f"Game ended with reward: {reward}")
                        break