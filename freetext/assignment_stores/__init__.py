from .AssignmentStore import AssignmentStore, InMemoryAssignmentStore
from .JSONFileAssignmentStore import JSONFileAssignmentStore
from .DynamoAssignmentStore import DynamoAssignmentStore
from pydantic import BaseModel
from typing import Literal, Union


class InMemoryAssignmentStoreConfig(BaseModel):
    type: str = Literal["in_memory"]


class JSONAssignmentStoreConfig(BaseModel):
    type: str = Literal["json"]
    path: str = "assignments.json"


class DynamoAssignmentStoreConfig(BaseModel):
    type: str = Literal["dynamo"]
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    table_name: str


AssignmentStoreConfig = Union[
    InMemoryAssignmentStoreConfig,
    JSONAssignmentStoreConfig,
    DynamoAssignmentStoreConfig,
]


def create_assignment_store(config: AssignmentStoreConfig) -> AssignmentStore:
    """Factory function for creating a assignment store from a config object."""
    if config.type == Literal["in_memory"]:
        return InMemoryAssignmentStore()
    elif config.type == Literal["json"]:
        return JSONFileAssignmentStore(config.path)
    elif config.type == Literal["dynamo"]:
        return DynamoAssignmentStore(
            config.aws_access_key_id,
            config.aws_secret_access_key,
            config.aws_region,
            config.table_name,
        )
    else:
        raise ValueError(f"Unknown assignment store type: {config.type}")


__all__ = [
    "AssignmentStore",
    "AssignmentStoreConfig",
    "InMemoryAssignmentStore",
    "InMemoryAssignmentStoreConfig",
    "JSONFileAssignmentStore",
    "JSONAssignmentStoreConfig",
    "DynamoAssignmentStore",
    "DynamoAssignmentStoreConfig",
    "create_assignment_store",
]
