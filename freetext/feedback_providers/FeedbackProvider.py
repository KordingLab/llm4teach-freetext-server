from typing import List, Protocol

from ..llm4text_types import Assignment, Feedback, Submission


class FeedbackProvider(Protocol):
    """
    A base class for a feedback provider, which is a class that can provide
    feedback for a given assignment and submission.

    """

    async def get_feedback(
        self, submission: Submission, assignment: Assignment
    ) -> List[Feedback]:
        """
        Returns the feedback for a given submission.

        """

        raise NotImplementedError()

    async def suggest_criteria(self, assignment: Assignment) -> List[str]:
        """
        Suggest an improvement to the set of criteria for a given assignment.
        """
        raise NotImplementedError()

    async def suggest_question(self, Assignment) -> str:
        """
        Suggest an improvement to the question for a given assignment.
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
