from .PromptStore import PromptStore, InMemoryPromptStore
from .PlainTextPromptStore import PlainTextPromptStore
from pydantic import BaseModel
from typing import Literal, Union


class InMemoryPromptStoreConfig(BaseModel):
    type: str = Literal["in_memory"]


class PlainTextPromptStoreConfig(BaseModel):
    type: str = Literal["plain_text"]
    root: str


PromptStoreConfig = Union[InMemoryPromptStoreConfig, PlainTextPromptStoreConfig]


def create_prompt_store(config: PromptStoreConfig) -> PromptStore:
    """Factory function for creating a prompt store from a config object."""
    if config.type == Literal["in_memory"]:
        return InMemoryPromptStore()
    elif config.type == Literal["plain_text"]:
        return PlainTextPromptStore(config.root)
    else:
        raise ValueError(f"Unknown prompt store type: {config.type}")


__all__ = [
    "PromptStore",
    "PromptStoreConfig",
    "InMemoryPromptStore",
    "InMemoryPromptStoreConfig",
    "PlainTextPromptStore",
    "PlainTextPromptStoreConfig",
    "create_prompt_store",
]
