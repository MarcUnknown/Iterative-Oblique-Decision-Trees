import time
import copy
import numpy as np
import oracle_utils as o_utils
from Results import utils as p_utils
from sklearn.tree import DecisionTreeRegressor
from Initializing.Oracles import load_oracle as lo
from Initializing.Environments import load_environment as le

if __name__ == "__main__":
    max_depth = 10
    numb_runs = 10
    numb_eps = 100
    numb_trees = 10
    numb_samples = int(3e4)
    time_run = np.zeros(numb_runs)
    time_cart = np.zeros((max_depth, numb_runs))
    samples_cart = np.zeros((max_depth, numb_runs))
    rewards_cart = np.zeros((max_depth, numb_runs))
    rewards_oracle = np.zeros((max_depth, numb_runs))
    best_carts = np.empty((max_depth, numb_runs), dtype=object)
    reward_threshold = le.Pendulumv1Environment().get_reward_threshold()
    pend_env = le.Pendulumv1Environment().get_environment()
    td3_pend = lo.TD3_Oracle().load_model(le.Pendulumv1Environment().get_environmentShort())

    print(
        "----------------------Starting experiment for Pendulum-v1 Episode samples with CART----------------------"
    )
    for k in range(numb_runs):
        time_start_run = time.time()
        pend_samples, rewards = o_utils.evaluate_oracle_pend_steps(
            model=td3_pend, env=pend_env, num_samples=numb_samples
        )
        pend_samples = pend_samples.sample(n=numb_samples)
        print(f"Oracle performance: {np.mean(rewards)} +/- {np.std(rewards)}")
        for i in range(max_depth):
            best_cart, best_reward, best_std = None, -np.inf, -np.inf
            time_start_cart = time.time()
            for j in range(numb_trees):
                pend_cart = DecisionTreeRegressor(max_depth=i + 1)
                pend_cart.fit(pend_samples.iloc[:, :-1].values, pend_samples.iloc[:, -1].values)
                _, cart_rewards = p_utils.eval_cart_reg(
                    tree=pend_cart,
                    env=pend_env,
                    columns=pend_samples.columns,
                    num_episodes=numb_eps,
                )
                if np.mean(cart_rewards) > best_reward:
                    best_cart, best_reward, best_std = (
                        pend_cart,
                        np.mean(cart_rewards),
                        np.std(cart_rewards),
                    )
            time_cart[i, k] = time.time() - time_start_cart
            rewards_cart[i, k] = best_reward
            rewards_oracle[i, k] = np.mean(rewards)
            best_carts[i, k] = copy.deepcopy(best_cart)
            samples_cart[i, k] = numb_samples
            print(
                f"CART with a depth of {i+1} with a reward of: {best_reward} +/- {best_std}"
            )
        time_run[k] = time.time() - time_start_run
    p_utils.save_results("Pendulum-v1", rewards_cart, rewards_oracle, method="CART")
    p_utils.save_best_cart(
        best_carts, rewards_cart, reward_threshold, env_name="Pendulum-v1", method="CART"
    )
    p_utils.save_timings_samples(
        time_run, time_cart, samples_cart, env_name="Pendulum-v1", method="CART"
    )
