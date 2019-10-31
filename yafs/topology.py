import logging
from typing import Dict

import networkx as nx


# TODO Is this entire class necessary? Wouldn't it be smarter to just use a nx.networkx instance?


class Topology:
    """Unifies the functions to deal with **Complex Networks** as a network topology within of the simulator.

    In addition, it facilitates its creation, and assignment of attributes.
    """

    LINK_BW = "BW"  # Link feature: Bandwidth
    LINK_PR = "PR"  # Link feature: Propagation delay
    NODE_IPT = "IPT"  # Node feature: Instructions per Simulation Time

    def __init__(self, data: Dict, logger=None):  # TODO Remove logger  G: nx.Graph,
        self.G = nx.Graph()
        for entity in data["entity"]:
            self.G.add_node(entity["id"], **entity)
        for edge in data["link"]:
            self.G.add_edge(edge["s"], edge["d"], BW=edge[self.LINK_BW], PR=edge[self.LINK_PR])
        self._init_uptimes()

        self.logger = logger or logging.getLogger(__name__)

    def _init_uptimes(self):  # TODO What is this used for?
        for key in self.G.nodes:
            self.G.nodes[key]["uptime"] = (0, None)

    def find_IDs(self, value):
        """Search for nodes with the same attributes that value

        Args:
             value (dict). example value = {"model": "m-"}. Only one key is admitted

        Returns:
            A list with the ID of each node that have the same attribute that the value.value
        """
        keyS = list(value.keys())[0]

        result = []
        for key in list(self.G.nodes.keys()):
            val = self.G.nodes[key]
            if keyS in val:
                if value[keyS] == val[keyS]:
                    result.append(key)
        return result

    def add_node(self, nodes, edges=None):  # TODO edges unused
        """Add a list of nodes in the topology

        Args:
            nodes (list): a list of identifiers
            edges (list): a list of destination edges
        """
        id_ = len(self.G) + 1
        self.G.add_node(id_)
        self.G.add_edges_from(list(zip(nodes, [id_] * len(nodes))))
        return id_

    def remove_node(self, id_node: int):
        """Remove a node of the topology

        Args:
            id_node: Node identifier
        """
        self.G.remove_node(id_node)


def draw_png(network: nx.networkx, filepath: str):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(nrows=1, ncols=1)
    pos = nx.spring_layout(network)
    nx.draw(network, pos)
    labels = nx.draw_networkx_labels(network, pos)
    fig.savefig(filepath)  # save the figure to file
    plt.close(fig)  # close the figure
