from functools import lru_cache
from typing import Protocol, Annotated
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from EdgeGPT import Chatbot, ConversationStyle


class Assignment(BaseModel):
    """
    A base schema for an Assignment, to which many Submissions can be made.

    The assignment contains both public information (student_prompt) as well
    as private information (grading_requirements, grading_instructions) that
    are not shared with students but will be used by the LLM grader.

    """

    student_prompt: str = Field(
        ...,
        title="Student Prompt",
        description="The prompt that will be shown to students.",
    )
    feedback_requirements: list[str] = Field(
        ...,
        title="Feedback Requirements",
        description="A list of criteria for the grader to use.",
    )
    feedback_instructions: str = Field(
        ...,
        title="Feedback Instructions",
        description="Instructions for the grader on how to provide feedback for this assignment.",
    )


class Feedback(BaseModel):
    """
    A base schema for Feedback, which is a response to a Submission.

    """

    feedback_string: str = Field(
        ...,
        title="Feedback String",
        description="The feedback response text.",
    )
    source: str = Field(
        ...,
        title="Source",
        description="The source of the feedback, e.g. the grader's name or LLM provenance.",
    )
    # Optional
    location: tuple[int, int] = Field(
        None,
        title="Location",
        description="The location of the feedback in the submission, as (start, stop) character indices.",
    )


class Submission(BaseModel):
    """
    A base schema for a Submission, which is a response to an Assignment.

    """

    assignment_id: str = Field(
        ...,
        title="Assignment ID",
        description="The ID of the assignment that this submission is for.",
    )

    submission_string: str = Field(
        ...,
        title="Submission String",
        description="The submission response text.",
    )


class FeedbackProvider(Protocol):
    """
    A base class for a feedback provider, which is a class that can provide
    feedback for a given assignment and submission.

    """

    async def get_feedback(
        self, submission: Submission, assignment: Assignment
    ) -> list[Feedback]:
        """
        Returns the feedback for a given submission.

        """

        raise NotImplementedError()


class DummyFeedbackProvider(FeedbackProvider):
    """
    A dummy feedback provider that returns a single feedback object.

    """

    def __init__(self, always_respond: str):
        self._always_respond = always_respond

    async def get_feedback(
        self, submission: Submission, assignment: Assignment
    ) -> list[Feedback]:
        """
        Returns the feedback for a given submission.

        """

        return [
            Feedback(
                feedback_string=self._always_respond,
                source="Dummy Feedback Provider",
                location=(0, len(submission.submission_string)),
            )
        ]


class UnderTenWordFinder(FeedbackProvider):
    """
    Finds standalone digits under ten and suggests you write them out.

    """

    async def get_feedback(
        self, submission: Submission, assignment: Assignment
    ) -> list[Feedback]:
        """
        Returns the feedback for a given submission.

        """
        feedback = []
        # Location is provided in (start, stop) character indices,
        # which makes it a little harder to detect words...
        import re

        for match in re.finditer(r"\b(\d)\b", submission.submission_string):
            # check if the match is a single digit
            if len(match.group(1)) == 1:
                # check if the digit is less than 10
                if int(match.group(1)) < 10:
                    # add feedback
                    feedback.append(
                        Feedback(
                            feedback_string=f"Write out {match.group(1)}",
                            source="UnderTenWordFinder",
                            location=match.span(),
                        )
                    )
        return feedback


class EdgeGPTFeedbackProvider(FeedbackProvider):
    def __init__(self):
        ...

    def _generate_prompt(self, submission: Submission, assignment: Assignment) -> str:
        """ """
        return f"""
        The following is a peer review process.
        {assignment.feedback_instructions}.
        The entry must satisfy the following criteria:
        {assignment.feedback_requirements}.
        The entry is below:

        ---
        {submission.submission_string}
        ---

        Provide feedback to the author, citing specific criteria from the assignment if the author has not met them. Do NOT give feedback if the author has met all the criteria.

        The response should contain nothing but a bulleted list. Do not include any other text, including your name or the author's name. Do not say 'hope this helps' or offer any other filler text. Do not say 'here is some feedback' or any other introductory text. Do not indicate when criteria were successfully met; only indicate when they were not met, and include one sentence of feedback for each, followed by a sentence explaining how to remedy the problem. Do not include any other text. Do not say 'I hope this helps!'.

        For example, a complete example response might be:

        '''
        * The author did not explain the difference between a list and a tuple. Tuples are immutable, while lists are mutable.
        * The author did not explain how 1.0 and 1 are interpreted differently. 1.0 is a float, while 1 is an int.
        '''

        """

    async def get_feedback(
        self, submission: Submission, assignment: Assignment
    ) -> list[Feedback]:
        """ """
        feedback = []
        bot = await Chatbot.create(cookie_path="freetext/cookies.json")
        res = await bot.ask(
            prompt=self._generate_prompt(submission, assignment),
            conversation_style=ConversationStyle.precise,
            wss_link="wss://sydney.bing.com/sydney/ChatHub",
        )

        await bot.close()
        return [
            Feedback(
                feedback_string=res["item"]["messages"][1]["text"],
                source="EdgeGPTFeedbackProvider",
                location=(0, len(submission.submission_string)),
            )
        ]


class FeedbackRouter:
    """
    A router handles multiple feedback providers and returns aggregated
    feedback from all of them.

    """

    def __init__(self, feedback_providers: list[FeedbackProvider] | None = None):
        """
        Create a new feedback router, with an optional list of providers.
        """
        self._feedback_providers = feedback_providers or []

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
            [
                DummyFeedbackProvider("This is a dummy feedback provider."),
                UnderTenWordFinder(),
                EdgeGPTFeedbackProvider(),
            ]
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
    default_assignment = Assignment(
        student_prompt="",
        feedback_instructions="Determine if the author has met the following criteria for explaining what a neuron is.",
        feedback_requirements=[
            "Must include the terms 'synapse' and 'action potential'.",
            "Must mention the role of neurotransmitters.",
        ],
    )
    return await commons.feedback_router.get_feedback(submission, default_assignment)


app.include_router(router)
