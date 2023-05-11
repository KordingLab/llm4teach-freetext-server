from typing import Protocol
from EdgeGPT import Chatbot, ConversationStyle

from freetext.types import Assignment, Feedback, Submission


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
