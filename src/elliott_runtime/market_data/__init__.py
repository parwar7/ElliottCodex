"""Local, factual market-data ingestion."""

from .ingestion import MarketDataError, load_csv, load_json

__all__ = ["MarketDataError", "load_csv", "load_json"]

