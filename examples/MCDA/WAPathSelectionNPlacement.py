import networkx as nx
import os
import pandas as pd
from subprocess import Popen, PIPE
from collections import namedtuple
from yafs import Selection
import operator
import numpy as np
from sklearn import preprocessing

NodeDES = namedtuple("NodeDES", ["node", "des", "path"])


class WARoutingAndDeploying(Selection):
    def __init__(self, path, pathResults, idcloud, logger=None):
        super(WARoutingAndDeploying, self).__init__()
        self.cache = {}
        self.invalid_cache_value = -1
        self.previous_number_of_nodes = -1
        self.idcloud = idcloud

        self.path = path

        pathTMP = "tmp_WA"

        # TODO CAMBAR TIME STAMP
        # DEBUG
        # self.datestamp = time.strftime('%Y%m%d%H%M%S')
        # self.datestamp = time.strftime('%Y%m%d')

        self.dname = pathResults + pathTMP  # + self.datestamp
        try:
            os.makedirs(self.dname)
        except OSError:
            None

        self.logger = logger or logging.getLogger(__name__)
        self.logger.info(" MCDA - Routing, Placement and Selection initialitzed ")

        self.min_path = {}

        self.idEvaluation = 0
        self.controlServices = {}
        # key: a service
        # value : a list of idDevices
        # Note: All services are deployed in the cloud, and they cannot be removed from there.

        self.powermin = []

    """
    It selects all paths
    """

    def get_the_path(self, G, node_src, node_dst):
        if (node_src, node_dst) not in list(self.min_path.keys()):
            self.min_path[(node_src, node_dst)] = list(nx.shortest_path(G, source=node_src, target=node_dst))
        return self.min_path[(node_src, node_dst)]

    def compute_NodeDESCandidates(self, node_src, alloc_DES, sim, DES_dst):

        try:
            # print len(DES_dst)
            nodes = []
            for dev in DES_dst:
                # print "DES :",dev
                node_dst = alloc_DES[dev]
                try:
                    nodes.append(self.get_the_path(sim.topology.G, node_src, node_dst))

                except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
                    self.logger.warning("No path between two nodes: %s - %s " % (node_src, node_dst))

            return nodes

        except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
            self.logger.warning("No path between from nodes: %s " % (node_src))
            # print "Simulation ends?"
            return []

    # def compute_SAR(self, sim, node_src, node_dst, message):
    #     try:
    #         print "COMPUTING LAT. node_src: %i to node_dst: %i" % (node_src, node_dst)
    #
    #         path = list(nx.shortest_path(sim.topology.G, source=node_src, target=node_dst))
    #         print "PATH ", path
    #
    #         totalTimelatency = 0
    #         for i in range(len(path) - 1):
    #             link = (path[i], path[i + 1])
    #             print "LINK : ", link
    #             # print " BYTES :", message.bytes
    #             totalTimelatency += sim.topology.G.edges[link][Topology.LINK_PR] + (
    #                 message.bytes / sim.topology.G.edges[link][Topology.LINK_BW])
    #             # print sim.topology.G.edges[link][Topology.LINK_BW]
    #
    #         att_node = sim.topology.get_nodes_att()[path[-1]]
    #         time_service = message.instructions / float(att_node["IPT"])
    #         totalTimelatency += time_service  # HW - computation of last node
    #         print totalTimelatency
    #
    #         return totalTimelatency
    #
    #     except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
    #         return 9999999

    def compute_Latency(self, sim, node_src, node_dst):
        try:
            path = list(nx.shortest_path(sim.topology.G, source=node_src, target=node_dst))
            totalTimelatency = 0
            for i in range(len(path) - 1):
                link = (path[i], path[i + 1])
                totalTimelatency += sim.topology.G.edges[link][Topology.LINK_PR]
            return totalTimelatency

        except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
            return 9999999

    # def compute_DSAR(self, node_src, alloc_DES, sim, DES_dst,message):
    #     try:
    #         bestSpeed = float('inf')
    #         minPath = []
    #         bestDES = []
    #         #print len(DES_dst)
    #         for dev in DES_dst:
    #             #print "DES :",dev
    #             node_dst = alloc_DES[dev]
    #             path = list(nx.shortest_path(sim.topology.G, source=node_src, target=node_dst))
    #             speed = 0
    #             for i in range(len(path) - 1):
    #                 link = (path[i], path[i + 1])
    #                # print "LINK : ",link
    #                # print " BYTES :", message.bytes
    #                 speed += sim.topology.G.edges[link][Topology.LINK_PR] + (message.bytes/sim.topology.G.edges[link][Topology.LINK_BW])
    #                 #print sim.topology.G.edges[link][Topology.LINK_BW]
    #
    #             att_node = sim.topology.get_nodes_att()[path[-1]]
    #             #TODO ISAAC
    #             # if att_node["id"]==100:
    #             #     print "\t last cloud"
    #             #     speed += 10000
    #
    #             time_service = message.instructions / float(att_node["IPT"])
    #             speed += time_service  # HW - computation of last node
    #             #print "SPEED: ",speed
    #             if  speed < bestSpeed:
    #                 bestSpeed = speed
    #                 minPath = path
    #                 bestDES = dev
    #
    #         #print bestDES,minPath
    #         return minPath, bestDES
    #
    #     except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
    #         self.logger.warning("There is no path between two nodes: %s - %s " % (node_src, node_dst))
    #         # print "Simulation ends?"
    #         return [], None

    def sort_table(self, table, col=0):
        return sorted(table, key=operator.itemgetter(col))

    def runMCDAR(self, pathRScript, pathWD, fileName, ncriteria, criteriaWeights, categoriesLowerProfiles, criteriaMinMax, criteriaVetos, majorityThreshold):

        cmd = [
            "Rscript",
            pathRScript + "/rscripts/MCDAv2.R",
            pathWD,
            fileName,
            ncriteria,
            criteriaWeights,
            categoriesLowerProfiles,
            criteriaMinMax,
            criteriaVetos,
            majorityThreshold,
        ]
        proc = Popen(cmd, stdout=PIPE)
        stdout = proc.communicate()[0]
        return "{}".format(stdout)

    def runELECTRER(self, pathRScript, pathWD, fileName, criteriaWeights, IndifferenceThresholds, PreferenceThresholds, VetoThresholds, minmaxcriteria):

        cmd = [
            "Rscript",
            pathRScript + "rscripts/ELECTREv1.R",
            pathWD,
            fileName,
            criteriaWeights,
            IndifferenceThresholds,
            PreferenceThresholds,
            VetoThresholds,
            minmaxcriteria,
        ]
        proc = Popen(cmd, stdout=PIPE)
        stdout = proc.communicate()[0]
        return "{}".format(stdout)

    def get_aprx_number_services(self, sim, node):
        # TODO IMPROVE - It also counts the number of clients in that node!
        y = np.array(list(sim.alloc_DES.values()))
        return (y == node).sum()

    def get_power(self, sim, nodes):
        power = []

        for i in sim.topology.G.nodes():
            if i in nodes:
                power.append((sim.topology.get_nodes_att()[i]["POWERmin"] + sim.topology.get_nodes_att()[i]["POWERmax"]) / 2.0)

        return power

    # TODO The implementation of new criteria should be dynamic

    def WA_EVALUATION(self, sim, node_src, nodes, message, app_name, service):
        nprojects = len(nodes)
        nrankcategories = 5
        criteriaMinMax = ""

        df = pd.DataFrame({"node": nodes}, index=nodes)
        # df.index = nodes
        # df["node"] = nodes

        ### REMOVING NODES WITH ONE SERVICE DEPLOYED, excetp the cloud
        nwithservices = list(np.unique(list(sim.alloc_DES.values())))
        nwithservices.remove(self.idcloud)
        # print "NODOS REMOVIDOS %s" %nwithservices
        df.drop(df.loc[df["node"].isin(nwithservices)].index, inplace=True)
        nodes = df.node
        # print "LENG OF NODES : %i"%len(nodes)
        # 1 CRITERIA: min : hop count
        values = []
        for node in nodes:
            values.append(len(self.get_the_path(sim.topology.G, node_src, node)))
        df["hopcount"] = values
        # criteriaMinMax += "min"

        # 2 CRITERIA: min : hop count - latency
        values = [self.compute_Latency(sim, node_src, node_dst=node) for node in nodes]
        df["latency"] = values
        # criteriaMinMax += ",min"

        # 3 CRITERIA: min : power (watts)
        values = self.get_power(sim, nodes)
        df["power"] = values
        # criteriaMinMax += ",min"

        # 4 CRITERIA: min : penalizacion por "SW" incompatibility "NODE id % app user"
        print(app_name)

        values = []
        for node in nodes:
            if node % 2 == int(app_name) % 2:
                values.append(1)
            else:
                values.append(40)
        df["deploymentPenalty"] = values

        # 5 COST
        values = []
        for node in nodes:  ##### I have a deadline :/
            if node < 100:
                values.append(40)
            else:
                values.append(1)

        df["cost"] = values

        # if sim.get_DES_from_Service_In_Node(node, app_name, service) == []:
        #     values.append(20 * sim.topology.get_nodes_att()[node]["IPT"])
        # else:

        # criteriaMinMax += ",min"

        # 5 CRITERIA: max : utilization
        # values = []
        # for node in nodes:
        #     values.append(self.get_aprx_number_services(sim, node))
        # df["utilization"] = values
        # # criteriaMinMax += ",max"

        # print df[:5]
        # criteriaWeights = "4,1,2,3,1"
        # cw = 1 / np.array([4., 1., 3., 3., 3.]) #10
        # cw = 1 / np.array([4., 4., 3., 1., 3.]) #11
        cw = 1 / np.array([4.0, 4.0, 3.0, 3.0, 1.0])  # 11
        cw = list(cw / cw.sum())

        cw.insert(0, 0.0)  # first column indicates "id.nodes"

        x = df.values  # returns a numpy array
        min_max_scaler = preprocessing.MinMaxScaler()
        x_scaled = min_max_scaler.fit_transform(x)
        df = pd.DataFrame(x_scaled, index=df.index)

        ### Invertir attr. max

        # df[df.columns[5]] = 1.0 - df[df.columns[5]] #Utilization column

        # df.convert_objects(convert_numeric=True).dtypes
        ## weighted average
        df = df * cw
        wa = df.sum(axis=1)

        best_node = wa.idxmin()

        print("BEST NODE: %i", best_node)

        df.to_csv(self.dname + "/data_%i.csv" % self.idEvaluation, index=False, index_label=False)

        self.logger.info("\t Best node: %i " % best_node)

        return best_node

    def doDeploy(self, sim, app_name, module, id_resource):
        app = sim.apps[app_name]
        services = app.services
        return sim.deploy_module(app_name, module, services[module], [id_resource])

    def print_control_services(self):
        print("-" * 30)
        print(" - Assignaments (node_src,service) -> (PATH, DES) ")
        print("-" * 30)
        for k in list(self.controlServices.keys()):
            print(k, "->", self.controlServices[k])

        print("-" * 30)
        return self.controlServices

    """
    This functions is called from the simulator to compute the path between two nodes. Also, it chooses the destination service.

    If the message.src == None, the message is send from a client to a gateway device.
    In this case, we use MCDA process to take an action.
    Actions are:
        - Use the cloud
        - Deploy a new service
        - Move (undeploy and deploy the service)
    """

    def get_path(self, sim, app_name, message, topology_src, alloc_DES, alloc_module, traffic, from_des):
        # print message
        # Entity that sends the message
        node_src = topology_src

        # Name of the service
        service = message.dst

        # Current ID_processes who run this service: a list
        DES_dst = alloc_module[app_name][message.dst]

        # print "\t  THE SERVICE IS: %s" %message.dst

        # The action depends on the type of service  and the place from it is called.
        if (node_src, service) not in list(self.controlServices.keys()):
            logging.info("Take an action on service: %s from node: %i" % (service, node_src))

            # Looking for a candidate devices to host the service
            # These candidate devices are our "objectives" in MCDA model

            # our candidate devices are the minimun path among current deployed same services.
            # In initial case: [[x,...,idCloud]]
            # In other case: [[x,...,idCloud],[y,...,z]]

            # OPTION A: a subsection
            # nodes = self.compute_NodeDESCandidates(node_src, alloc_DES, sim, DES_dst)
            # mergednodes = list(itertools.chain(*nodes))
            # mergednodes = np.unique(mergednodes)

            # OPTION B: all nodes
            mergednodes = sim.topology.G.nodes

            # logging.info("\t Candidate list: "+str(mergednodes))

            best_node = self.WA_EVALUATION(sim, node_src, mergednodes, message, app_name, service)
            # logging.info("\t BEST_NODE : " + str(best_node))

            self.idEvaluation += 1

            des = sim.get_DES_from_Service_In_Node(best_node, app_name, service)

            logging.info("RESULTS: bestNODE: %i, DES: %s" % (best_node, des))

            if des == []:
                logging.info("NEW DEPLOYMENT IS REQUIRED in node: %i ", best_node)
                des = self.doDeploy(sim, app_name, service, best_node)

                # sim.print_debug_assignaments()
            else:
                des = [des]
                print("HERE Node: %i, APP: %s , SERVICE: %s" % (best_node, app_name, service))
                logging.info("From node choice: DES: %s " % (des))

            # TODO gestionar best_node action

            path = self.get_the_path(sim.topology.G, node_src, best_node)
            self.controlServices[(node_src, service)] = (path, des)

        path, des = self.controlServices[(node_src, service)]
        # print path, des
        # print "---"*20
        # The number of nodes control the updating of the cache. If the number of nodes changes, the cache is totally cleaned.
        # currentNodes = len(sim.topology.G.nodes)
        # if not self.invalid_cache_value == currentNodes:
        #     self.invalid_cache_value = currentNodes
        #     self.cache = {}
        #     self.controlServices = {}

        return [path], des

    def get_path_from_failure(self, sim, message, link, alloc_DES, alloc_module, traffic, ctime, from_des):
        # print "Example of enrouting"
        # print message.path # [86, 242, 160, 164, 130, 301, 281, 216]
        # print message.dst_int  # 301
        # print link #(130, 301) link is broken! 301 is unreacheble

        idx = message.path.index(link[0])
        # print "IDX: ",idx
        if idx == len(message.path):
            # The node who serves ... not possible case
            return [], []
        else:
            node_src = message.path[idx]  # In this point to the other entity the system fail
            # print "SRC: ",node_src # 164

            node_dst = message.path[len(message.path) - 1]
            # print "DST: ",node_dst #261
            # print "INT: ",message.dst_int #301

            path, des = self.get_path(sim, message.app_name, message, node_src, alloc_DES, alloc_module, traffic, from_des)
            if len(path[0]) > 0:
                # print path # [[164, 130, 380, 110, 216]]
                # print des # [40]

                concPath = message.path[0 : message.path.index(path[0][0])] + path[0]
                # print concPath # [86, 242, 160, 164, 130, 380, 110, 216]
                newINT = node_src  # path[0][2]
                # print newINT # 380

                message.dst_int = newINT
                return [concPath], des
            else:
                return [], []
