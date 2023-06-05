from pydantic import BaseSettings


class OpenAIConfig(BaseSettings):
    token: str = "sk-###"
    organization: str = "org-###"


class ApplicationSettings(BaseSettings):
    aws_access_key_id: str = "AKIA###"
    aws_secret_access_key: str = "###"
    aws_region: str = "us-east-1"
    assignments_table: str = "llm4_freetext_assignments"
    responses_table: str = "llm4_freetext_responses"
