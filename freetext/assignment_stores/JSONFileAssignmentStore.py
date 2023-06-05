from freetext.assignment_stores.AssignmentStore import AssignmentStore
from freetext.llm4text_types import Assignment, AssignmentID


import json
import os
import uuid


class JSONFileAssignmentStore(AssignmentStore):
    """
    A AssignmentStore that stores assignments in a JSON file.
    """

    def __init__(self, filename: str):
        self._filename = filename

    def __getitem__(self, key: AssignmentID) -> Assignment:
        """
        Returns the assignment with the given ID.
        """
        # Create the file if it doesn't exist
        if not os.path.exists(self._filename):
            with open(self._filename, "w") as f:
                json.dump({}, f)
        with open(self._filename, "r") as f:
            assignments = {k: Assignment.parse_obj(v) for k, v in json.load(f).items()}

        return assignments[key]

    def __setitem__(self, key: AssignmentID, value: Assignment) -> None:
        """
        Sets the assignment with the given ID.
        """
        # Create the file if it doesn't exist
        if not os.path.exists(self._filename):
            with open(self._filename, "w") as f:
                json.dump({}, f)
        with open(self._filename, "r") as f:
            assignments = {k: Assignment.parse_obj(v) for k, v in json.load(f).items()}

        print(assignments, flush=True)
        assignments[key] = value
        print(assignments, flush=True)

        with open(self._filename, "w") as f:
            json.dump({k: dict(v) for k, v in assignments.items()}, f)

    def __delitem__(self, key: AssignmentID) -> None:
        """
        Deletes the assignment with the given ID.
        """

        with open(self._filename, "r") as f:
            assignments = json.load(f)

        del assignments[key]

        with open(self._filename, "w") as f:
            json.dump({k: dict(v) for k, v in assignments.items()}, f)

    def get_assignment_ids(self) -> list[AssignmentID]:
        with open(self._filename, "r") as f:
            assignments = json.load(f)

        return list(assignments.keys())

    def new_assignment(self, assignment: Assignment) -> AssignmentID:
        """
        Adds a new assignment to the store.
        """
        assignment_id = AssignmentID(str(uuid.uuid4()))
        self[assignment_id] = assignment

        return assignment_id

    def __iter__(self) -> list[str]:
        """
        Returns a list of all assignment IDs.
        """
        if not os.path.exists(self._filename):
            with open(self._filename, "w") as f:
                json.dump({}, f)
        with open(self._filename, "r") as f:
            assignments = json.load(f)

        return list(assignments.keys())

    def __len__(self) -> int:
        """
        Returns the number of assignments.
        """
        if not os.path.exists(self._filename):
            with open(self._filename, "w") as f:
                json.dump({}, f)
        with open(self._filename, "r") as f:
            assignments = json.load(f)

        return len(assignments)

    def __contains__(self, key: AssignmentID) -> bool:
        """
        Returns whether the given assignment ID is in the AssignmentStore.
        """
        if not os.path.exists(self._filename):
            with open(self._filename, "w") as f:
                json.dump({}, f)
        with open(self._filename, "r") as f:
            assignments = json.load(f)

        return key in assignments
