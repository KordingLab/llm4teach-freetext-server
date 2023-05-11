import json
import os
from typing import Protocol, Annotated
import uuid
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware

from .types import Submission, Assignment, Feedback, AssignmentID
from .feedback_provider import FeedbackProvider, EdgeGPTFeedbackProvider


class AssignmentStore(Protocol):
    """
    A class that handles storing assignments (and later, submissions.)
    """

    def __getitem__(self, key: AssignmentID) -> Assignment:
        """
        Returns the assignment with the given ID.

        """

        raise NotImplementedError()

    def __setitem__(self, key: AssignmentID, value: Assignment) -> None:
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

    def __iter__(self) -> list[str]:
        """
        Returns a list of all assignment IDs.

        """
        raise NotImplementedError()

    def __len__(self) -> int:
        """
        Returns the number of assignments.

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
        self._assignments = {}

    def __getitem__(self, key: AssignmentID) -> Assignment:
        """
        Returns the assignment with the given ID.

        """

        return self._assignments[key]

    def __setitem__(self, key: AssignmentID, value: Assignment) -> None:
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

    def __iter__(self) -> list[str]:
        """
        Returns a list of all assignment IDs.

        """

        return list(self._assignments.keys())

    def __len__(self) -> int:
        """
        Returns the number of assignments.

        """

        return len(self._assignments)

    def __contains__(self, key: AssignmentID) -> bool:
        """
        Returns whether the given assignment ID is in the AssignmentStore.

        """

        return key in self._assignments


class JSONFileAssignmentStore(AssignmentStore):
    """
    A AssignmentStore that stores assignments in a JSON file.

    """

    def __init__(self, filename: str):
        self._filename = filename
        # Create the file if it doesn't exist
        if not os.path.exists(self._filename):
            with open(self._filename, "w") as f:
                json.dump({}, f)

    def __getitem__(self, key: AssignmentID) -> Assignment:
        """
        Returns the assignment with the given ID.

        """

        with open(self._filename, "r") as f:
            assignments = {k: Assignment.parse_obj(v) for k, v in json.load(f).items()}

        return assignments[key]

    def __setitem__(self, key: AssignmentID, value: Assignment) -> None:
        """
        Sets the assignment with the given ID.

        """

        with open(self._filename, "r") as f:
            assignments = {k: Assignment.parse_obj(v) for k, v in json.load(f).items()}

        assignments[key] = value

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

        with open(self._filename, "r") as f:
            assignments = json.load(f)

        assignments[assignment_id] = assignment

        with open(self._filename, "w") as f:
            json.dump({k: dict(v) for k, v in assignments.items()}, f)

        return assignment_id

    def __iter__(self) -> list[str]:
        """
        Returns a list of all assignment IDs.

        """
        with open(self._filename, "r") as f:
            assignments = json.load(f)

        return list(assignments.keys())

    def __len__(self) -> int:
        """
        Returns the number of assignments.

        """

        with open(self._filename, "r") as f:
            assignments = json.load(f)

        return len(assignments)

    def __contains__(self, key: AssignmentID) -> bool:
        """
        Returns whether the given assignment ID is in the AssignmentStore.

        """

        with open(self._filename, "r") as f:
            assignments = json.load(f)

        return key in assignments


class FeedbackRouter:
    """
    A router handles multiple feedback providers and returns aggregated
    feedback from all of them.

    """

    def __init__(
        self,
        feedback_providers: list[FeedbackProvider] | None = None,
        assignment_store: AssignmentStore | None = None,
    ):
        """
        Create a new feedback router, with an optional list of providers and
        assignment store.

        Arguments:
            feedback_providers: A list of feedback providers to use.
            assignment_store: An assignment store to use.

        """
        self._feedback_providers = feedback_providers or []
        self._assignment_store = assignment_store or InMemoryAssignmentStore()

    def add_feedback_provider(self, feedback_provider: FeedbackProvider) -> None:
        """
        Add a feedback provider to the router.

        Arguments:
            feedback_provider: The feedback provider to add.

        Returns:
            None

        """
        self._feedback_providers.append(feedback_provider)

    async def get_feedback(
        self, submission: Submission, assignment: Assignment
    ) -> list[Feedback]:
        """
        Get feedback for a given submission.

        Arguments:
            submission: The submission to get feedback for.

        Returns:
            A list of feedback objects.

        """
        all_feedback = []
        for feedback_provider in self._feedback_providers:
            # get async feedback
            feedback = await feedback_provider.get_feedback(submission, assignment)
            # wait for feedback to be returned
            all_feedback.extend(feedback)

        return all_feedback


class Commons:
    def __init__(self, feedback_router: FeedbackRouter):
        self.feedback_router = feedback_router


# @lru_cache()
def get_commons():
    return Commons(
        feedback_router=FeedbackRouter(
            [EdgeGPTFeedbackProvider()],
            assignment_store=JSONFileAssignmentStore("assignments.json"),
        )
    )


app = FastAPI()
# cors:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
assignment_router = APIRouter(
    prefix="/assignments",
    tags=["assignments"],
)


@router.post("/feedback")
async def get_feedback(
    submission: Submission, commons: Annotated[Commons, Depends(get_commons)]
) -> list[Feedback]:
    """
    Get feedback for a given submission.

    Arguments:
        submission: The submission to get feedback for.

    Returns:
        A list of feedback objects.

    """
    asg_id = submission.assignment_id
    try:
        asg = commons.feedback_router._assignment_store[asg_id]
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Assignment {asg_id} not found."
        ) from None

    return await commons.feedback_router.get_feedback(submission, asg)


@assignment_router.get("/")
async def get_assignments(
    commons: Annotated[Commons, Depends(get_commons)]
) -> list[AssignmentID]:
    """
    Get a list of all assignment IDs.

    """
    return commons.feedback_router._assignment_store.get_assignment_ids()


@assignment_router.post("/new")
async def new_assignment(
    assignment: Assignment,
    commons: Annotated[Commons, Depends(get_commons)],
) -> AssignmentID:
    """
    Create a new assignment.

    """
    return commons.feedback_router._assignment_store.new_assignment(assignment)


app.include_router(router)
app.include_router(assignment_router)
