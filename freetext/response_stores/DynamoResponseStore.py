import datetime
import uuid

import boto3

from freetext.response_stores import ResponseStore

from ..llm4text_types import Assignment, AssignmentID, Feedback, Submission


# class JSONFileResponseStore(ResponseStore):
#     def __init__(self, path: str | pathlib.Path):
#         self._path = pathlib.Path(path)

#     def save(
#         self,
#         assignment: Assignment,
#         submission: Submission,
#         all_feedback: list[Feedback],
#     ):
#         # Append a new JSONL line:
#         if not self._path.exists():
#             with open(self._path, "w") as f:
#                 f.write("")
#         with open(self._path, "a") as f:
#             f.write(
#                 json.dumps(
#                     {
#                         "assignment": assignment.dict(),
#                         "submission": submission.dict(),
#                         "all_feedback": [f.dict() for f in all_feedback],
#                         "timestamp": datetime.datetime.now().isoformat(),
#                     }
#                 )
#                 + "\n"
#             )


class DynamoResponseStore(ResponseStore):
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        table_name: str,
    ):
        self._table_name = table_name

        self._dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )

        # Create the table if it doesn't exist:
        try:
            self._dynamodb.create_table(  # type: ignore
                TableName=self._table_name,
                # Assignment ID can be used as a sort key to get all submissions for a given assignment
                KeySchema=[
                    {"AttributeName": "assignment_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "assignment_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                ],
                # On-demand pricing
                BillingMode="PAY_PER_REQUEST",
            )
        except self._dynamodb.meta.client.exceptions.ResourceInUseException:  # type: ignore
            # Table already exists
            pass

    def save(
        self,
        assignment: Assignment,
        submission: Submission,
        all_feedback: list[Feedback],
    ):
        table = self._dynamodb.Table(self._table_name)  # type: ignore
        response = table.put_item(
            Item={
                "assignment": assignment.dict(),
                "submission": submission.dict(),
                "all_feedback": [f.dict() for f in all_feedback],
                "timestamp": datetime.datetime.now().isoformat(),
                "assignment_id": str(uuid.uuid4()),
            }
        )
        return response
