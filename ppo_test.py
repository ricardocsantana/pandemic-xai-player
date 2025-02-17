import gymnasium as gym
import numpy as np
from env import PandemicEnv
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from datetime import datetime


# MaskablePPO behaves the same as SB3's PPO unless the env is wrapped
# with ActionMasker. If the wrapper is detected, the masks are automatically
# retrieved and used when learning. Note that MaskablePPO does not accept
# a new action_mask_fn kwarg, as it did in an earlier draft.
model = MaskablePPO.load("./ppo/models/ppo_pandemic-20250217-235210", env=PandemicEnv())

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
        print(env.current_player.id, env.current_player.all_actions[action], env.current_player.goal)
        obs, reward, terminated, truncated, info = env.step(action)
        print("--------------------")
        for key, value in env.decode_obs(obs).items():
            print(key+"-"*(14-len(key)), value)
        print(info)
        print(reward)
        print("--------------------")