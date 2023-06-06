from typing import Optional
import guidance

from ..config import OpenAIConfig
from ..feedback_providers.FeedbackProvider import FeedbackProvider
from ..llm4text_types import Assignment, Feedback, Submission


class OpenAICompletionBasedFeedbackProvider(FeedbackProvider):

    """
    A feedback provider that transacts with the OpenAI API for student
    responses. Uses Microsoft's `guidance` tool for feedback curation.
    """

    def __init__(self, config_override: Optional[OpenAIConfig] = None):
        if config_override is not None:
            self.config = config_override
        else:
            self.config = OpenAIConfig()

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
            openai_kwargs = self.config.dict()
            guidance.llm = guidance.llms.OpenAI("text-davinci-003", **openai_kwargs)

            # https://github.com/microsoft/guidance/discussions/108
            grader = guidance.Program(
                """
            You are a helpful and terse TA.
            The student has been given the following prompt:

            ---
            {{prompt}}
            ---

            The secret, grader-only criteria for grading are as follows:

            ---
            {{criteria}}
            ---

            The student response is as follows:
            ---

            {{response}}

            ---

            Provide your feedback as a list of JSON objects, each including the following fields:
            * feedback (str): The comment to give to the student.
            * location (tuple[int, int]): The start and end character indices of the text to which the feedback applies.

            Be as precise and specific as possible, referencing the shortest possible spans while still including all the problem text.
            You do not need to cover all of the problem text with locations.

            Do not instruct the student to review the criteria, as this is not provided to the student.

            {{audience_caveat}}

            {{fact_check_caveat}}


            When you're done, write "// Done" on the last line.

            # Feedback

            {{#geneach 'items' stop='// Done'}}
            {
                "feedback": "{{gen 'this.feedback'}}",
                "location": [{{gen 'this.start' stop=','}}, {{gen 'this.stop' stop=']'}}],
            }
            {{/geneach}}
            """
            )

            response = submission.submission_string
            feedback = grader(
                response=response,
                prompt=assignment.student_prompt,
                criteria="\n".join(
                    [f"     * {f}" for f in assignment.feedback_requirements]
                ),
                audience_caveat="",  # You should provide feedback keeping in mind that the student is a Graduate Student and should be graded accordingly.
                fact_check_caveat="",  # You should also fact-check the student's response. If the student's response is factually incorrect, you should provide feedback on the incorrect statements.
            )

            return [
                Feedback(
                    feedback_string=f["feedback"],
                    source="OpenAIFeedbackProvider",
                    location=(f["start"], f["stop"]),
                )
                for f in feedback["items"]
            ]
        except Exception as e:
            print(e)
            return []


class OpenAIChatBasedFeedbackProvider(FeedbackProvider):

    """
    A feedback provider that transacts with the OpenAI API for student
    responses. Uses Microsoft's `guidance` tool for feedback curation. This
    version, unline OpenAICompletionBasedFeedbackProvider, uses the chat API
    instead of the completion API, which gives more conversational feedback and
    more cost-effective API use, at the cost of a more constrained prompt.
    """

    def __init__(self, config_override: Optional[OpenAIConfig] = None):
        if config_override is not None:
            self.config = config_override
        else:
            self.config = OpenAIConfig()

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
            openai_kwargs = self.config.dict()
            guidance.llm = guidance.llms.OpenAI("gpt-3.5-turbo", **openai_kwargs)

            grader = guidance.Program(
                """
            {{#system~}}
            You are a helpful and terse TA.
            {{~/system}}

            {{#user~}}
            The student has been given the following prompt:

            ---
            {{prompt}}
            ---

            The secret, grader-only criteria for grading are as follows:

            ---
            {{criteria}}
            ---

            The student response is as follows:
            ---

            {{response}}

            ---

            Provide your feedback as a bulleted list.

            Do not instruct the student to review the criteria, as this is not provided to the student.

            {{audience_caveat}}

            {{fact_check_caveat}}

            {{~/user}}

            {{#assistant~}}
            {{gen 'feedback'}}
            {{~/assistant}}
            """
            )

            response = submission.submission_string
            feedback = grader(
                response=response,
                prompt=assignment.student_prompt,
                criteria="\n".join(
                    [f"     * {f}" for f in assignment.feedback_requirements]
                ),
                audience_caveat="",  # You should provide feedback keeping in mind that the student is a Graduate Student and should be graded accordingly.
                fact_check_caveat="",  # You should also fact-check the student's response. If the student's response is factually incorrect, you should provide feedback on the incorrect statements.",
            )

            return [
                Feedback(
                    feedback_string=feedback["feedback"],
                    source="OpenAIFeedbackProvider",
                    location=(0, len(submission.submission_string)),
                )
            ]
        except Exception as e:
            print(e)
            return []


__all__ = [
    "OpenAICompletionBasedFeedbackProvider",
    "OpenAIChatBasedFeedbackProvider",
]
