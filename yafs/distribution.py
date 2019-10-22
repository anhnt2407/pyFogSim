"""
This module is a generic class to introduce whatever kind of distribution in the simulator

"""
# TODO Improve documentation

import random
import warnings
from abc import ABC

import numpy as np


class Distribution(ABC):  # TODO This interface defines nothing??
    """
    Abstract class
    """

    def __init__(self, name):
        self.name = name

    def __next__(self):
        None


class DeterministicDistribution(Distribution):
    def __init__(self, time, **kwargs):
        warnings.warn(
            "The exponentialDistribution class is deprecated and " "will be removed in version 2.0.0. " "Use the exponential_distribution function instead.",
            FutureWarning,
            stacklevel=8,
        )
        self.time = time
        super(DeterministicDistribution, self).__init__(**kwargs)

    def __next__(self):
        return self.time


class DeterministicDistributionStartPoint(Distribution):
    def __init__(self, start, time, **kwargs):
        self.start = start
        self.time = time
        self.started = False
        super(DeterministicDistributionStartPoint, self).__init__(**kwargs)

    def __next__(self):
        if not self.started:
            self.started = True
            return self.start
        else:
            return self.time


class ExponentialDistribution(Distribution):
    def __init__(self, lambd, seed=1, **kwargs):
        warnings.warn(
            "The exponentialDistribution class is deprecated and " "will be removed in version 2.0.0. " "Use the exponential_distribution function instead.",
            FutureWarning,
            stacklevel=8,
        )
        super(ExponentialDistribution, self).__init__(**kwargs)
        self.l = lambd
        self.rnd = np.random.RandomState(seed)

    def __next__(self):
        value = int(self.rnd.exponential(self.l, size=1)[0])
        if value == 0:
            return 1
        return value


class ExponentialDistributionStartPoint(Distribution):
    def __init__(self, start, lambd, **kwargs):
        self.lambd = lambd
        self.start = start
        self.started = False
        super(ExponentialDistributionStartPoint, self).__init__(**kwargs)

    def __next__(self):
        if not self.started:
            self.started = True
            return self.start
        else:
            return int(np.random.exponential(self.lambd, size=1)[0])


class UniformDistribution(Distribution):
    def __init__(self, min, max, **kwargs):
        self.min = min
        self.max = max
        super(UniformDistribution, self).__init__(**kwargs)

    def __next__(self):
        return random.randint(self.min, self.max)