from typing import Protocol
from EdgeGPT import Chatbot, ConversationStyle
import guidance

from .config import OpenAIConfig
from .llm4text_types import Assignment, Feedback, Submission


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
        You are reviewing a short-essay response to the following assignment.
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

        The criteria for grading are as follows:

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

        Be as precise and specific as possible, referencing the shortest possible spans while still including all the problem text. You do not need to cover all of the problem text with locations.

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


class FallbackFeedbackProvider(FeedbackProvider):
    """
    A feedback provider that uses a fallback feedback provider if the
    primary feedback provider fails.

    """

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
        return (
            [
                Feedback(
                    feedback_string=assignment.fallback_response,
                    source="FallbackFeedbackProvider",
                    location=(0, len(submission.submission_string)),
                )
            ]
            if assignment.fallback_response is not None
            else []
        )
