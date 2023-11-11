from pydantic import BaseSettings, Field
from freetext.assignment_stores import AssignmentStoreConfig
from freetext.response_stores import ResponseStoreConfig
from freetext.prompt_stores import PromptStoreConfig, PlainTextPromptStoreConfig


class OpenAIConfig(BaseSettings):
    token: str = "sk-###"
    organization: str = "org-###"
    model: str = "gpt-3.5-turbo"


class ApplicationSettings(BaseSettings):
    # A secret that must be provided in the header of the request to create a
    # new assignment. This is a simple (but not very secure) way to prevent
    # random people from creating assignments (which could be used to abuse
    # your OpenAI API key)
    assignment_creation_secret: str = "I'm totally allowed to make a project"

    # To override the config for stores, replace Field(..., discriminator="type") with the config you want, e.g.:
    # assignment_store: AssignmentStoreConfig = JSONAssignmentStoreConfig(path="assignments.json")
    # or
    # assignment_store: AssignmentStoreConfig = InMemoryAssignmentStoreConfig()
    assignment_store: AssignmentStoreConfig = Field(..., discriminator="type")
    response_store: ResponseStoreConfig = Field(..., discriminator="type")
    prompt_store: PromptStoreConfig = PlainTextPromptStoreConfig(root="prompts/default")
