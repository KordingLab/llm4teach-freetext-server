from typing import Protocol


PromptID = str


class PromptStore(Protocol):
    def get_prompt(self, prompt_id: PromptID) -> str:
        ...

    def set_prompt(self, prompt_id: PromptID, prompt: str):
        ...

    def __delitem__(self, key: PromptID):
        ...

    def get_prompt_ids(self) -> list[PromptID]:
        ...

    def __contains__(self, key: PromptID) -> bool:
        ...


class InMemoryPromptStore(PromptStore):
    def __init__(self):
        self._prompts = {}

    def get_prompt(self, prompt_id: PromptID) -> str:
        return self._prompts[prompt_id]

    def set_prompt(self, prompt_id: PromptID, prompt: str):
        self._prompts[prompt_id] = prompt

    def __delitem__(self, key: PromptID):
        del self._prompts[key]

    def get_prompt_ids(self) -> list[PromptID]:
        return list(self._prompts.keys())

    def __contains__(self, key: PromptID) -> bool:
        return key in self._prompts

