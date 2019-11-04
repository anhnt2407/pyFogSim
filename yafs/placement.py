import logging
from abc import abstractmethod, ABC
from typing import Callable


logger = logging.getLogger(__name__)


class Placement(ABC):
    """A placement (or allocation) algorithm controls where to locate the service modules and their replicas in the different nodes of the topology, according to load criteria or other objectives.

    A placement consists out of two functions:
    - *initial_allocation*: Invoked at the start of the simulation
    - *run*: Invoked according to the assigned temporal distribution

    Args:
        name: Placement name
        activation_dist (function): a distribution function to active the *run* function in execution time  TODO What das function mean? Callable?

    Kwargs:
        param (dict): the parameters of the *activation_dist*  TODO ???
    """

    def __init__(self, name: str, activation_dist: Callable = None):  # TODO Remove logger
        self.name = name  # TODO What do we need this for
        self.activation_dist = activation_dist
        self.scaleServices = []  # TODO What does this do??

    def scaleService(self, scale):  # TODO Refactor, this is not pythonic
        self.scaleServices = scale

    def get_next_activation(self):
        """
        Returns:
            the next time to be activated
        """
        return next(self.activation_dist)  # TODO Data type?

    @abstractmethod
    def initial_allocation(self, simulation: "Simulation", app_name: str):  # TODO Why does this know about the simulation?
        """Given an ecosystem, it starts the allocation of modules in the topology."""

    def run(self, simulation: "Simulation"):  # TODO Does this have to be implemented?  # TODO Why does this know about the simulation?
        """This method will be invoked during the simulation to change the assignment of the modules to the topology."""
        logger.debug("Activiting - RUN - Placement")


class JSONPlacement(Placement):  # TODO The placement should not care how it was instantiated
    def __init__(self, json, **kwargs):
        super(JSONPlacement, self).__init__(**kwargs)
        self.data = json

    def initial_allocation(self, simulation, app_name):
        for item in self.data["initialAllocation"]:
            if app_name == item["app"]:
                module = item["module_name"]
                idtopo = item["id_resource"]

                app = simulation.applications[app_name]
                process_id = simulation.deploy_module(app_name, module, app.services[module], [idtopo])  # TODO unused variable


class JSONPlacementOnlyCloud(Placement):
    """Initialization of the service only in the cloud. We filter the rest of the assignments from the JSON file"""

    def __init__(self, json, idcloud, **kwargs):
        super(JSONPlacementOnlyCloud, self).__init__(**kwargs)
        self.data = json
        self.idcloud = idcloud
        logger.info(" Placement Initialization of %s in NodeCLOUD: %i" % (self.name, self.idcloud))

    def initial_allocation(self, sim, app_name):
        for item in self.data["initialAllocation"]:
            idtopo = item["id_resource"]
            print(idtopo)
            if idtopo == self.idcloud:
                # print item
                app_name = item["app"]
                module = item["module_name"]
                app = sim.apps[app_name]
                process_id = sim.deploy_module(app_name, module, app.services[module], [idtopo])


class CloudPlacement(Placement):
    """Locates the services of the application in the cheapest cloud regardless of where the sources or sinks are located.  # TODO Docstring wrong?

    It only runs once, in the initialization.
    """

    def initial_allocation(self, simulation: "Simulation", app_name: str):  # TODO Why does the placement know about the simulation?
        id_cluster = simulation.topology.find_IDs({"mytag": "cloud"})  # TODO These are very implicit assumptions about module naming...
        app = simulation.applications[app_name]
        for service in app.services:
            if service in self.scaleServices:
                for rep in range(0, self.scaleServices[service]):
                    simulation.deploy_module(app_name, service, app.services[service], id_cluster)


class CloudPlacementIFogSIM(Placement):
    """
    This implementation locates the services of the application in the cheapest cloud regardless of where the sources or sinks are located.

    It only runs once, in the initialization.

    """

    def initial_allocation(self, simulation, app_name):
        # We find the ID-nodo/resource
        value = {"model": "Cluster"}
        id_cluster = simulation.topology.find_IDs(value)  # there is only ONE Cluster
        value = {"model": "m-"}
        id_mobiles = simulation.topology.find_IDs(value)

        # Given an application we get its modules implemented
        app = simulation.apps[app_name]
        for module in list(app.services.keys()):
            if "Coordinator" == module:
                if "Coordinator" in list(self.scaleServices.keys()):
                    # print self.scaleServices["Coordinator"]
                    for rep in range(0, self.scaleServices["Coordinator"]):
                        process_id = simulation.deploy_module(app_name, module, app.services[module], id_cluster)  # Deploy as many modules as elements in the array

            elif "Calculator" == module:
                if "Calculator" in list(self.scaleServices.keys()):
                    for rep in range(0, self.scaleServices["Calculator"]):
                        process_id = simulation.deploy_module(app_name, module, app.services[module], id_cluster)

            elif "Client" == module:
                process_id = simulation.deploy_module(app_name, module, app.services[module], id_mobiles)


class FogPlacement(Placement):
    """
    This implementation locates the services of the application in the fog-device regardless of where the sources or sinks are located.

    It only runs once, in the initialization.

    """

    def initial_allocation(self, simulation, app_name):
        # We find the ID-nodo/resource
        value = {"model": "Cluster"}
        id_cluster = simulation.topology.find_IDs(value)  # there is only ONE Cluster

        value = {"model": "d-"}
        id_proxies = simulation.topology.find_IDs(value)

        value = {"model": "m-"}
        id_mobiles = simulation.topology.find_IDs(value)

        # Given an application we get its modules implemented
        app = simulation.applications[app_name]
        for module in list(app.services.keys()):
            if "Coordinator" == module:
                if "Coordinator" in list(self.scaleServices.keys()):
                    for rep in range(0, self.scaleServices["Coordinator"]):
                        process_id = simulation.deploy_module(app_name, module, app.services[module], id_cluster)  # Deploy as many modules as elements in the array
            elif "Calculator" == module:
                if "Calculator" in list(self.scaleServices.keys()):
                    for rep in range(0, self.scaleServices["Calculator"]):
                        process_id = simulation.deploy_module(app_name, module, app.services[module], id_proxies)
            elif "Client" == module:
                process_id = simulation.deploy_module(app_name, module, app.services[module], id_mobiles)


class ClusterPlacement(Placement):
    """Locates the services of the application in the cheapest cluster regardless of where the sources or sinks are located.  # TODO Docstring wrong?

    Only runs once during initialization.
    """

    def initial_allocation(self, simulation: "Simulation", app_name: str):  # TODO Why does this know about the simulation?
        # We find the ID-nodo/resource
        id_cluster = simulation.topology.find_IDs({"model": "Cluster"})  # there is only ONE Cluster  # TODO These are very implicit assumptions about module naming...
        id_mobiles = simulation.topology.find_IDs({"model": "m-"})  # TODO These are very implicit assumptions about module naming...

        # Given an application we get its modules implemented
        app = simulation.apps[app_name]
        for module in list(app.services.keys()):
            if "Coordinator" == module:
                if "Coordinator" in list(self.scaleServices.keys()):
                    # print self.scaleServices["Coordinator"]
                    for rep in range(0, self.scaleServices["Coordinator"]):
                        # Deploy as many modules as elements in the array
                        process_id = simulation.deploy_module(app_name, module, app.services[module], id_cluster)  # TODO unused variable

            elif "Calculator" == module:
                if "Calculator" in list(self.scaleServices.keys()):
                    for rep in range(0, self.scaleServices["Calculator"]):
                        process_id = simulation.deploy_module(app_name, module, app.services[module], id_cluster)  # TODO unused variable

            elif "Client" == module:
                process_id = simulation.deploy_module(app_name, module, app.services[module], id_mobiles)  # TODO unused variable


class EdgePlacement(Placement):
    """Locates the services of the application in the cheapest cluster regardless of where the sources or sinks are located.  # TODO Docstring wrong?

    Only runs once during initialization.
    """

    def initial_allocation(self, simulation, app_name):
        # We find the ID-nodo/resource
        id_cluster = simulation.topology.find_IDs({"model": "Cluster"})  # there is only ONE Cluster  # TODO These are very implicit assumptions about module naming...
        id_proxies = simulation.topology.find_IDs({"model": "d-"})  # TODO These are very implicit assumptions about module naming...
        id_mobiles = simulation.topology.find_IDs({"model": "m-"})  # TODO These are very implicit assumptions about module naming...

        # Given an application we get its modules implemented
        app = simulation.apps[app_name]
        for module in list(app.services.keys()):
            if "Coordinator" == module:
                # Deploy as many modules as elements in the array
                process_id = simulation.deploy_module(app_name, module, app.services[module], id_cluster)  # TODO Unused variable
            elif "Calculator" == module:
                process_id = simulation.deploy_module(app_name, module, app.services[module], id_proxies)  # TODO Unused variable
            elif "Client" == module:
                process_id = simulation.deploy_module(app_name, module, app.services[module], id_mobiles)  # TODO Unused variable


class NoPlacementOfModules(Placement):
    """
    This implementation locates the services of the application in the cheapest cluster regardless of where the sources or sinks are located.

    It only runs once, in the initialization.

    """

    def initial_allocation(self, simulation, app_name):
        # The are not modules to be allocated
        None
