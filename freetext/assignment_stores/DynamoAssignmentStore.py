import uuid

import boto3

from ..assignment_stores.AssignmentStore import AssignmentStore
from ..llm4text_types import Assignment, AssignmentID


class DynamoAssignmentStore(AssignmentStore):
    """
    An AssignmentStore that stores assignments in a DynamoDB table on AWS.

    Note that several methods have NOT been implemented here because they are
    not critical for the project and can incur significant costs if used on
    very large tables (usually because they involve a `scan` operation.)

    """

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
                KeySchema=[
                    {"AttributeName": "assignment_id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "assignment_id", "AttributeType": "S"},
                ],
                # On-demand pricing
                BillingMode="PAY_PER_REQUEST",
            )
        except self._dynamodb.meta.client.exceptions.ResourceInUseException:  # type: ignore
            # Table already exists
            pass

    def get_assignment(self, key: AssignmentID) -> Assignment:
        """
        Returns the assignment with the given ID.

        Arguments:
            key: The ID of the assignment to get.

        Returns:
            The assignment with the given ID, or throw an IndexError if it doesn't exist.

        """
        table = self._dynamodb.Table(self._table_name)  # type: ignore
        # assignment_id is the primary key, so we can get the item directly
        response = table.get_item(Key={"assignment_id": key})
        if "Item" not in response:
            raise IndexError(f"Assignment with ID {key} does not exist.")
        return Assignment.parse_obj(response["Item"])

    def set_assignment(self, key: AssignmentID, value: Assignment) -> None:
        """
        Sets the assignment with the given ID.

        If the assignment already exists, it will be overwritten. Otherwise, it
        will be created.

        Arguments:
            key: The ID of the assignment to set.
            value: The assignment to set.

        """
        table = self._dynamodb.Table(self._table_name)  # type: ignore
        response = table.put_item(Item=dict(**value.dict(), assignment_id=key))
        #  Check response for errors
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise Exception(f"Error setting assignment: {response}")

    def __delitem__(self, key: AssignmentID) -> None:
        raise NotImplementedError()

    def get_assignment_ids(self) -> list[AssignmentID]:
        """
        Returns a list of all assignment IDs in the store.
        """
        # We raise because this could be a very expensive operation (scan)
        raise NotImplementedError()

    def new_assignment(self, assignment: Assignment) -> AssignmentID:
        """
        Adds a new assignment to the store.

        Arguments:
            assignment: The assignment to add.

        Returns:
            The ID of the new assignment.

        """
        # Generate a new assignment ID
        assignment_id = AssignmentID(str(uuid.uuid4()))
        self.set_assignment(assignment_id, assignment)
        return assignment_id

    def __contains__(self, key: AssignmentID) -> bool:
        """
        Returns whether the given assignment ID is in the AssignmentStore.

        """
        table = self._dynamodb.Table(self._table_name)  # type: ignore
        response = table.get_item(Key={"assignment_id": key})
        return "Item" in response
