from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class MarketProvider(ABC):
    @abstractmethod
    async def get_price(self, symbol: str) -> Optional[float]:
        raise NotImplementedError

    @abstractmethod
    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        raise NotImplementedError


class DummyProvider(MarketProvider):
    async def get_price(self, symbol: str) -> Optional[float]:
        return None

    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        return None


# TODO: Implement Binance/Bybit provider here later.
