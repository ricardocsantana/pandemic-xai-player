import copy
from state_eval import StateEvaluator
import networkx as nx

class GreedyAgent:
    """
    A greedy agent that picks the action with the lowest heuristic value.
    """

    def __init__(self, env):
        self.env = env


    import networkx as nx

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
                if getattr(self.env.board, f"{color.lower()}_cure"):
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
                        graph, candidate_city, self.env.current_player.loc.name
                    )
                    dist_partner = nx.shortest_path_length(
                        graph, candidate_city, self.env.current_player.partner.loc.name
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

        if not self.env.board.yellow_cure:
            treat_yellow_disease = 1 if list(current_player_hand_by_color.values()).count("YELLOW") >= 4 else 0
        if not self.env.board.blue_cure:
            treat_blue_disease = 1 if list(current_player_hand_by_color.values()).count("BLUE") >= 4 else 0
        if not self.env.board.red_cure:
            treat_red_disease = 1 if list(current_player_hand_by_color.values()).count("RED") >= 4 else 0

        treat_disease = treat_yellow_disease or treat_blue_disease or treat_red_disease

        if treat_disease:
            return treat_disease, share_knowledge, share_knowledge_location
        
        share_knowledge, share_knowledge_location = self.set_share_location(current_player_hand_by_color, partner_player_hand_by_color, graph)
        if share_knowledge:
            return treat_disease, share_knowledge, share_knowledge_location
        
        return treat_disease, share_knowledge, share_knowledge_location

    def _evaluate_state(self, env, goal):
        """
        Evaluate the given state's heuristic with respect to a *fixed* goal.
        """
        # Use your existing StateEvaluator
        evaluator = StateEvaluator(
            env.board, 
            env.current_player, 
            [env.player_1, env.player_2], 
            env.graph, 
            env.cities
        )
        return evaluator.h_state(goal)

    def _dfs_4_level(self, env, depth, action_sequence, goal, best_value, best_sequence):
        """
        Depth-limited DFS that explores up to 4 actions. 
        Returns an updated (best_value, best_sequence).
        """

        # Switch player turns
        if depth == 4:
            env.current_player = env.player_2 if env.current_player == env.player_1 else env.player_1
            # Compute the goal once
            goal = self.choose_player_goal(
            self.env.current_player.hand,
            self.env.current_player.partner.hand,
            self.env.cities, 
            self.env.graph
        )

        if depth == 8:
            h_value = self._evaluate_state(env, goal)
            if h_value < best_value:
                return h_value, action_sequence
            else:
                return best_value, best_sequence

        # Find which actions are valid in the current state
        _, allowed_actions = env.current_player.action_mask(env.board, env.cities)

        # 1) Evaluate each action's immediate score
        action_scores = []
        for action in allowed_actions:
            temp_env = copy.deepcopy(env)
            temp_env.current_player.take_action(action, temp_env.board, temp_env.cities)
            score = self._evaluate_state(temp_env, goal)
            action_scores.append((action, score))

        # 2) Sort actions by score (ascending)
        action_scores.sort(key=lambda x: x[1])

        # Explore each allowed action
        for action, _ in action_scores[:3]:
            # Copy the environment so as not to disturb the real one
            temp_env = copy.deepcopy(env)
            # Apply the action
            temp_env.current_player.take_action(action, temp_env.board, temp_env.cities)

            # Recurse
            new_value, new_sequence = self._dfs_4_level(
                temp_env, 
                depth + 1, 
                action_sequence + [action], 
                goal,
                best_value,
                best_sequence
            )

            # Update the best if the new one is better
            if new_value < best_value:
                best_value = new_value
                best_sequence = new_sequence

        return best_value, best_sequence

    def select_best_4step_sequence(self):
        """
        Determines the single best sequence of up to 4 actions, 
        based on the final state's heuristic value w.r.t. a fixed goal.
        """
        # Compute the goal once
        goal = self.choose_player_goal(
            self.env.current_player.hand,
            self.env.current_player.partner.hand,
            self.env.cities, 
            self.env.graph
        )

        # Start the DFS at depth=0, with an empty sequence, 
        # and best initialized to infinity
        best_value, best_sequence = self._dfs_4_level(
            env=self.env,
            depth=0,
            action_sequence=[],
            goal=goal,
            best_value=float('inf'),
            best_sequence=[]
        )

        return best_sequence


    def play(self, episodes=1):
        """
        Runs the agent for a given number of episodes,
        using the 4-step lookahead strategy.
        """
        for i in range(episodes):
            print(f"Starting episode {i + 1}")
            obs = self.env.reset()
            done = False

            while not done:
                # 1) Get the "best" sequence of up to 4 actions.
                action_sequence = self.select_best_4step_sequence()
                print(f"Best action sequence: {action_sequence}")
                action_sequence_idx = [self.env.current_player.all_actions.index(action) for action in action_sequence]

                # 2) Execute each action in that sequence, stopping if game ends.
                for action in action_sequence_idx:
                    obs, reward, done, _, _ = self.env.step(action)
                    self.env.render()

                    if done:
                        print(f"Game ended with reward: {reward}")
                        break
