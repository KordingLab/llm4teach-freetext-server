from ..llm4text_types import Assignment, Feedback, Submission
from ..response_stores.ResponseStore import ResponseStore


import datetime
import json
import pathlib


class JSONFileResponseStore(ResponseStore):
    def __init__(self, path: str | pathlib.Path):
        self._path = pathlib.Path(path)

    def save(
        self,
        assignment: Assignment,
        submission: Submission,
        all_feedback: list[Feedback],
    ):
        # Append a new JSONL line:
        if not self._path.exists():
            with open(self._path, "w") as f:
                f.write("")
        with open(self._path, "a") as f:
            f.write(
                json.dumps(
                    {
                        "assignment": assignment.dict(),
                        "submission": submission.dict(),
                        "all_feedback": [f.dict() for f in all_feedback],
                        "timestamp": datetime.datetime.now().isoformat(),
                    }
                )
                + "\n"
            )
