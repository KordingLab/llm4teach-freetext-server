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
            You are a helpful instructor, who knows that students need precise and terse feedback. Students are most motivated if you are engaging and remain positive, but it is more important to be honest and accurate than cheerful.
            {{~/system}}

            {{#user~}}
            The student has been given the following prompt by the instructor:

            ----
            {{prompt}}
            ----

            The secret, grader-only criteria for grading are:
            ----
            {{criteria}}
            ----

            Please give your OWN answer to the prompt:

            {{~/user}}

            {{#assistant~}}
            {{gen '_machine_answer'}}
            {{~/assistant}}

            {{#user~}}
            The complete student response is as follows:
            ----

            {{response}}

            ----

            Thinking about the differences between your answer and the student's, provide your feedback to the student as a bulleted list indicating both what the student got right and what they got wrong. Give details about what they are missing or misunderstood, and mention points they overlooked, if any.

            Do not instruct the student to review the criteria, as this is not provided to the student. Write to the student using "you" in the second person. The student will not see your answer to the prompt, so do not refer to it.

            Be particularly mindful of scientific rigor issues including confusing correlation with causation, biases, and logical fallacies. You must also correct factual errors using your extensive domain knowledge, even if the errors are subtle or minor.

            Do not say "Keep up the good work" or other encouragement "fluff." Write only the response to the student; do not write any other text.

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
                fact_check_caveat="You should also fact-check the student's response. If the student's response is factually incorrect, you should provide feedback on the incorrect statements.",
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


__all__ = [
    "OpenAICompletionBasedFeedbackProvider",
    "OpenAIChatBasedFeedbackProvider",
]
