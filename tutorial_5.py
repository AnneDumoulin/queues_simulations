from collections import deque
from heapq import heappop, heappush
import numpy as np
from scipy.stats import expon, uniform

np.random.seed(8)

ARRIVAL = 0
DEPARTURE = 1

ECONOMY = 0
BUSINESS = 1


class Job:
    def __init__(self):
        self.arrival_time = 0
        self.service_time = 0
        self.customer_type = ECONOMY
        self.server_type = ECONOMY
        self.departure_time = 0
        self.queue_length_at_arrival = 0

    def sojourn_time(self):
        return self.departure_time - self.arrival_time

    def waiting_time(self):
        return self.sojourn_time() - self.service_time

    def service_start(self):
        return self.departure_time - self.service_time

    def __repr__(self):
        return f"{self.customer_type}, {self.server_type}, {self.arrival_time}, {self.service_time}, {self.service_start()}, {self.departure_time}\n"


def generate_jobs(F, G, p_business, num_jobs):
    jobs = set()
    time = 0
    a = F.rvs(num_jobs)
    b = G.rvs(num_jobs)
    p = uniform(0, 1).rvs(num_jobs)

    for n in range(num_jobs):
        job = Job()
        job.arrival_time = time + a[n]
        job.service_time = b[n]
        if p[n] < p_business:
            job.customer_type = BUSINESS
        else:
            job.customer_type = ECONOMY

        jobs.add(job)
        time = job.arrival_time

    return jobs


def generate_jobs_bad_implementation(F, G, p_business, num_jobs):
    # the difference in performance is tremendous
    for n in range(num_jobs):
        job = Job()
        job.arrival_time = time + F.rvs()
        job.service_time = G.rvs()
        if uniform(0, 1).rvs() < p_business:
            job.customer_type = BUSINESS
        else:
            job.customer_type = ECONOMY

        jobs.add(job)
        time = job.arrival_time

    return jobs


class GGc_with_business:
    def __init__(self, c, jobs):
        self.b = 1  # number of b servers
        self.c = c  # number of e servers
        self.jobs = jobs

        self.num_b_busy = 0
        self.num_e_busy = 0
        self.stack = []
        self.b_queue = deque()
        self.e_queue = deque()

        self.fill_stack()

    def fill_stack(self):
        for job in sorted(self.jobs, key=lambda j: j.arrival_time):
            heappush(self.stack, (job.arrival_time, job, ARRIVAL))

    def handle_arrival(self, time, job):
        if job.customer_type == BUSINESS:
            job.queue_length_at_arrival = len(self.b_queue)
        else:
            job.queue_length_at_arrival = len(self.e_queue)

        if job.customer_type == ECONOMY:
            if self.num_e_busy < self.c:
                job.server_type = ECONOMY
                self.start_service(time, job)
            elif self.num_b_busy < self.b:
                job.server_type = BUSINESS
                self.start_service(time, job)
            else:
                self.e_queue.append(job)
        else:  # business customer
            if self.num_b_busy < self.b:
                job.server_type = BUSINESS
                self.start_service(time, job)
            elif self.num_e_busy < self.c:
                job.server_type = ECONOMY
                self.start_service(time, job)
            else:
                self.b_queue.append(job)

    def start_service(self, time, job):
        if job.server_type == BUSINESS:
            self.num_b_busy += 1
        else:
            self.num_e_busy += 1
        job.departure_time = time + job.service_time
        heappush(self.stack, (job.departure_time, job, DEPARTURE))

    def pop_from_queue_set_server_and_start(self, time, queue, server_type):
        next_job = queue.popleft()
        next_job.server_type = server_type
        self.start_service(time, next_job)

    def handle_departure(self, time, job):
        if job.server_type == BUSINESS:
            self.num_b_busy -= 1
            if self.b_queue:
                self.pop_from_queue_set_server_and_start(time, self.b_queue, BUSINESS)
            elif self.e_queue:
                self.pop_from_queue_set_server_and_start(time, self.e_queue, BUSINESS)
        else:  # economy server free
            self.num_e_busy -= 1
            if self.e_queue:
                self.pop_from_queue_set_server_and_start(time, self.e_queue, ECONOMY)
            elif self.b_queue:
                self.pop_from_queue_set_server_and_start(time, self.b_queue, ECONOMY)

    def run(self):
        time = 0
        while self.stack:  # not empty
            time, job, epoch_type = heappop(self.stack)
            if epoch_type == ARRIVAL:
                self.handle_arrival(time, job)
            else:
                self.handle_departure(time, job)

    def print_served_job(self):
        for j in sorted(self.jobs, key=lambda j: j.arrival_time):
            print(j)

    def mean_waiting_time(self, customer_type=None):
        if customer_type is None:
            jobs = self.jobs
        else:
            jobs = set(j for j in self.jobs if j.customer_type == customer_type)
        return sum(j.waiting_time() for j in jobs) / len(jobs)

    def max_waiting_time(self, customer_type=None):
        if customer_type is None:
            return max(j.waiting_time() for j in self.jobs)
        else:
            return max(
                j.waiting_time() for j in self.jobs if j.customer_type == customer_type
            )


def sakasegawa(F, G, c):
    labda = 1.0 / F.mean()
    ES = G.mean()
    rho = labda * ES / c
    EWQ_1 = rho ** (np.sqrt(2 * (c + 1)) - 1) / (c * (1 - rho)) * ES
    ca2 = F.var() * labda * labda
    ce2 = G.var() / ES / ES
    return (ca2 + ce2) / 2 * EWQ_1


# this time I worked according to a test driven procedure


def DD1_test_1():
    # test with only business customers
    c = 0
    F = uniform(1, 0.0001)
    G = expon(0.5, 0.0001)
    p_business = 1
    num_jobs = 5
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()
    ggc.print_served_job()
    quit()

#DD1_test_1()

def DD1_test_2():
    # test with only economy customers
    c = 1
    F = uniform(1, 0.0001)
    G = expon(0.5, 0.0001)
    p_business = 0
    num_jobs = 5
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()
    ggc.print_served_job()
    quit()

#DD1_test_2()

def DD1_test_3():
    # test with only economy customers but only a business server
    c = 0
    F = uniform(1, 0.0001)
    G = expon(0.5, 0.0001)
    p_business = 0
    num_jobs = 5
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()
    ggc.print_served_job()
    quit()

#DD1_test_3()

def DD2_test_1():
    # test with only economy customers and one e_server. As the b_server is always present, we must have 2 servers.
    # assume that all jobs arrive at time 0, and have service time 1
    c = 1
    F = uniform(0, 0.0001)
    G = expon(1, 0.0001)
    p_business = 0
    num_jobs = 10
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()
    ggc.print_served_job()
    quit()

#DD2_test_1()

def mm1_test_1():
    # test with only business customers but no e_server, very few jobs
    c = 0
    labda = 0.9
    mu = 1
    F = expon(scale=1.0 / labda)
    G = expon(scale=1.0 / mu)
    p_business = 1

    num_jobs = 10
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()
    ggc.print_served_job()
    quit()

#mm1_test_1()

def mm1_test_2():
    # test with only economy customers but no e_server
    c = 0
    labda = 0.9
    mu = 1
    F = expon(scale=1.0 / labda)
    G = expon(scale=1.0 / mu)
    p_business = 0

    print("theory: ", sakasegawa(F, G, c + 1))  # 1 for the business server

    num_jobs = 100_000
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()

    print("mean waiting: ", ggc.mean_waiting_time())
     quit()

#mm1_test_2()

def mm1_test_3():
    # test with only business customers but no e_server
    c = 0
    labda = 0.9
    mu = 1
    F = expon(scale=1.0 / labda)
    G = expon(scale=1.0 / mu)
    p_business = 1

    print("theory: ", sakasegawa(F, G, c + 1))  # 1 for the business server

    num_jobs = 100_000
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()

    print("mean waiting: ", ggc.mean_waiting_time())
    quit()

#mm1_test_3()


def mm2_test_1():
    # test with only business customers and 1 e_server
    c = 1
    labda = 0.9
    mu = 1
    F = expon(scale=1.0 / labda)
    G = expon(scale=1.0 / mu)
    p_business = 1

    print("theory: ", sakasegawa(F, G, c + 1))  # 1 for the business server

    num_jobs = 100_000
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()

    # mind that Sakasegawa's result is an approximation for the M/M/c with c>1
    print("mean waiting: ", ggc.mean_waiting_time())
    quit()

#mm2_test_1()


def mm2_test_2():
    # test with only economy customers and 1 e_server
    c = 1
    labda = 0.9
    mu = 1
    F = expon(scale=1.0 / labda)
    G = expon(scale=1.0 / mu)
    p_business = 0

    print("theory: ", sakasegawa(F, G, c + 1))  # 1 for the business server

    num_jobs = 100_000
    jobs = generate_jobs(F, G, p_business, num_jobs)
    ggc = GGc_with_business(c, jobs)
    ggc.run()

    print("mean waiting: ", ggc.mean_waiting_time())
    quit()

#mm2_test_2()


# CASE ANALYSIS

import copy


def case_analysis(jobs, c):
    # we need the same jobs for all cases, so that we can compare in a fair way. 
    b_jobs = set(copy.copy(j) for j in jobs if j.customer_type == BUSINESS)
    e_jobs = set(copy.copy(j) for j in jobs if j.customer_type == ECONOMY)

    # Case 1: each class its own server, no sharing
    bus = GGc_with_business(0, b_jobs)
    bus.run()

    eco = GGc_with_business(c - 1, e_jobs)
    eco.run()

    # Case 2: sharing with business server
    shared = GGc_with_business(c, jobs)
    shared.run()

    print("separate: bus mean", bus.mean_waiting_time())
    print("shared: bus mean: ", shared.mean_waiting_time(BUSINESS))
    print("separate: bus max", bus.max_waiting_time())
    print("shared: bus max: ", shared.max_waiting_time(BUSINESS))

    print("separate: eco mean", eco.mean_waiting_time())
    print("shared: eco mean: ", shared.mean_waiting_time(ECONOMY))
    print("separate: eco max", eco.max_waiting_time())
    print("shared: eco max: ", shared.max_waiting_time(ECONOMY))

    print("shared: all mean: ", shared.mean_waiting_time())
    print("shared: all max: ", shared.max_waiting_time())
    print()


def case1():
    num_jobs = 300
    labda = num_jobs / 90
    F = expon(scale=1.0 / labda)
    G = uniform(1, 2)
    p_business = 0.1
    c = 6
    jobs = generate_jobs(F, G, p_business, num_jobs)
    case_analysis(jobs, c)
    quit()

#case1()

def case2():
    num_jobs = 300
    labda = num_jobs / 180
    F = expon(scale=1.0 / labda)
    G = uniform(1, 2)
    p_business = 0.05
    c = 5
    jobs = generate_jobs(F, G, p_business, num_jobs)
    case_analysis(jobs, c)
    quit()

#case2()
