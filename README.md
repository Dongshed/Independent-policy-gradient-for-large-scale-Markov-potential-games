# Independent-policy-gradient-for-large-scale-Markov-potential-games

Copyright (c) [2022] 
[Dongsheng Ding, Chen-Yu Wei, Kaiqing Zhang, and Mihailo Jovanovic]
All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

====================================================================================

Acknowledgment

The code of creating simulation environment and the standard policy gradient algorithm are from:

Leonardos S, Overman W, Panageas I, Piliouras G. Global Convergence of Multi-Agent Policy Gradient in Markov Potential Games. International Conference on Learning Representations 2021.

====================================================================================

# Description

MPG_experiments in the ICML 2022 paper (Link to the paper: https://arxiv.org/abs/2202.04129): 

    Independent policy gradient for large-scale Markov potential games: Sharper rates, function approximation, and game-agnostic convergence

The codes generate the comparison plots in the computational experiments section and appendix. 
 
# Main File:

1. congestionMPG_unif_plots.py: this code compares the policy gradient algorithm (Leonardos, et al, 2022 ICLR) and our projected Q-ascent algorithm. For each policy profile, it has subroutines that estimate the discounted visitation distribution, the value function (of each agent), and the Q-function (of each agent). The stopping criterion is that two successive updates in the policy space do not differ more than a constant in the L1-norm. The constant that we used in the experiments is 10e-16.

# Auxiliary Files:

1. projection_simplex.py: this code does the projection to the simplex in the projected gradient ascent (policy gradient) updates.
This file is due to: https://gist.github.com/EdwardRaff/f4f4cf0c927c2addfb39

2. congestion_games.py: this code creates the class "Congestion Game". Each Congestion Game comprises a set of players, a set of facilities (that the players can choose from), and a set of weights (one for each facility). The methods of the Class and the additional functions mainly aim to calculate the agents' rewards (which in these instances are equal to the number of players at each facility times the weight of that facility).

# Other Files:

The files congestionMPG_deg1 and congestionMPG_deg2 repeat our comparison experiments for degenerate initial state distributions that are shown in the supplementary material. 
