import dworp
import igraph
import logging
import numpy as np
import sys
import subprocess
import os
import pygame
import pdb

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
        num_none = 0
        for i in range(0, len(neighbors)):
            nvert = neighbors[i]
            nstate = nvert["agent"].state
            if nstate[0] == 1:
                num_apple += 1
            elif nstate[0] == 2:
                num_android += 1
            elif nstate[0] == 0:
                num_none += 1
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
        if np.random.random() < 0.1: #10% chance of randomly switching (which some people decide to do)
                self.state[0] = np.random.random_integers(0,2)
        # print('Apple: {}, Android: {}, None {}'.format(num_apple, num_android, num_none))


class PhoneEnvironment(dworp.NetworkEnvironment):
    def __init__(self, network):
        super().__init__(1, network)

    def init(self, now):
        self.state.fill(0)

    def step(self, now, agents):
        self.logger.info("Environment did not need to update.")


class PhoneObserver(dworp.Observer):
    def __init__(self, fhandle):
        self.fhandle = fhandle

    def start(self, now, agents, env):
        print("BEGINNING SIMULATION: {} agents using apple, {} agents using android, {} not using either".format(
                                            self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))
        self.fhandle.write("Step\tApple\tAndroid\tNeither\n")
        self.fhandle.write("%d\t%d\t%d\t%d\n" % (now, self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))

    def step(self, now, agents, env):
        print("Step {}: {} agents using apple, {} agents using android, {} not using either".format(now,
                self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))
        self.fhandle.write("%d\t%d\t%d\t%d\n" % (now, self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))

    def stop(self, now, agents, env):
        print("ENDING SIMULATION: {} agents using apple, {} agents using android, {} not using either\nEND OF SIMULATION".format(
                self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))
        self.fhandle.write("%d\t%d\t%d\t%d\n" % (now, self.sum_apple(agents), self.sum_android(agents), self.sum_none(agents)))

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
    def __init__(self, maxwithoutchange):
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


class PyGameRenderer(dworp.Observer):
    def __init__(self, zoom, fps, frames_in_anim):
        self.zoom = zoom
        self.fps = fps
        self.width = 750
        self.height = 750

        pygame.init()
        pygame.display.set_caption("Phones")
        self.screen = pygame.display.set_mode((self.zoom * self.width, self.zoom * self.height))
        self.background = pygame.Surface((self.screen.get_size()))
        self.background = self.background.convert()
        self.clock = pygame.time.Clock()
        self.filename_list = [os.path.join('temp' + str(n) + '.png') for n in range(frames_in_anim)]
        self.frame = 0

    def start(self, start_time, agents, env):
        self.draw(agents)

    def step(self, now, agents, env):
        self.draw(agents)

    def stop(self, now, agents, env):
        pygame.quit()

    def draw(self, agents):
        #side = self.zoom - 1
        side = 5
        self.background.fill((255, 255, 255))
        for agent in agents:
            x = self.zoom * (agent.state[3] - 78.6569) * (0.95*self.width)
            y = self.zoom * (agent.state[2] - 37.4316) * (0.95*self.height)
            if agent.state[0] == 0:
                color = (0, 191, 255) #blue
            else:
                if agent.state[0] == 1:
                    color = (255, 128, 0) #orange
                else:
                    color = (139, 0, 0) #maroon
            pygame.draw.rect(self.background, color, (x, y, side, side), 0)
        self.screen.blit(self.background, (0, 0))
        pygame.font.init()  # you have to call this at the start,
        # if you want to use this module.
        myfont = pygame.font.SysFont('Arial', 24)
        textsurface = myfont.render("Simulation at %d" % (self.frame), False, (0, 0, 0))
        self.screen.blit(textsurface, (5, int(0.95*self.width)))
        pygame.display.flip()
        self.clock.tick(self.fps)
        pygame.image.save(self.screen, self.filename_list[self.frame])
        self.frame = self.frame + 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()


class Simulation:
    def test(self):
        logging.basicConfig(level=logging.WARN)
        outstring = "_B"
        outname = "outputs%s.tsv" % (outstring)
        fhandle = open(outname, 'w')
        num_agents = 2500
        num_tsteps = 150
        wealth = np.random.normal(100000, 20000, num_agents)
        offsets_lat = np.random.random((num_agents, 1))
        offsets_lon = np.random.random((num_agents, 1))
        lat = offsets_lon + 37.4316 # deg north
        lon = offsets_lat + 78.6569 # deg west
        phone = np.random.random_integers(0, 2, num_agents)
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

        np.random.seed(347)
        makevis = True
        vis_flag = makevis and 'pygame' in sys.modules
        if vis_flag:
            print("vis_flag is True")
        else:
            print("vis_flag is False")
        # vis does not support different colors
        # color
        #
        # s = ["blue", "orange"]
        # params = SegregationParams(density, similarity, grid_size, seed, colors)

        # create and run one realization of the simulation
        observer = dworp.ChainedObserver(PhoneObserver(fhandle))
        n_fps = 4

        if vis_flag:
            observer.append(dworp.PauseAtEndObserver(3))
            pgr = PyGameRenderer(1, n_fps, num_tsteps + 1)
            observer.append(pgr)
        env = PhoneEnvironment(g)
        time = dworp.BasicTime(num_tsteps)
        scheduler = dworp.RandomOrderScheduler(np.random.RandomState(4587))
        term = PhoneTerminator(50)
        sim = dworp.BasicSimulation(agents, env, time, scheduler, observer, terminator=term)
        sim.run()
        fhandle.close()

        with open("demographics.tsv",'w') as f:
            for i in range(0,num_agents):
                f.write('Location: {}, {}\t\t'.format(lat[i], lon[i]))
                f.write('Wealth: {}\t'.format(wealth[i]))
                if agents[i].state[0] == 0:
                    f.write('\tPhone Type: None\n')
                elif agents[i].state[0] == 1:
                    f.write('\tPhone Type: Apple\n')
                elif agents[i].state[0] == 2:
                    f.write('\tPhone Type: Android\n')
            f.close()


thistest = Simulation()
thistest.test()