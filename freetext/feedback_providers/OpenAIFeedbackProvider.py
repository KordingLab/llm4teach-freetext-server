from typing import List, Optional
import guidance

from ..config import OpenAIConfig
from ..feedback_providers.FeedbackProvider import FeedbackProvider
from ..prompt_stores import PromptStore
from ..llm4text_types import Assignment, Feedback, Submission


class OpenAIChatBasedFeedbackProvider(FeedbackProvider):

    """
    A feedback provider that transacts with the OpenAI API for student
    responses. Uses Microsoft's `guidance` tool for feedback curation. This
    version, unline OpenAICompletionBasedFeedbackProvider, uses the chat API
    instead of the completion API, which gives more conversational feedback and
    more cost-effective API use, at the cost of a more constrained prompt.
    """

    def __init__(
        self, prompt_store: PromptStore, config_override: Optional[OpenAIConfig] = None
    ):
        self.prompts = prompt_store
        if config_override is not None:
            self.config = config_override
        else:
            self.config = OpenAIConfig()
        guidance.llm = guidance.llms.OpenAI(**self.config.dict())

    async def get_feedback(
        self, submission: Submission, assignment: Assignment
    ) -> list[Feedback]:
        """
        Returns the feedback.
        Arguments:
            submission: The submission to provide feedback for.
            assignment: The assignment to provide feedback for.
        Returns:
            A list of feedback objects.
        """

        # set the default language model used to execute guidance programs
        try:
            grader = guidance.Program(self.prompts.get_prompt("grader.feedback"))

            response = submission.submission_string
            feedback = grader(
                response=response,
                prompt=assignment.student_prompt,
                criteria="\n".join(
                    [f"     * {f}" for f in assignment.feedback_requirements]
                ),
            )

            return [
                Feedback(
                    feedback_string="\n" + feedback["feedback"],
                    source="OpenAIFeedbackProvider",
                    location=(0, len(submission.submission_string)),
                )
            ]
        except Exception as e:
            print(e)
            return []

    async def suggest_criteria(self, assignment: Assignment) -> List[str]:
        """
        Uses the OpenAI ChatGPT 3.5 Turbo model to suggest grading criteria
        for a question. If criteria are already provided, they may be edited
        or modified by this function.

        Arguments:
            assignment (Assignment): The assignment to suggest criteria for.

        Returns:
            List[str]: A list of criteria.

        """
        try:
            grader = guidance.Program(self.prompts.get_prompt("grader.draft_criteria"))

            response = assignment.student_prompt
            criteria = grader(
                response=response,
                prompt=assignment.student_prompt,
                criteria="\n".join(
                    [f"     * {f}" for f in assignment.feedback_requirements]
                ),
                audience_caveat="",
            )

            return criteria["criteria"].split("\n")
        except Exception as e:
            print(e)
            return []

    async def suggest_question(self, assignment: Assignment) -> str:
        """
        Generate a suggestion for a student-facing question, given a current
        question and a set of criteria.

        The current implementation is a bit heavy, and may be unadvised for
        high-throughput applications as it requires several responses from a
        LLM to arrive at an improved question.

        The current approach is the following:
        * Take a question "draft" and have the machine answer it.
        * Grade that response with the current criteria.
        * Identify what properties (if any) SHOULD have been more clear in the
            question text.
        * Generate a new question that includes those properties.

        """
        try:
            draft_response = guidance.Program(
                self.prompts.get_prompt("grader.draft_response")
            )
            criteria = draft_response(prompt=assignment.student_prompt)

            feedback = await self.get_feedback(
                Submission(
                    submission_string=criteria["_machine_answer"],
                    assignment_id="_DRAFT_",
                ),
                assignment,
            )

            question_improver = guidance.Program(
                self.prompts.get_prompt("grader.improve_question")
            )

            improved_question = question_improver(
                prompt=assignment.student_prompt,
                feedback="\n".join([f.feedback_string for f in feedback]),
            )

            return improved_question["improved_question"].lstrip('"').rstrip('"')
        except Exception as e:
            print(e)
            return assignment.student_prompt


__all__ = [
    "OpenAIChatBasedFeedbackProvider",
]
