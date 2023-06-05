from pydantic import BaseModel, Field

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
        description="The submission response text (i.e., from the student).",
    )
