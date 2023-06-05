import guidance

from ..config import OpenAIConfig
from ..feedback_providers.FeedbackProvider import FeedbackProvider
from ..llm4text_types import Assignment, Feedback, Submission


class OpenAIFeedbackProvider(FeedbackProvider):

    """
    A feedback provider that transacts with the OpenAI API for student
    responses. Uses Microsoft's `guidance` tool for feedback curation.
    """

    def __init__(self, config_override: OpenAIConfig | None = None):
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
