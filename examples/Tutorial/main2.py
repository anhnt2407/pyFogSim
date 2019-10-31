"""

    @author: isaac

"""
import random

from yafs.core import Simulation
from yafs.application import Application, Message

from yafs.population import *
from yafs.topology import Topology

from examples.Tutorial.simpleSelection import MinPath_RoundRobin
from examples.Tutorial.simplePlacement import CloudPlacement
from yafs.distribution import DeterministicDistribution
from yafs.utils import fractional_selectivity
from yafs.stats import Stats
import time
import numpy as np

RANDOM_SEED = 1


def create_application():
    # APLICATION
    a = Application(name="SimpleCase")

    # (S) --> (ServiceA) --> (A)
    a.set_modules(
        [
            {"Sensor": {"Type": Application.TYPE_SOURCE}},
            {"ServiceA": {"RAM": 10, "Type": Application.TYPE_MODULE}},
            {"Actuator": {"Type": Application.TYPE_SINK}},
        ]
    )
    """
    Messages among MODULES (AppEdge in iFogSim)
    """
    m_a = Message("M.A", "Sensor", "ServiceA", instructions=20 * 10 ^ 6, size=1000)
    m_b = Message("M.B", "ServiceA", "Actuator", instructions=30 * 10 ^ 6, size=500, broadcasting=True)

    """
    Defining which messages will be dynamically generated # the generation is controlled by Population algorithm
    """
    a.add_source_messages(m_a)

    """
    MODULES/SERVICES: Definition of Generators and Consumers (AppEdges and TupleMappings in iFogSim)
    """
    # MODULE SERVICES
    a.add_service_module("ServiceA", m_a, m_b, fractional_selectivity, threshold=1.0)

    return a


def create_json_topology():
    """
       TOPOLOGY DEFINITION

       Some attributes of fog entities (nodes) are approximate
       """

    ## MANDATORY FIELDS
    topology_json = {}
    topology_json["entity"] = []
    topology_json["link"] = []

    cloud_dev = {"id": 0, "model": "cloud", "mytag": "cloud", "IPT": 5000 * 10 ^ 6, "RAM": 40000, "COST": 3, "WATT": 20.0}
    sensor_dev = {"id": 1, "model": "sensor-device", "IPT": 100 * 10 ^ 6, "RAM": 4000, "COST": 3, "WATT": 40.0}
    actuator_dev = {"id": 2, "model": "actuator-device", "IPT": 100 * 10 ^ 6, "RAM": 4000, "COST": 3, "WATT": 40.0}

    link1 = {"s": 0, "d": 1, "BW": 1, "PR": 10}
    link2 = {"s": 0, "d": 2, "BW": 1, "PR": 1}

    topology_json["entity"].append(cloud_dev)
    topology_json["entity"].append(sensor_dev)
    topology_json["entity"].append(actuator_dev)
    topology_json["link"].append(link1)
    topology_json["link"].append(link2)

    return topology_json


# @profile
def main(simulated_time):

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    """
    TOPOLOGY from a json
    """
    t = Topology()
    t_json = create_json_topology()
    t.load(t_json)
    nx.write_gefx(t.G, "network.gexf")

    """
    APPLICATION
    """
    app = create_application()

    """
    PLACEMENT algorithm
    """
    placement = CloudPlacement("onCloud")  # it defines the deployed rules: module-device
    placement.scaleService({"ServiceA": 4})

    """
    POPULATION algorithm
    """
    # In ifogsim, during the creation of the application, the Sensors are assigned to the topology, in this case no. As mentioned, YAFS differentiates the adaptive sensors and their topological assignment.
    # In their case, the use a statical assignment.
    pop = StaticPopulation("Statical")
    # For each type of sink modules we set a deployment on some type of devices
    # A control sink consists on:
    #  args:
    #     model (str): identifies the device or devices where the sink is linked
    #     number (int): quantity of sinks linked in each device
    #     module (str): identifies the module from the app who receives the messages
    pop.set_sink_control({"model": "actuator-device", "number": 2, "module": app.sink_modules})

    # In addition, a source includes a distribution function:
    dDistribution = DeterministicDistribution(name="Deterministic", time=100)
    pop.set_src_control({"model": "sensor-device", "number": 1, "message": app.get_message["M.A"], "distribution": dDistribution})  # 5.1}})

    """--
    SELECTOR algorithm
    """
    # Their "selector" is actually the shortest way, there is not type of orchestration algorithm.
    # This implementation is already created in selector.class,called: First_ShortestPath
    selectorPath = MinPath_RoundRobin()

    """
    SIMULATION ENGINE
    """

    stop_time = simulated_time
    s = Simulation(t, default_results_path="Results_multiple")
    s.deploy_app(app, placement, pop, selectorPath)

    s.run(stop_time, show_progress_monitor=False)

    s.draw_allocated_topology()  # for debugging


if __name__ == "__main__":
    import logging.config
    import os

    logging.config.fileConfig(os.getcwd() + "/logging.ini")

    start_time = time.time()
    main(simulated_time=1000)

    print(("\n--- %s seconds ---" % (time.time() - start_time)))

    ### Finally, you can analyse the results:
    print("-" * 20)
    print("Results:")
    print("-" * 20)
    m = Stats(default_path="Results_multiple")  # Same name of the results
    time_loops = [["M.A", "M.B"]]
    m.showResults2(1000, time_loops=time_loops)
    print("\t- Network saturation -")
    print("\t\tAverage waiting messages : %i" % m.average_messages_not_transmitted())
    print("\t\tPeak of waiting messages : %i" % m.peak_messages_not_transmitted())
    print("\t\tTOTAL messages not transmitted: %i" % m.messages_not_transmitted())

    print("\n\t- Stats of each service deployed -")
    print(m.get_df_modules())
    print(m.get_df_service_utilization("ServiceA", 1000))

    print("\n\t- Stats of each DEVICE -")
    # TODO
