from congestion_games import *
import matplotlib.pyplot as plt
import itertools
import numpy as np
import copy
import statistics
import seaborn as sns; sns.set()
from time import process_time

def projection_simplex_sort(v, z=1):
	# Courtesy: EdwardRaff/projection_simplex.py
    if v.sum() == z and np.alltrue(v >= 0):
        return v
    n_features = v.shape[0]
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - z
    ind = np.arange(n_features) + 1
    cond = u - cssv / ind > 0
    rho = ind[cond][-1]
    theta = cssv[cond][-1] / float(rho)
    w = np.maximum(v - theta, 0)
    return w

# Define the states and some necessary info
N = 8 #number of agents
harm = - 100 * N # pentalty for being in bad state

safe_state = CongGame(N,1,[[1,0],[2,0],[4,0],[6,0]])
bad_state = CongGame(N,1,[[1,-100],[2,-100],[4,-100],[6,-100]])
state_dic = {0: safe_state, 1: bad_state}

M = safe_state.num_actions
M = int(M)
D = safe_state.m #number facilities
S = 2

# Dictionary to store the action profiles and rewards to
selected_profiles = {}

# Dictionary associating each action (value) to an integer (key)
act_dic = {}
counter = 0
for act in safe_state.actions:
	act_dic[counter] = act 
	counter += 1

def get_next_state(state, actions):
    acts_from_ints = [act_dic[i] for i in actions]
    density = state_dic[state].get_counts(acts_from_ints)
    max_density = max(density)

    if state == 0 and max_density > N/2 or state == 1 and max_density > N/4:
      # if state == 0 and max_density > N/2 and np.random.uniform() > 0.2 or state == 1 and max_density > N/4 and np.random.uniform() > 0.1:
        return 1
    return 0

def pick_action(prob_dist):
    # np.random.choice(range(len(prob_dist)), 1, p = prob_dist)[0]
    acts = [i for i in range(len(prob_dist))]
    action = np.random.choice(acts, 1, p = prob_dist)
    return action[0]

def visit_dist(state, policy, gamma, T,samples):
    # This is the unnormalized visitation distribution. Since we take finite trajectories, the normalization constant is (1-gamma**T)/(1-gamma).
    visit_states = {st: np.zeros(T) for st in range(S)}        
    for i in range(samples):
        curr_state = state
        for t in range(T):
            visit_states[curr_state][t] += 1
            actions = [pick_action(policy[curr_state, i]) for i in range(N)]
            curr_state = get_next_state(curr_state, actions)
    dist = [np.dot(v/samples,gamma**np.arange(T)) for (k,v) in visit_states.items()]
    return dist 

def value_function(policy, gamma, T,samples):
    value_fun = {(s,i):0 for s in range(S) for i in range(N)}
    for k in range(samples):
        for state in range(S):
            curr_state = state
            for t in range(T):
                actions = [pick_action(policy[curr_state, i]) for i in range(N)]
                q = tuple(actions+[curr_state])
                rewards = selected_profiles.setdefault(q,get_reward(state_dic[curr_state], [act_dic[i] for i in actions]))                  
                for i in range(N):
                    value_fun[state,i] += (gamma**t)*rewards[i]
                curr_state = get_next_state(curr_state, actions)
    value_fun.update((x,v/samples) for (x,v) in value_fun.items())
    return value_fun

def Q_function(agent, state, action, policy, gamma, value_fun, samples):
    tot_reward = 0
    for i in range(samples):
        actions = [pick_action(policy[state, i]) for i in range(N)]
        actions[agent] = action
        q = tuple(actions+[state])
        rewards = selected_profiles.setdefault(q,get_reward(state_dic[state], [act_dic[i] for i in actions]))
        tot_reward += rewards[agent] + gamma*value_fun[get_next_state(state, actions), agent]
    return (tot_reward / samples)

def policy_accuracy(policy_pi, policy_star):
    total_dif = N * [0]
    for agent in range(N):
        for state in range(S):
            total_dif[agent] += np.sum(np.abs((policy_pi[state, agent] - policy_star[state, agent])))
	  # total_dif[agent] += np.sqrt(np.sum((policy_pi[state, agent] - policy_star[state, agent])**2))
    return np.sum(total_dif) / N

def policy_gradient(mu, max_iters, gamma, eta, T, samples):

    policy = {(s,i): [1/M]*M for s in range(S) for i in range(N)}
    policy_hist = [copy.deepcopy(policy)]

    value_fun_avg = 0

    for t in range(max_iters):

        #print(t)

        b_dist = M * [0]
        for st in range(S):
            a_dist = visit_dist(st, policy, gamma, T, samples)
            b_dist[st] = np.dot(a_dist, mu)
            
        grads = np.zeros((N, S, M))
        value_fun = value_function(policy, gamma, T, samples)

        value_fun_avg += sum(value_fun.values()) / float(len(value_fun)) / float(max_iters)

        for agent in range(N):
            for st in range(S):
                for act in range(M):
                    grads[agent, st, act] = b_dist[st] * Q_function(agent, st, act, policy, gamma, value_fun, samples)
                    # grads[agent, st, act] = Q_function(agent, st, act, policy, gamma, value_fun, samples)

        for agent in range(N):
            for st in range(S):
                policy[st, agent] = projection_simplex_sort(np.add(policy[st, agent], eta * grads[agent,st]), z=1)
        policy_hist.append(copy.deepcopy(policy))

        if policy_accuracy(policy_hist[t], policy_hist[t-1]) < 10e-16:
      # if policy_accuracy(policy_hist[t+1], policy_hist[t]) < 10e-16: (it makes a difference, not when t=0 but from t=1 onwards.)
            print(value_fun_avg)
            return policy_hist

    print(value_fun_avg)
    return policy_hist


def policy_gradientQ(mu, max_iters, gamma, eta, T, samples):
    policy = {(s, i): [1 / M] * M for s in range(S) for i in range(N)}
    policy_hist = [copy.deepcopy(policy)]

    value_fun_avg = 0

    for t in range(max_iters):

        # print(t)

        # b_dist = M * [0]
        # for st in range(S):
        #     a_dist = visit_dist(st, policy, gamma, T, samples)
        #     b_dist[st] = np.dot(a_dist, mu)

        grads = np.zeros((N, S, M))
        value_fun = value_function(policy, gamma, T, samples)

        value_fun_avg += sum(value_fun.values()) / float(len(value_fun)) / float(max_iters)

        for agent in range(N):
            for st in range(S):
                for act in range(M):
                    grads[agent, st, act] = Q_function(agent, st, act, policy, gamma, value_fun, samples)

        for agent in range(N):
            for st in range(S):
                policy[st, agent] = projection_simplex_sort(np.add(policy[st, agent], eta * grads[agent, st]), z=1)
        policy_hist.append(copy.deepcopy(policy))

        if policy_accuracy(policy_hist[t], policy_hist[t - 1]) < 10e-16:
            # if policy_accuracy(policy_hist[t+1], policy_hist[t]) < 10e-16: (it makes a difference, not when t=0 but from t=1 onwards.)
            print(value_fun_avg)
            return policy_hist

    print(value_fun_avg)
    return policy_hist

def get_accuracies(policy_hist):
    fin = policy_hist[-1]
    accuracies = []
    for i in range(len(policy_hist)):
        this_acc = policy_accuracy(policy_hist[i], fin)
        accuracies.append(this_acc)
    return accuracies

def full_experiment(runs,iters,eta,T,samples,flagQ):

    # print('S, M: ', S, M)
    densities = np.zeros((S,M))

    raw_accuracies = []
    for k in range(runs):
        if flagQ == 0:
            policy_hist = policy_gradient([0.9999, 0.0001],iters,0.99,eta,T,samples)
        if flagQ == 1:
            policy_hist = policy_gradientQ([0.9999, 0.0001], iters, 0.99, eta, T, samples)

        raw_accuracies.append(get_accuracies(policy_hist))

        converged_policy = policy_hist[-1]
        for i in range(N):
            for s in range(S):
                densities[s] += converged_policy[s,i]

    densities = densities / runs

    return densities, raw_accuracies


# main program
# policy_gradient
myp_start = process_time()
flagQ = 0
[densities, raw_accuracies] = full_experiment(3,1000,0.0001,20,10,flagQ)
myp_end = process_time()
elapsed_time = myp_end - myp_start
print(elapsed_time)

# policy_gradientQ
myp_start = process_time()
flagQ = 1
[densitiesQ, raw_accuraciesQ] = full_experiment(3,1000,0.001,20,10,flagQ)
myp_end = process_time()
elapsed_time = myp_end - myp_start
print(elapsed_time)


# plots
plot_accuracies = np.array(list(itertools.zip_longest(*raw_accuracies, fillvalue=np.nan))).T
piters = list(range(plot_accuracies.shape[1]))
plot_accuraciesQ = np.array(list(itertools.zip_longest(*raw_accuraciesQ, fillvalue=np.nan))).T
pitersQ = list(range(plot_accuraciesQ.shape[1]))
clrs = sns.color_palette("husl", 3)

fig2 = plt.figure(figsize=(6, 4))
for i in range(len(plot_accuracies)):
    plt.plot(piters, plot_accuracies[i],'--')
for i in range(len(plot_accuraciesQ)):
    plt.plot(pitersQ, plot_accuraciesQ[i],'-')
plt.grid(linewidth=0.6)
# plt.gca().set(xlabel='Iterations',ylabel='L1-accuracy', title='Policy Gradient: agents = {}, runs = {}, $\eta$ = {}'.format(N, runs,eta))
plt.show()
fig2.savefig('Fig_individual_runs_n{}_deg1_1.png'.format(N), bbox_inches='tight')

plot_accuracies = np.nan_to_num(plot_accuracies)
pmean = list(map(statistics.mean, zip(*plot_accuracies)))
pstdv = list(map(statistics.stdev, zip(*plot_accuracies)))

plot_accuraciesQ = np.nan_to_num(plot_accuraciesQ)
pmeanQ = list(map(statistics.mean, zip(*plot_accuraciesQ)))
pstdvQ = list(map(statistics.stdev, zip(*plot_accuraciesQ)))


fig1 = plt.figure(figsize=(6, 4))
ax = sns.lineplot(piters, pmean, color=clrs[0])  # label= 'Mean L1-accuracy'
ax.fill_between(piters, np.subtract(pmean, pstdv), np.add(pmean, pstdv), alpha=0.3,
                facecolor=clrs[0])  # label="1-standard deviation"
ax = sns.lineplot(pitersQ, pmeanQ, color=clrs[1])  # label= 'Mean L1-accuracy'
ax.fill_between(pitersQ, np.subtract(pmeanQ, pstdvQ), np.add(pmeanQ, pstdvQ), alpha=0.3,
                facecolor=clrs[1])  # label="1-standard deviation"
ax.legend()
plt.grid(linewidth=0.6)
# plt.gca().set(xlabel='Iterations',ylabel='L1-accuracy', title='Policy Gradient: agents = {}, runs = {}, $\eta$ = {}'.format(N, runs,eta))
plt.show()
fig1.savefig('Fig_avg_runs_n{}_deg1_1.png'.format(N), bbox_inches='tight')
# plt.close()

# print(densities)


fig3, ax = plt.subplots()
index = np.arange(D)
bar_width = 0.35
opacity = 1

# print(len(index))
# print(len(densities[0]))
rects1 = plt.bar(index, densities[0], bar_width,
                 alpha=.7 * opacity,
                 color='b',
                 label='Safe state')

rects2 = plt.bar(index + bar_width, densities[1], bar_width,
                 alpha=opacity,
                 color='r',
                 label='Distancing state')

# plt.gca().set(xlabel='Facility',ylabel='Average number of agents', title='Policy Gradient: agents = {}, runs = {}, $\eta$ = {}'.format(N,runs,eta))
plt.xticks(index + bar_width / 2, ('A', 'B', 'C', 'D'))
plt.legend()
fig3.savefig('Fig_facilities_n{}_deg1_1.png'.format(N), bbox_inches='tight')
# plt.close()
plt.show()


fig4, ax = plt.subplots()
index = np.arange(D)
bar_width = 0.35
opacity = 1

# print(len(index))
# print(len(densities[0]))
rects1 = plt.bar(index, densitiesQ[0], bar_width,
                 alpha=.7 * opacity,
                 color='k',
                 label='Safe state')

rects2 = plt.bar(index + bar_width, densitiesQ[1], bar_width,
                 alpha=opacity,
                 color='r',
                 label='Distancing state')

# plt.gca().set(xlabel='Facility',ylabel='Average number of agents', title='Policy Gradient: agents = {}, runs = {}, $\eta$ = {}'.format(N,runs,eta))
plt.xticks(index + bar_width / 2, ('A', 'B', 'C', 'D'))
plt.legend()
fig4.savefig('Fig_facilitiesQ_n{}_deg1_1.png'.format(N), bbox_inches='tight')
# plt.close()
plt.show()
