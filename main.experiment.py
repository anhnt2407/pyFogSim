import logging
import random
from typing import Tuple, List

import networkx as nx

from yafs import utils
from yafs.core import Simulation
from yafs.application import Application, Message, Module
from yafs.placement import CloudPlacement
from yafs.population import StaticPopulation

from yafs.selection import ShortestPath
from yafs.topology import Topology

from yafs.distribution import UniformDistribution
import time
import numpy as np

RANDOM_SEED = 1


def create_application(name: str = "SimpleApp") -> Tuple[Application, List[Message]]:
    sensor = Module("sensor")
    service_a = Module("service_a")
    actuator = Module("actuator")
    message_a = Message("M.A", src=sensor, dst=service_a, instructions=20 * 10 ^ 6, size=1000)
    message_b = Message("M.B", src=service_a, dst=actuator, instructions=30 * 10 ^ 6, size=500)
    service_a.add_service(message_a, message_b)  # TODO Weird back-referencing objects
    application = Application(name=name, modules=[sensor, service_a, actuator])

    return application, [message_a]


def main(simulated_time):
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    G = nx.node_link_graph({
        "directed": False,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {"id": "cloud", "IPT": 10**6, "RAM": 10**6, "WATT": 20.0},
            {"id": "sensor1", "IPT": 1000, "RAM": 4000, "WATT": 40.0},
            {"id": "sensor2", "IPT": 1000, "RAM": 4000, "WATT": 40.0},
            {"id": "sensor3", "IPT": 1000, "RAM": 4000, "WATT": 40.0},
            {"id": "sensor4", "IPT": 1000, "RAM": 4000, "WATT": 40.0},
            {"id": "fog1", "IPT": 5000, "RAM": 4000, "WATT": 40.0},
            {"id": "fog2", "IPT": 5000, "RAM": 4000, "WATT": 40.0},
            {"id": "actuator1", "IPT": 1000, "RAM": 4000, "WATT": 40.0},
            {"id": "actuator2", "IPT": 1000, "RAM": 4000, "WATT": 40.0},
        ],
        "links": [
            {"source": "sensor1", "target": "fog1", "BW": 1, "PR": 10},
            {"source": "sensor1", "target": "fog2", "BW": 1, "PR": 10},
            {"source": "sensor2", "target": "fog1", "BW": 1, "PR": 10},
            {"source": "sensor2", "target": "fog2", "BW": 1, "PR": 10},
            {"source": "sensor3", "target": "fog1", "BW": 1, "PR": 10},
            {"source": "sensor3", "target": "fog2", "BW": 1, "PR": 10},
            {"source": "sensor4", "target": "fog1", "BW": 1, "PR": 10},
            {"source": "sensor4", "target": "fog2", "BW": 1, "PR": 10},
            {"source": "fog1", "target": "cloud", "BW": 5, "PR": 10},
            {"source": "fog1", "target": "actuator1", "BW": 5, "PR": 10},
            {"source": "fog1", "target": "actuator2", "BW": 5, "PR": 10},
            {"source": "fog2", "target": "cloud", "BW": 5, "PR": 10},
            {"source": "fog2", "target": "actuator1", "BW": 5, "PR": 10},
            {"source": "fog2", "target": "actuator2", "BW": 5, "PR": 10},
            {"source": "cloud", "target": "actuator1", "BW": 5, "PR": 10},
            {"source": "cloud", "target": "actuator2", "BW": 5, "PR": 10},
        ]
    })
    t = Topology(G)
    utils.draw_topology(t)

    app1, source_messages1 = create_application("App1")
    app2, source_messages2 = create_application("App2")

    distribution = UniformDistribution(min=1, max=100)
    # TODO Sink hardcoded
    population = StaticPopulation("Statical")
    population.set_sink_control({"id": "actuator1",  # identifies the device or devices where the sink is linked
                                 "number": 1,  # quantity of sinks linked in each device
                                 "module": "actuator"})  # identifies the module from the app who receives the messages

    # TODO It appears that the current implementation does not respect applications
    for source_message in source_messages1:
        population.set_src_control({"id": "sensor1",
                                    "number": 1,
                                    "message": source_message,
                                    "distribution": distribution})

    selection = ShortestPath()

    simulation = Simulation(t)
    simulation.deploy_app(app1, selection=selection)
    # simulation.deploy_app(app2, selection=selection)

    simulation.deploy_placement(CloudPlacement(apps=[app1]))
    simulation.deploy_population(population, applications=[app1])

    simulation.run(until=simulated_time, results_path="results", progress_bar=False)
    simulation.stats.print_report(simulated_time)
    utils.draw_topology(t, simulation.node_to_modules)


if __name__ == "__main__":
    logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    start_time = time.time()
    main(simulated_time=1000)
    print(("\n--- %s seconds ---" % (time.time() - start_time)))
