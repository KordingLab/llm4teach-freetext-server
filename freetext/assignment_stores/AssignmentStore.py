import uuid
from typing import Protocol

from ..llm4text_types import Assignment, AssignmentID


class AssignmentStore(Protocol):
    """
    A class that handles storing assignments (and later, submissions.)
    """

    def get_assignment(self, key: AssignmentID) -> Assignment:
        """
        Returns the assignment with the given ID.
        """

        raise NotImplementedError()

    def set_assignment(self, key: AssignmentID, value: Assignment) -> None:
        """
        Sets the assignment with the given ID.
        """
        raise NotImplementedError()

    def __delitem__(self, key: AssignmentID) -> None:
        """
        Deletes the assignment with the given ID.
        """
        raise NotImplementedError()

    def get_assignment_ids(self) -> list[AssignmentID]:
        raise NotImplementedError()

    def new_assignment(self, assignment: Assignment) -> AssignmentID:
        """
        Adds a new assignment to the store.
        """
        raise NotImplementedError()

    def __contains__(self, key: AssignmentID) -> bool:
        """
        Returns whether the given assignment ID is in the AssignmentStore.
        """
        raise NotImplementedError()


class InMemoryAssignmentStore(AssignmentStore):
    """
    An in-memory AssignmentStore that stores assignments in a dictionary.

    """

    def __init__(self):
        print("InMemory Store...")
        self._assignments = {}

    def get_assignment(self, key: AssignmentID) -> Assignment:
        """
        Returns the assignment with the given ID.

        """

        return self._assignments[key]

    def set_assignment(self, key: AssignmentID, value: Assignment) -> None:
        """
        Sets the assignment with the given ID.

        """

        self._assignments[key] = value

    def __delitem__(self, key: AssignmentID) -> None:
        """
        Deletes the assignment with the given ID.

        """

        del self._assignments[key]

    def get_assignment_ids(self) -> list[AssignmentID]:
        return list(self._assignments.keys())

    def new_assignment(self, assignment: Assignment) -> AssignmentID:
        """
        Adds a new assignment to the store.

        """

        assignment_id = AssignmentID(str(uuid.uuid4()))
        self._assignments[assignment_id] = assignment
        return assignment_id

    def __contains__(self, key: AssignmentID) -> bool:
        """
        Returns whether the given assignment ID is in the AssignmentStore.

        """

        return key in self._assignments


__all__ = ["AssignmentStore", "InMemoryAssignmentStore"]
