import json
from functools import lru_cache
import os
from typing import Protocol, Annotated
import uuid
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from EdgeGPT import Chatbot, ConversationStyle

AssignmentID = str


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
            [
                UnderTenWordFinder(),
                EdgeGPTFeedbackProvider(),
            ],
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
