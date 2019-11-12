from abc import ABC
from copy import copy
from typing import List, Optional, Dict


class Service:
    """Definition of Generators and Consumers (AppEdges and TupleMappings in iFogSim)

    Args:
        message_in: input message
        message_out: Output message. If Empty the module is a sink
        probability: Probability to process the message
        p: a list of probabilities to send this message. Broadcasting  # TODO Understand and refactor
        module_dst: a list of modules who can receive this message. Broadcasting.
    """
    def __init__(self, message_in: "Message", message_out: "Message", probability: float = 1.0, p: Optional[List] = None,
                 module_dst: Optional[List] = None):
        self.message_in = message_in
        self.message_out = message_out
        self.probability = probability
        self.module_dst = module_dst if module_dst else []


class Module(ABC):
    def __init__(self, name: str, data: Optional[Dict] = None):
        self.name = name
        self.data = data if data else {}  # TODO find better name


class Source(Module):
    pass


class Operator(Module):
    def __init__(self, name: str, data: Optional[Dict] = None):
        super().__init__(name, data)
        self.services = []  # can deal with different messages, "tuppleMapping (iFogSim)"

    def add_service(self, message_in: "Message", message_out: "Message", probability: float = 1.0, p: Optional[List] = None,
                    module_dst: Optional[List] = None):
        self.services.append(Service(message_in, message_out, probability, p, module_dst))


class Sink(Module):
    pass


class Message:
    """Representation of a request between two modules.

    Args:
        name: Message name, unique for each application
        src: Name of the module who sent this message
        dst: Name of the module who receives this message
        instructions: Number of instructions to be executed (Instead of MIPS, we use IPt since the time is relative to the simulation units.)
        size: Size in bytes

    Internal args used in the **yafs.core** are:
        timestamp (float): simulation time. Instant of time that was created.
        path (list): a list of entities of the topology that has to travel to reach its target module from its source module.
        next_dst (int): an identifier of the intermediate entity in which it is in the process of transmission.
        app_name (str): the name of the application
    """

    def __init__(self, name: str, src: Module, dst: Module, instructions: int = 0, size: int = 0):
        self.name = name
        self.src = src
        self.dst = dst
        self.instructions = instructions  # TODO ??
        self.size = size

        self.timestamp = 0  # TODO Where is this used?
        self.path = []  # TODO Not sure this should be encoded in the message, only the routing can know this?
        self.next_dst = None  # TODO Understand this
        self.application = None  # TODO Remove this, Message should have no knowledge about application
        self.timestamp_rec = 0  # TODO ??

    def __str__(self):
        return f"Message<name=\"{self.name}\", src=\"{self.src.name}\", dst=\"{self.dst.name}\">"

    def evolve(self, **kwargs) -> "Message":
        message = copy(self)
        for key, value in kwargs.items():
            setattr(message, key, value)
        return message


class Application:
    """Defined by a Directed Acyclic Graph (DAG) between modules that generates, processes and receives messages.

    Args:
        name: Application name, unique within the same topology.
    """

    def __init__(self, name: str, source: Source, operators: List[Operator], sink: Sink):
        self.name = name
        self.source = source
        self.modules = operators
        self.sink = sink

    @property
    def service_modules(self):
        return self.modules
