from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

import aiohttp


class MarketError(RuntimeError):
    pass


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


class BybitProvider(MarketProvider):
    base_url = "https://api.bybit.com"

    async def get_price(self, symbol: str) -> Optional[float]:
        data = await self._request(
            "/v5/market/tickers",
            {"category": "linear", "symbol": symbol},
        )
        try:
            return float(data["result"]["list"][0]["lastPrice"])
        except (KeyError, IndexError, ValueError, TypeError):
            return None

    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        interval = tf.replace("m", "")
        data = await self._request(
            "/v5/market/kline",
            {"category": "linear", "symbol": symbol, "interval": interval, "limit": limit},
        )
        try:
            rows = data["result"]["list"]
        except (KeyError, TypeError):
            return None
        klines = []
        for row in rows:
            klines.append(
                {
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5],
                }
            )
        return klines

    async def _request(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise MarketError(f"Bybit status {resp.status}")
                return await resp.json()


class BitgetProvider(MarketProvider):
    base_url = "https://api.bitget.com"

    async def get_price(self, symbol: str) -> Optional[float]:
        data = await self._request(
            "/api/v2/mix/market/ticker",
            {"symbol": symbol, "productType": "USDT-FUTURES"},
        )
        try:
            return float(data["data"][0]["lastPr"])
        except (KeyError, IndexError, ValueError, TypeError):
            return None

    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        granularity = self._tf_to_seconds(tf)
        data = await self._request(
            "/api/v2/mix/market/candles",
            {
                "symbol": symbol,
                "productType": "USDT-FUTURES",
                "granularity": granularity,
                "limit": limit,
            },
        )
        try:
            rows = data["data"]
        except (KeyError, TypeError):
            return None
        klines = []
        for row in rows:
            klines.append(
                {
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5],
                }
            )
        return klines

    async def _request(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise MarketError(f"Bitget status {resp.status}")
                return await resp.json()

    @staticmethod
    def _tf_to_seconds(tf: str) -> str:
        if tf.endswith("m"):
            return str(int(tf[:-1]) * 60)
        if tf.endswith("h"):
            return str(int(tf[:-1]) * 3600)
        return "900"


class BinanceProvider(MarketProvider):
    base_url = "https://api.binance.com"

    async def get_price(self, symbol: str) -> Optional[float]:
        data = await self._request("/api/v3/ticker/price", {"symbol": symbol})
        try:
            return float(data["price"])
        except (KeyError, ValueError, TypeError):
            return None

    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        interval = tf
        data = await self._request(
            "/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )
        if not isinstance(data, list):
            return None
        klines = []
        for row in data:
            klines.append(
                {
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5],
                }
            )
        return klines

    async def _request(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise MarketError(f"Binance status {resp.status}")
                return await resp.json()


class OkxProvider(MarketProvider):
    base_url = "https://www.okx.com"

    async def get_price(self, symbol: str) -> Optional[float]:
        inst = self._to_inst_id(symbol)
        data = await self._request("/api/v5/market/ticker", {"instId": inst})
        try:
            return float(data["data"][0]["last"])
        except (KeyError, IndexError, ValueError, TypeError):
            return None

    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        inst = self._to_inst_id(symbol)
        bar = self._tf_to_bar(tf)
        data = await self._request(
            "/api/v5/market/candles",
            {"instId": inst, "bar": bar, "limit": limit},
        )
        try:
            rows = data["data"]
        except (KeyError, TypeError):
            return None
        klines = []
        for row in rows:
            klines.append(
                {
                    "open": row[1],
                    "high": row[2],
                    "low": row[3],
                    "close": row[4],
                    "volume": row[5],
                }
            )
        return klines

    async def _request(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise MarketError(f"OKX status {resp.status}")
                return await resp.json()

    @staticmethod
    def _to_inst_id(symbol: str) -> str:
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}-USDT-SWAP"
        return symbol

    @staticmethod
    def _tf_to_bar(tf: str) -> str:
        if tf.endswith("m"):
            return f"{tf[:-1]}m"
        if tf.endswith("h"):
            return f"{tf[:-1]}H"
        return "15m"


class KucoinProvider(MarketProvider):
    base_url = "https://api.kucoin.com"

    async def get_price(self, symbol: str) -> Optional[float]:
        data = await self._request(
            "/api/v1/market/orderbook/level1",
            {"symbol": self._to_symbol(symbol)},
        )
        try:
            return float(data["data"]["price"])
        except (KeyError, ValueError, TypeError):
            return None

    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        interval = self._tf_to_interval(tf)
        data = await self._request(
            "/api/v1/market/candles",
            {"symbol": self._to_symbol(symbol), "type": interval},
        )
        try:
            rows = data["data"]
        except (KeyError, TypeError):
            return None
        klines = []
        for row in rows[:limit]:
            klines.append(
                {
                    "open": row[1],
                    "high": row[3],
                    "low": row[4],
                    "close": row[2],
                    "volume": row[5],
                }
            )
        return klines

    async def _request(self, path: str, params: dict) -> dict:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise MarketError(f"Kucoin status {resp.status}")
                return await resp.json()

    @staticmethod
    def _to_symbol(symbol: str) -> str:
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}-USDT"
        return symbol

    @staticmethod
    def _tf_to_interval(tf: str) -> str:
        if tf.endswith("m"):
            return f"{tf[:-1]}min"
        if tf.endswith("h"):
            return f"{tf[:-1]}hour"
        return "15min"


class AutoProvider(MarketProvider):
    def __init__(self, providers: List[MarketProvider]) -> None:
        self.providers = providers

    async def get_price(self, symbol: str) -> Optional[float]:
        for provider in self.providers:
            try:
                price = await provider.get_price(symbol)
            except Exception:
                price = None
            if price is not None:
                return price
        return None

    async def get_klines(self, symbol: str, tf: str, limit: int) -> Optional[List[dict]]:
        for provider in self.providers:
            try:
                klines = await provider.get_klines(symbol, tf, limit)
            except Exception:
                klines = None
            if klines:
                return klines
        return None
