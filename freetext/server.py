from functools import lru_cache
import pathlib
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from mangum import Mangum

from freetext.assignment_stores import AssignmentStore, create_assignment_store
from freetext.response_stores import ResponseStore, create_response_store
from freetext.prompt_stores import PromptStore, create_prompt_store
from .config import ApplicationSettings
from .feedback_providers.FeedbackProvider import FeedbackProvider
from .feedback_providers.OpenAIFeedbackProvider import OpenAIChatBasedFeedbackProvider
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
        assignment_store: AssignmentStore,
        response_store: ResponseStore,
        feedback_providers: Optional[list[FeedbackProvider]] = None,
        fallback_feedback_provider: Optional[FeedbackProvider] = None,
    ):
        """
        Create a new feedback router, with an optional list of providers and
        assignment store.

        Arguments:
            feedback_providers: A list of feedback providers to use.
            assignment_store: An assignment store to use.

        """
        self._assignment_store = assignment_store
        self._response_store = response_store
        self._feedback_providers = feedback_providers or []
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
            assignment_store=create_assignment_store(config.assignment_store),
            response_store=create_response_store(config.response_store),
            feedback_providers=[
                OpenAIChatBasedFeedbackProvider(
                    create_prompt_store(config.prompt_store)
                )
            ],
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
app_router = APIRouter(
    prefix="/app",
    tags=["app"],
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


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    data = """User-agent: *\nDisallow: /"""
    return data


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


# AssignmentReviewRequest definition:
class AssignmentCriteriaReviewRequest(Assignment):
    ...


class AssignmentCriteriaReviewResponse(Assignment):
    suggested_criteria: List[str]


class AssignmentQuestionReviewRequest(Assignment):
    ...


class AssignmentQuestionReviewResponse(Assignment):
    suggested_question: str


@assignment_router.post("/suggest/criteria")
async def review_criteria(
    assignment_review_request: AssignmentCriteriaReviewRequest,
    commons: Annotated[Commons, Depends(get_commons)],
    assignment_creation_secret: str = Header(None),
) -> AssignmentCriteriaReviewResponse:
    """
    Review an assignment, providing instructor-facing guidance on criteria.

    """
    if assignment_creation_secret != ApplicationSettings().assignment_creation_secret:
        raise HTTPException(status_code=401, detail="Invalid token.")

    # TODO: Should delegate to first feedback provider that supports review.
    new_crits = await commons.feedback_router._feedback_providers[0].suggest_criteria(
        assignment_review_request
    )
    response = AssignmentCriteriaReviewResponse(
        **assignment_review_request.dict(), suggested_criteria=new_crits
    )
    return response


@assignment_router.post("/suggest/question")
async def review_question(
    assignment_review_request: AssignmentQuestionReviewRequest,
    commons: Annotated[Commons, Depends(get_commons)],
    assignment_creation_secret: str = Header(None),
) -> AssignmentQuestionReviewResponse:
    """
    Review an assignment, providing instructor-facing guidance on question.

    """
    if assignment_creation_secret != ApplicationSettings().assignment_creation_secret:
        raise HTTPException(status_code=401, detail="Invalid token.")

    # TODO: Should delegate to first feedback provider that supports review.
    new_question = await commons.feedback_router._feedback_providers[
        0
    ].suggest_question(assignment_review_request)
    response = AssignmentQuestionReviewResponse(
        **assignment_review_request.dict(), suggested_question=new_question
    )
    return response


@app_router.get("/")
async def app_get():
    templates = pathlib.Path(__file__).parent / "templates"
    return HTMLResponse(open(templates / "simple.html").read())


@router.get("/")
async def root_get():
    templates = pathlib.Path(__file__).parent / "templates"
    return HTMLResponse(open(templates / "paper.html").read())


@router.get("/paper")
async def paper_get():
    templates = pathlib.Path(__file__).parent / "templates"
    return HTMLResponse(open(templates / "paper.html").read())


@app_router.get("/assignments/{assignment_id}")
async def app_get_assignment(
    assignment_id: AssignmentID, commons: Annotated[Commons, Depends(get_commons)]
):
    template = pathlib.Path(__file__).parent / "templates" / "assignment.html"
    try:
        asg = commons.feedback_router._assignment_store.get_assignment(assignment_id)
        janky_template = {
            "<%= assignment_id %>": assignment_id,
            "<%= student_prompt %>": asg.student_prompt,
        }
        html = open(template).read()
        for k, v in janky_template.items():
            html = html.replace(k, v)

        return HTMLResponse(html)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Assignment {assignment_id} not found."
        ) from None


app.include_router(router)
app.include_router(assignment_router)
app.include_router(app_router)


def serve():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9900, workers=4)


def serve_debug():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9900, workers=2, reload=True)


handler = Mangum(app, lifespan="off")
