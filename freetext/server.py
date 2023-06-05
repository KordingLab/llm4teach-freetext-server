from functools import lru_cache
import json
import os
from typing import Annotated
import uuid
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware

from freetext.AssignmentStore import (
    AssignmentStore,
    InMemoryAssignmentStore,
    JSONFileAssignmentStore,
)

from .llm4text_types import Submission, Assignment, Feedback, AssignmentID
from .feedback_provider import (
    FeedbackProvider,
    EdgeGPTFeedbackProvider,
    OpenAIFeedbackProvider,
)


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
        self._assignment_store = (
            assignment_store
            if (assignment_store is not None)
            else InMemoryAssignmentStore()
        )

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


@lru_cache()
def get_commons():
    return Commons(
        feedback_router=FeedbackRouter(
            # [EdgeGPTFeedbackProvider()],
            [OpenAIFeedbackProvider()],
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


def serve():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9900, workers=4)


def serve_debug():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9900, workers=2, reload=True)
