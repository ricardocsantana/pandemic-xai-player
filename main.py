from env import PandemicEnv
from greedy import GreedyAgent

# Initialize the environment
env = PandemicEnv()

# Initialize the greedy agent
greedy_agent = GreedyAgent(env)

# Run the greedy agent for 5 episodes
greedy_agent.play(episodes=5)