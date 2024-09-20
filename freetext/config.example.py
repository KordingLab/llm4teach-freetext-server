from pydantic_settings import BaseSettings


class OpenAIConfig(BaseSettings):
    token: str = "sk-###"
    organization: str = "org-###"


class ApplicationSettings(BaseSettings):
    # A secret that must be provided in the header of the request to create a
    # new assignment. This is a simple (but not very secure) way to prevent
    # random people from creating assignments (which could be used to abuse
    # your OpenAI API key)
    assignment_creation_secret: str = "I'm totally allowed to make a project"

    # AWS credentials and table names for storing assignments and responses.
    # If you're using local (e.g., JSON-based) stores, you can set these all to
    # empty strings or ignore them entirely.
    aws_access_key_id: str = "AKIA###"
    aws_secret_access_key: str = "###"
    aws_region: str = "us-east-1"
    assignments_table: str = "llm4_freetext_assignments"
    responses_table: str = "llm4_freetext_responses"
