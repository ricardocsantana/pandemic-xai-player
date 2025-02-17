from env import PandemicEnv

for _ in range(100):
    env = PandemicEnv()
    obs, _ = env.reset()
    action_space = env.players[0].all_actions
    terminated = False
    env.render()
    while not terminated:
        # Render the state after each action
        action = str(input("Enter action: ").strip().upper())
        action_idx = action_space.index(action)
        print(action_idx)
        print(env.valid_action_mask())
        if env.valid_action_mask()[action_idx]:  # Check if action is valid
            print(env.current_player.id, env.current_player.all_actions[action_idx])
            obs, reward, terminated, truncated, info = env.step(action_idx)
            print("--------------------")
            for key, value in env.decode_obs(obs).items():
                print(key+"-"*(14-len(key)), value)
            print(info)
            print(reward)
            print("--------------------")
            env.render()
        else:
            print("Invalid action")
            continue
    