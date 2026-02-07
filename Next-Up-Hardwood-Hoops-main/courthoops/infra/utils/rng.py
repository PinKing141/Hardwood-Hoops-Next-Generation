from abc import ABC, abstractmethod
import random
from typing import Optional, Sequence, TypeVar

T = TypeVar("T")


class IRNG(ABC):
    """Interface for deterministic random number generation."""

    @abstractmethod
    def randint(self, a: int, b: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def random(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def choice(self, seq: Sequence[T]) -> T:
        raise NotImplementedError

    @abstractmethod
    def choice_weighted(self, seq: Sequence[T], weights: Sequence[float]) -> T:
        """Weighted choice that mirrors random.choices semantics."""
        raise NotImplementedError


class PythonRNG(IRNG):
    """Wrapper around Python's RNG to enable dependency injection."""

    def __init__(self, seed: Optional[int] = None):
        self._rand = random.Random(seed)

    def randint(self, a: int, b: int) -> int:
        return self._rand.randint(a, b)

    def random(self) -> float:
        return self._rand.random()

    def choice(self, seq: Sequence[T]) -> T:
        return self._rand.choice(seq)

    def choice_weighted(self, seq: Sequence[T], weights: Sequence[float]) -> T:
        return self._rand.choices(seq, weights=weights, k=1)[0]


class SeededRNG(PythonRNG):
    """Semantic alias for a seeded RNG."""
    pass

