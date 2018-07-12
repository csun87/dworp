import numpy as np
import igraph
import dworp
import dworp.plot
import logging
import argparse


class Person(dworp.Agent):
    def __init__(self, vertex, traits):
        super().__init__(vertex.index, 13)
        vertex['agent'] = self
        self.vertex = vertex
        self.state = traits
        self.personality_inds = range(0, 5)
        self.demographics_inds = range(5, 10)
        self.changeables_inds = range(10, 13)

    # def init(self, now, env):

    def step(self, now, env):
        neighbors = self.vertex.neighbors()
        eating_out = []
        env_aware = []
        social = []
        for i in range(0, len(neighbors)):
            nvert = neighbors[i]
            nstate = nvert["agent"].state
            eating_out.append(nstate[1])
            env_aware.append(nstate[2])
            social.append(nstate[14])
        new_eo = min((1/(1+(1+self.state.traits[15])*sum(social))))
        # I don't know how to do this according to the formula

    def complete(self, now, env):
        pass


class StrawEnvironment(dworp.NetworkEnvironment):
    def __init__(self, network):
        super().__init__(1, network)

    def init(self, now):
        self.state.fill(0)

    def step(self, now, agents):
        pass


class StrawObserver(dworp.Observer):
    def __init__(self):
        pass

    def start(self, now, agents, env):
        pass

    def step(self, now, agents, env):
        pass

    def stop(self, now, agents, env):
        pass


class StrawTerminator(dworp.Terminator):
    def __init__(self):
        pass

    def test(self, now, agents, env):
        pass


def sample_agents(n=1000, num_friends=20):
    means = [0.466, 0.482, 0.504, 0.304, 0.544]
    mu = np.array(means)
    cov = np.zeros((5, 5))
    cov[0, :] = [0.384400, 0.073036, 0.057536, 0.091450, 0.096720]
    cov[1, :] = [0.073036, 0.384400, 0.061132, 0.062186, 0.000000]
    cov[2, :] = [0.057536, 0.061132, 0.336400, 0.037642, -0.020880]
    cov[3, :] = [0.091450, 0.062186, 0.037642, 0.348100, 0.095580]
    cov[4, :] = [0.096720, 0.000000, -0.020880, 0.095580, 0.360000]
    samples = np.random.multivariate_normal(mu, cov, n)
    offsets = np.random.random_sample((n, 1))
    lat = offsets + 78.6569
    offsets = np.random.random_sample((n, 1))
    long = offsets + 37.4316
    wealth = np.random.normal(300000, 100000, n)
    education = np.random.random_integers(0, 4, n)
    gender = np.random.random_integers(0, 1, n)
    cd = np.random.random_sample((n, 1))
    eo = np.random.random_sample((n, 1))
    ea = np.random.random_sample((n, 1))
    sa = np.random.random_sample((n, 1))
    rf = np.random.random_sample((n, 1))
    g = igraph.Graph(directed=True)
    for i in range(0, n):
        g.add_vertices(i)
    vs = g.vs
    agents = []
    for i in range(0, n):
        traits = np.zeros(16)
        traits[0] = 0
        traits[1] = eo[i]
        traits[2] = ea[i]
        traits[3:8] = samples[i, :]
        traits[8] = wealth[i]
        traits[9] = lat[i]
        traits[10] = long[i]
        traits[11] = gender[i]
        traits[12] = education[i]
        traits[13] = cd[i]
        traits[14] = sa[i]
        traits[15] = rf[i]
        xdif = lat - lat[i]
        ydif = long - long[i]
        distance = np.power(xdif, 2) + np.power(ydif, 2)
        sorted = np.argsort(distance)
        friends = sorted[1:num_friends + 1]
        for j in range(0, len(friends)):
            g.add_edge(i, int(friends[j]))
        agent = Person(vs[i], traits)
        agents.append(agent)


sample_agents()