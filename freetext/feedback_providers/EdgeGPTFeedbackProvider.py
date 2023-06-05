# from freetext.feedback_providers.FeedbackProvider import FeedbackProvider
# from freetext.llm4text_types import Assignment, Feedback, Submission


# class EdgeGPTFeedbackProvider(FeedbackProvider):
#     def __init__(self):
#         ...

#     def _generate_prompt(self, submission: Submission, assignment: Assignment) -> str:
#         """ """
#         return f"""
#         You are reviewing a short-essay response to the following assignment.
#         {assignment.feedback_instructions}.
#         The entry must satisfy the following criteria:
#         {assignment.feedback_requirements}.
#         The entry is below:

#         ---
#         {submission.submission_string}
#         ---

#         Provide feedback to the author, citing specific criteria from the assignment if the author has not met them. Do NOT give feedback if the author has met all the criteria.

#         The response should contain nothing but a bulleted list. Do not include any other text, including your name or the author's name. Do not say 'hope this helps' or offer any other filler text. Do not say 'here is some feedback' or any other introductory text. Do not indicate when criteria were successfully met; only indicate when they were not met, and include one sentence of feedback for each, followed by a sentence explaining how to remedy the problem. Do not include any other text. Do not say 'I hope this helps!'.

#         For example, a complete example response might be:

#         '''
#         * The author did not explain the difference between a list and a tuple. Tuples are immutable, while lists are mutable.
#         * The author did not explain how 1.0 and 1 are interpreted differently. 1.0 is a float, while 1 is an int.
#         '''

#         """

#     async def get_feedback(
#         self, submission: Submission, assignment: Assignment
#     ) -> list[Feedback]:
#         """ """
#         feedback = []
#         bot = await Chatbot.create(cookie_path="freetext/cookies.json")  # type: ignore
#         res = await bot.ask(
#             prompt=self._generate_prompt(submission, assignment),
#             conversation_style=ConversationStyle.precise,
#             wss_link="wss://sydney.bing.com/sydney/ChatHub",
#         )

#         await bot.close()
#         return [
#             Feedback(
#                 feedback_string=res["item"]["messages"][1]["text"],
#                 source="EdgeGPTFeedbackProvider",
#                 location=(0, len(submission.submission_string)),
#             )
#         ]
