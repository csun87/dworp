import dworp
import igraph
import logging
import numpy as np

class Person(dworp.Agent):
    def __init__(self, vertex, num_features, traits):
        super().__init__(vertex.index, num_features + 1)
        vertex['agent'] = self
        self.vertex = vertex
        self.state[0:-1] = traits


    def step(self, now, env):
        neighbors = self.vertex.neighbors()
        num_apple = 0
        num_android = 0
        for i in range(0, len(neighbors)):
            nvert = neighbors[i]
            nstate = nvert["agent"].state
            if nstate[0] == 1:
                num_apple += 1
            elif nstate[0] == 2:
                num_android += 1
            elif nstate[0] == 0:
                pass
            else:
                print("error")
        if num_apple > num_android and self.state[1] > 80000:
            self.state[0] = 1
        if num_apple == num_android and self.state[1] > 120000:
            self.state[0] = 1
        if num_apple == num_android and self.state[1] <= 100000:
            self.state[0] = 2
        if num_android > num_apple and self.state[1] > 80000:
            self.state[0] = 2
        if np.random.random() < 0.1:
                self.state[0] = np.random.random_integers(0,2)



class PhoneEnvironment(dworp.NetworkEnvironment):
    def __init__(self, network):
        super().__init__(1, network)

    def init(self, now):
        self.state.fill(0)

    def step(self, now, agents):
        pass


class PhoneObserver(dworp.Observer):
    def start(self, now, agents, env):
        print("BEGINNING SIMULATION\nStep {}: {} agents using apple, {} agents using android, {} not using either".format(now,
                                            self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))

    def step(self, now, agents, env):
        print("Step {}: {} agents using apple, {} agents using android, {} not using either".format(now,
                self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))
    def stop(self, now, agents, env):
        print("Step {}: {} agents using apple, {} agents using android, {} not using either\nENDING SIMULATION".format(now,
                self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))

    @staticmethod
    def sum_none(agents):
        number_none = 0
        for agent in agents:
            if agent.state[0] == 0:
                number_none += 1
        return number_none

    @staticmethod
    def sum_apple(agents):
        number_apple = 0
        for agent in agents:
            if agent.state[0] == 1:
                number_apple += 1
        return number_apple

    @staticmethod
    def sum_android(agents):
        number_android = 0
        for agent in agents:
            if agent.state[0] == 2:
                number_android += 1
        return number_android

class PhoneTerminator(dworp.Terminator):
    def __init__(self,maxwithoutchange):
        self.numstepswithoutchange = 0
        self.maxstepswithoutchange = maxwithoutchange
        self.lastnumRS = 0
        self.lastdiscontinuedRS = 0

    def test(self, now, agents, env):
        curnumRS = self.apple(agents)
        curnumdiscontinued = self.android(agents)
        if self.lastnumRS == curnumRS:
            if self.lastdiscontinuedRS == curnumdiscontinued:
                self.numstepswithoutchange = self.numstepswithoutchange + 1
            else:
                self.numstepswithoutchange = 0
        else:
            self.numstepswithoutchange = 0
        self.lastnumRS = curnumRS
        self.lastdiscontinuedRS = curnumdiscontinued
        # check if we havent changed for too many steps
        if self.numstepswithoutchange > self.maxstepswithoutchange:
            terminate = True
        else:
            terminate = False
        if terminate:
            print("Terminating simulation early at time = {} because of persistent lack of change".format(now))
        return terminate

    @staticmethod
    def apple(agents):
        number_apple = 0
        for agent in agents:
            if agent.state[0] == 1:
                number_apple += 1
        return number_apple

    @staticmethod
    def android(agents):
        number_android = 0
        for agent in agents:
            if agent.state[0] == 2:
                number_android += 1
        return number_android

class Simulation:
    def test(self):
        logging.basicConfig(level=logging.WARN)
        num_agents = 2500
        num_tsteps = 50
        wealth = np.random.normal(100000, 20000, num_agents)
        lat = np.random.random()
        lon = np.random.random()
        offsets_lat = np.random.random((num_agents,1))
        offsets_lon = np.random.random((num_agents,1))
        lat = offsets_lon + 37.4316 # deg north
        lon = offsets_lat + 78.6569 # deg west
        phone = np.random.random_integers(0,2,num_agents)
        g = igraph.Graph()
        for i in range(0, num_agents):
            g.add_vertex(i)
        vs = g.vs
        agents = []
        for i in range(0, num_agents):
            traits = np.zeros((4))
            traits[0] = phone[i]
            traits[1] = wealth[i]
            traits[2] = lat[i]
            traits[3] = lon[i]
            difflat = lat - lat[i]
            difflon = lon - lon[i]
            distsq = np.power(difflat, 2) + np.power(difflon, 2)
            sorted = np.argsort(distsq, axis=0)
            n_friends = 5
            friends = sorted[1: n_friends+1]
            for j in range(0,len(friends)):
                g.add_edge(i,int(friends[j]))
            curagent = Person(vs[i], 4, traits)
            agents.append(curagent)

        env = PhoneEnvironment(g)
        time = dworp.BasicTime(num_tsteps)
        scheduler = dworp.RandomOrderScheduler(np.random.RandomState(4587))
        term = PhoneTerminator(50)
        observer = PhoneObserver()
        sim = dworp.BasicSimulation(agents, env, time, scheduler, observer, terminator=term)
        sim.run()

thistest = Simulation()
thistest.test()