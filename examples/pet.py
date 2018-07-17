import dworp
import igraph
import logging
import numpy as np
import sys
import os


class Person(dworp.Agent):
    def __init__(self, vertex, num_features, traits):
        super().__init__(vertex.index, num_features + 1)
        vertex['agent'] = self
        self.vertex = vertex
        self.state[0:-1] = traits

    def step(self, now, env):
        trait_sum = (self.state[1] + self.state[2] + self.state[3] + self.state[4]) / 4
        if self.state[6] % 5 == 0:
            if self.state[0] == 0:
                if trait_sum <= 0.33:
                    self.state[0] = 1
                elif 0.33 < trait_sum <= 0.66:
                    self.state[0] = 2
                elif 0.66 < trait_sum <= 1:
                    self.state[0] = 3
            else:
                self.state[2] = np.random.random_sample()
                self.state[3] = np.random.random_sample()
                self.state[4] = np.random.random_sample()
        self.state[6] += 1


class PetEnvironment(dworp.NetworkEnvironment):
    def __init__(self, network):
        super().__init__(1, network)

    def init(self, now):
        self.state.fill(0)

    def step(self, now, agents):
        self.logger.info("Environment did not need to update.")


class PetObserver(dworp.Observer):
    def __init__(self, fhandle):
        self.fhandle = fhandle

    def start(self, now, env, agents):
        print("BEGINNING SIMULATION: {} fish owners, {} cat owners, {} dog owners".format(self.sum_fish(agents),
                                                                                           self.sum_cat(agents),
                                                                                           self.sum_dogs(agents)))
        self.fhandle.write("Step\tFish\tCats\tDogs\n")
        self.fhandle.write("{}\t{}\t{}\t{}\n".format(now, self.sum_fish(agents), self.sum_cat(agents), self.sum_dogs(agents)))

    def step(self, now, agents, env):
        print("Step {}: {} fish owners, {} cat owners, {} dog owners".format(now, self.sum_fish(agents),
                                                                                           self.sum_cat(agents),
                                                                                           self.sum_dogs(agents)))
        self.fhandle.write("{}\t{}\t{}\t{}\n".format(now, self.sum_fish(agents), self.sum_cat(agents), self.sum_dogs(agents)))

    def stop(self, now, agents, env):
        print("ENDING SIMULATION: {} fish owners, {} cat owners, {} dog owners".format(self.sum_fish(agents),
                                                                                           self.sum_cat(agents),
                                                                                           self.sum_dogs(agents)))
        self.fhandle.write("{}\t{}\t{}\t{}\n".format(now, self.sum_fish(agents), self.sum_cat(agents), self.sum_dogs(agents)))

    @staticmethod
    def sum_fish(agents):
        number_fish = 0
        for agent in agents:
            if agent.state[0] == 1:
                number_fish += 1
        return number_fish

    @staticmethod
    def sum_cat(agents):
        number_cats = 0
        for agent in agents:
            if agent.state[0] == 2:
                number_cats += 1
        return number_cats

    @staticmethod
    def sum_dogs(agents):
        number_dogs = 0
        for agent in agents:
            if agent.state[0] == 3:
                number_dogs += 1
        return number_dogs


class PetTerminator(dworp.Terminator):
    def __init__(self, maxwithoutchange):
        self.numstepswithoutchange = 0
        self.maxstepswithoutchange = maxwithoutchange
        self.lastnumRS = 0
        self.lastdiscontinuedRS = 0

    def test(self, now, agents, env):
        curnumRS = self.num_dog(agents)
        curnumdiscontinued = self.num_cat(agents)
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
    def num_dog(agents):
        number_cats = 0
        for agent in agents:
            if agent.state[0] == 'Cat':
                number_cats += 1
        return number_cats

    @staticmethod
    def num_cat(agents):
        number_dogs = 0
        for agent in agents:
            if agent.state[0] == 'Dog':
                number_dogs += 1
        return number_dogs


class Simulation:
    def test(self):
        logging.basicConfig(level=logging.WARN)
        outstring = ""
        outname = "pet_output%s.tsv" % outstring
        fhandle = open(outname, 'w')
        num_agents = 1000
        num_tsteps = 100
        wealth = np.random.random_sample(num_agents)
        interaction = np.random.random_sample(num_agents)
        responsible = np.random.random_sample(num_agents)
        time = np.random.random_sample(num_agents)
        gender = np.random.randint(1, 3, num_agents)
        pet = np.zeros(1000)
        g = igraph.Graph()
        for i in range(0, num_agents):
            g.add_vertex(i)
        vs = g.vs
        agents = []
        for i in range (0, num_agents):
            traits = np.zeros((7))
            traits[0] = pet[i]
            traits[1] = wealth[i]
            traits[2] = interaction[i]
            traits[3] = responsible[i]
            traits[4] = time[i]
            traits[5] = gender[i]
            traits[6] = 0
            g.add_edge(i, vs[1])
            specialagent = Person(vs[i], 7, traits)
            agents.append(specialagent)

        np.random.seed(347)
        env = PetEnvironment(g)
        time = dworp.BasicTime(num_tsteps)
        scheduler = dworp.RandomOrderScheduler(np.random.RandomState(4587))
        term = PetTerminator(50)
        observer = dworp.ChainedObserver(PetObserver(fhandle))
        sim = dworp.BasicSimulation(agents, env, time, scheduler, observer, terminator=term)
        sim.run()
        fhandle.close()

        with open("pet_demographics.tsv", 'w') as f:
            f.write('Wealth\tInteraction\tResponsible\tTime\tGender\tPet\n')
            for i in range(0, num_agents):
                f.write("{}\t{}\t{}\t{}\t{}\t".format(wealth[i], interaction[i], responsible[i], time[i], gender[i]))
                f.write("{}\n".format(agent.state[0] for agent in agents))

thistest = Simulation()
thistest.test()