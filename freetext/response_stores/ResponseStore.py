from typing import Protocol
from ..llm4text_types import Assignment, Submission, Feedback


class ResponseStore(Protocol):
    def save(
        self,
        assignment: Assignment,
        submission: Submission,
        all_feedback: list[Feedback],
    ):
        ...


class InMemoryResponseStore(ResponseStore):
    def __init__(self):
        self._responses = {}

    def save(
        self,
        assignment: Assignment,
        submission: Submission,
        all_feedback: list[Feedback],
    ):
        self._responses[(assignment, submission)] = all_feedback


__all__ = [
    "ResponseStore",
    "InMemoryResponseStore",
]
