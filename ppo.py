import gymnasium as gym
import numpy as np
from env import PandemicEnv
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from datetime import datetime


def mask_fn(env: gym.Env) -> np.ndarray:
    # Do whatever you'd like in this function to return the action mask
    # for the current env. In this example, we assume the env has a
    # helpful method we can rely on.
    # print(env.valid_action_mask())
    return env.valid_action_mask()


env = PandemicEnv()  # Initialize env
env = ActionMasker(env, mask_fn)  # Wrap to enable masking

# Define a larger network architecture:
policy_kwargs = dict(
    net_arch={
        "pi": [1024, 1024, 1024],  # Three hidden layers for the policy network
        "vf": [1024, 1024, 1024]   # Three hidden layers for the value network
    }
)

# MaskablePPO behaves the same as SB3's PPO unless the env is wrapped
# with ActionMasker. If the wrapper is detected, the masks are automatically
# retrieved and used when learning. Note that MaskablePPO does not accept
# a new action_mask_fn kwarg, as it did in an earlier draft.
model = MaskablePPO(MaskableActorCriticPolicy, env, verbose=1, tensorboard_log="./ppo/", policy_kwargs=policy_kwargs)
model.learn(100_000, progress_bar=True)
model.save("./ppo/models/ppo_pandemic-{}".format(datetime.now().strftime("%Y%m%d-%H%M%S")))

# Note that use of masks is manual and optional outside of learning,
# so masking can be "removed" at testing time
# model.predict(observation, action_masks=valid_action_array)

for _ in range(100):
    env = PandemicEnv()
    obs, _ = env.reset()
    terminated = False
    while not terminated:
        # Render the state after each action
        env.render()
        action, _states = model.predict(obs, action_masks=env.valid_action_mask())
        print(env.current_player.id, env.current_player.all_actions[action])
        obs, reward, terminated, truncated, info = env.step(action)
        print("--------------------")
        for key, value in env.decode_obs(obs).items():
            print(key+"-"*(14-len(key)), value)
        print(info)
        print(reward)
        print("--------------------")