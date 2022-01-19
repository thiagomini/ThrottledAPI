import itertools
import sys
import time
from dataclasses import dataclass, field
from functools import reduce
from math import log10
from typing import Iterable, Union

PRECISION: float = 1e-2
DECIMAL_PLACES: int = int(-log10(PRECISION))

DATACLASS_KWARGS = {"frozen": True}
if sys.version_info >= (3, 10):
    DATACLASS_KWARGS["slots"] = True


def ensure_precision(number: float) -> float:
    return round(number, DECIMAL_PLACES)


def epoch() -> float:
    """Return the current epoch in seconds."""
    return ensure_precision(time.time())


@dataclass(**DATACLASS_KWARGS)
class Hit:
    key: str = field(
        default_factory=str,
        metadata={"description": "The base contribution to the hit key."},
    )
    time: float = field(
        default_factory=epoch,
        metadata={
            "units": "seconds",
            "description": "time the hit occurred since epoch.",
        },
    )
    cost: int = 1

    def __lt__(self, other: "Hit") -> bool:
        return self.time < other.time

    def __gt__(self, other: "Hit") -> bool:
        return self.time > other.time


@dataclass(**DATACLASS_KWARGS)
class Rate:
    """
    :param hits: number of hits
    :param interval: interval for the hits in seconds
    :return: a Rate object
    """

    hits: int
    interval: float

    @property
    def ratio(self) -> float:
        """Return the rate as float in hits/seconds units."""
        return max(self.hits, 0) / max(self.interval, PRECISION)

    @classmethod
    def __assert_class(cls, other) -> "Rate":
        if not isinstance(other, Rate):
            raise TypeError(
                f"Can't compare {cls.__name__} with {other.__class__.__name__}"
            )
        return other

    def __lt__(self, other: Union["Rate", int, float]) -> bool:
        if isinstance(other, (int, float)):
            return self.ratio < other
        return self.ratio < other.ratio

    def __gt__(self, other: Union["Rate", int, float]) -> bool:
        if isinstance(other, (int, float)):
            return self.ratio > other
        return self.ratio > other.ratio

    def __eq__(self, other) -> bool:
        if isinstance(other, (int, float)):
            return self.ratio == other
        other = self.__assert_class(other)
        return self.ratio == other.ratio

    @classmethod
    def from_hits(cls, hits: Iterable[Hit]) -> "Rate":
        it1, it2, it3 = itertools.tee(hits, 3)
        cost: int = reduce(lambda a, b: a + b.cost, it1, 0)
        return cls(
            hits=cost,
            interval=ensure_precision(max(it2).time - min(it3).time) if cost > 0 else 0,
        )
