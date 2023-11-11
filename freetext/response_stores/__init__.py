from .ResponseStore import ResponseStore, InMemoryResponseStore
from .JSONFileResponseStore import JSONFileResponseStore
from .DynamoResponseStore import DynamoResponseStore
from pydantic import BaseModel
from typing import Literal, Union


class InMemoryResponseStoreConfig(BaseModel):
    type: str = Literal["in_memory"]


class JSONResponseStoreConfig(BaseModel):
    type: str = Literal["json"]
    path: str = "responses.json"


class DynamoResponseStoreConfig(BaseModel):
    type: str = Literal["dynamo"]
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    table_name: str


ResponseStoreConfig = Union[
    InMemoryResponseStoreConfig, JSONResponseStoreConfig, DynamoResponseStoreConfig
]


def create_response_store(config: ResponseStoreConfig) -> ResponseStore:
    """Factory function for creating a response store from a config object."""
    if config.type == Literal["in_memory"]:
        return InMemoryResponseStore()
    elif config.type == Literal["json"]:
        return JSONFileResponseStore(config.path)
    elif config.type == Literal["dynamo"]:
        return DynamoResponseStore(
            config.aws_access_key_id,
            config.aws_secret_access_key,
            config.aws_region,
            config.table_name,
        )
    else:
        raise ValueError(f"Unknown response store type: {config.type}")


__all__ = [
    "ResponseStore",
    "ResponseStoreConfig",
    "InMemoryResponseStore",
    "InMemoryResponseStoreConfig",
    "JSONFileResponseStore",
    "JSONResponseStoreConfig",
    "DynamoResponseStore",
    "DynamoResponseStoreConfig",
    "create_response_store",
]
