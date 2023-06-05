from pydantic import BaseSettings


class OpenAIConfig(BaseSettings):
    token: str = "sk-###"
    organization: str = "org-###"


class ApplicationSettings(BaseSettings):
    assignment_creation_secret: str = "I'm totally allowed to make a project"
    aws_access_key_id: str = "AKIA###"
    aws_secret_access_key: str = "###"
    aws_region: str = "us-east-1"
    assignments_table: str = "llm4_freetext_assignments"
    responses_table: str = "llm4_freetext_responses"
