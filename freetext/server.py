from functools import lru_cache
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from .assignment_stores import (
    AssignmentStore,
    InMemoryAssignmentStore,
    # JSONFileAssignmentStore,
)
from .assignment_stores.DynamoAssignmentStore import DynamoAssignmentStore
from .config import ApplicationSettings
from .response_stores.ResponseStore import (
    ResponseStore,
    InMemoryResponseStore,
    # JSONFileResponseStore,
)
from .response_stores.DynamoResponseStore import DynamoResponseStore

from .feedback_providers.FeedbackProvider import FeedbackProvider
from .feedback_providers.OpenAIFeedbackProvider import (
    OpenAICompletionBasedFeedbackProvider,
    OpenAIChatBasedFeedbackProvider,
)
from .llm4text_types import (
    Assignment,
    AssignmentID,
    PublishableAssignment,
    Feedback,
    Submission,
)


class FeedbackRouter:
    """
    A router handles multiple feedback providers and returns aggregated
    feedback from all of them.

    """

    def __init__(
        self,
        feedback_providers: Optional[list[FeedbackProvider]] = None,
        assignment_store: Optional[AssignmentStore] = None,
        response_store: Optional[ResponseStore] = None,
        fallback_feedback_provider: Optional[FeedbackProvider] = None,
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
        self._response_store = (
            response_store if (response_store is not None) else InMemoryResponseStore()
        )
        self._fallback_feedback_provider = fallback_feedback_provider

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

        if len(all_feedback) == 0 and self._fallback_feedback_provider is not None:
            # if no feedback was returned, use the fallback provider
            all_feedback.extend(
                await self._fallback_feedback_provider.get_feedback(
                    submission, assignment
                )
            )

        self._response_store.save(assignment, submission, all_feedback)

        return all_feedback


class Commons:
    def __init__(self, feedback_router: FeedbackRouter):
        self.feedback_router = feedback_router


@lru_cache()
def get_commons():
    config = ApplicationSettings()
    return Commons(
        feedback_router=FeedbackRouter(
            [
                # OpenAICompletionBasedFeedbackProvider(),
                OpenAIChatBasedFeedbackProvider()
            ],
            assignment_store=DynamoAssignmentStore(
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                aws_region=config.aws_region,
                table_name=config.assignments_table,
            ),
            response_store=DynamoResponseStore(
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                aws_region=config.aws_region,
                table_name=config.responses_table,
            ),
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
        asg = commons.feedback_router._assignment_store.get_assignment(asg_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Assignment {asg_id} not found."
        ) from None

    return await commons.feedback_router.get_feedback(submission, asg)


# @assignment_router.get("/")
# async def get_assignments(
#     commons: Annotated[Commons, Depends(get_commons)]
# ) -> list[AssignmentID]:
#     """
#     Get a list of all assignment IDs.

#     """
#     return commons.feedback_router._assignment_store.get_assignment_ids()


@assignment_router.get("/{assignment_id}")
async def get_assignment(
    assignment_id: AssignmentID, commons: Annotated[Commons, Depends(get_commons)]
) -> PublishableAssignment:
    """
    Get a specific assignment.

    """
    try:
        asg = commons.feedback_router._assignment_store.get_assignment(assignment_id)
        return PublishableAssignment(
            student_prompt=asg.student_prompt,
        )

    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Assignment {assignment_id} not found."
        ) from None


@assignment_router.post("/new")
async def new_assignment(
    assignment: Assignment,
    commons: Annotated[Commons, Depends(get_commons)],
    assignment_creation_secret: str = Header(None),
) -> AssignmentID:
    """
    Create a new assignment.

    """
    if assignment_creation_secret != ApplicationSettings().assignment_creation_secret:
        raise HTTPException(status_code=401, detail="Invalid assignment creation.")

    return commons.feedback_router._assignment_store.new_assignment(assignment)


app.include_router(router)
app.include_router(assignment_router)


def serve():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9900, workers=4)


def serve_debug():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9900, workers=2, reload=True)


handler = Mangum(app, lifespan="off")
