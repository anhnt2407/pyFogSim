"""

    This example implements a simple evolutive deployment of fog devices to study the latency of two applications.
    There is a comparison between:
    - One application has a cloud placement
    - Another one (equivalent application) has an evolutive deployement on fog devices

    @author: isaac

"""

import copy
import operator
import time

import networkx as nx
import numpy as np

from yafs.application import Application, Message
from yafs.core import Simulation
from yafs.distribution import *
from yafs.population import PopulationMove
from yafs.selection import CloudPathRR
from yafs.topology import Topology

RANDOM_SEED = 1


def create_application(name):
    a = Application(name=name)

    a.set_modules([{"Generator": {"Type": Application.TYPE_SOURCE}}, {"Actuator": {"Type": Application.TYPE_SINK}}])

    m_egg = Message("M.Action", "Generator", "Actuator", instructions=100, size=10)
    a.add_source_messages(m_egg)
    return a


# @profile
def main(simulated_time):

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    """
    TOPOLOGY from a json
    """

    t = Topology()
    t.G = nx.read_graphml("Euclidean.graphml")

    ls = list(t.G.nodes)
    li = {x: int(x) for x in ls}
    nx.relabel_nodes(t.G, li, False)  # Transform str-labels to int-labels

    print("Nodes: %i" % len(t.G.nodes()))
    print("Edges: %i" % len(t.G.edges()))
    # MANDATORY fields of a link
    # Default values =  {"BW": 1, "PR": 1}
    valuesOne = dict(zip(t.G.edges(), np.ones(len(t.G.edges()))))

    nx.set_edge_attributes(t.G, name="BW", values=valuesOne)
    nx.set_edge_attributes(t.G, name="PR", values=valuesOne)

    centrality = nx.betweenness_centrality(t.G)
    nx.set_node_attributes(t.G, name="centrality", values=centrality)

    sorted_clustMeasure = sorted(list(centrality.items()), key=operator.itemgetter(1), reverse=True)

    top20_devices = sorted_clustMeasure[0:20]
    main_fog_device = copy.copy(top20_devices[0][0])

    # df = pd.read_csv("pos_network.csv")
    # pos = {}
    # for r in df.iterrows():
    #     lat = r[1].x
    #     lng = r[1].y
    #     pos[r[0]] = (lat, lng)

    # fig = plt.figure(figsize=(10, 8), dpi=100)
    # nx.draw(t.G, with_labels=True,pos=pos,node_size=60,node_color="orange", font_size=8)
    # plt.savefig('labels.png')
    # exit()

    print("-" * 20)
    print("Best top centralized device: ", main_fog_device)
    print("-" * 20)

    """
    APPLICATION
    """
    app1 = create_application("app1")

    """
    PLACEMENT algorithm
    """
    # There are not modules to place.
    placement = NoPlacementOfModules("NoPlacement")

    """
    POPULATION algorithm
    """
    number_generators = int(len(t.G) * 0.1)
    print("Number of generators %i" % number_generators)

    # you can use whatever funciton to change the topology
    dStart = DeterministicDistributionStartPoint(500, 400, name="Deterministic")
    pop = PopulationMove(name="mttf-nodes", srcs=number_generators, node_dst=main_fog_device, activation_dist=dStart)
    pop.set_sink_control({"id": main_fog_device, "number": number_generators, "module": app1.sink_modules})

    dDistribution = DeterministicDistribution(name="Deterministic", time=100)
    pop.set_src_control({"number": 1, "message": app1.get_message["M.Action"], "distribution": dDistribution})

    # In addition, a source includes a distribution function:

    """--
    SELECTOR algorithm
    """
    selectorPath = CloudPathRR()

    """
    SIMULATION ENGINE
    """
    s = Simulation(t, default_results_path="Results_%s" % (simulated_time))
    s.deploy_app(app1, placement, pop, selectorPath)

    s.run(simulated_time, progress_bar=False)

    # s.draw_allocated_topology() # for debugging
    s.print_debug_assignaments()


if __name__ == "__main__":
    import logging.config
    import os

    logging.config.fileConfig(os.getcwd() + "/logging.ini")

    start_time = time.time()

    main(simulated_time=10000)

    print(("\n--- %s seconds ---" % (time.time() - start_time)))

# ffmpeg -i out5.mp4 -pix_fmt rgb24  out.gif
