from typing import Optional

from aws_cdk import (
    aws_cognito as cognito
)
from aws_cdk.aws_cognito import CfnUserPoolUserToGroupAttachment
from aws_cdk.custom_resources import AwsCustomResource, PhysicalResourceId, AwsCustomResourcePolicy
from constructs import Construct


class CognitoUser(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            username: str,
            password: str,
            user_pool: cognito.CfnUserPool,
            group_name: Optional[str] = None,
    ):
        super().__init__(scope, id)

        user_pool_id = user_pool.ref

        # Create the user inside the Cognito user pool using Lambda backed AWS Custom resource
        admin_create_user = AwsCustomResource(
            self,
            "AwsCustomResource-CreateUser",
            on_create={
                "service": "CognitoIdentityServiceProvider",
                "action": "adminCreateUser",
                "parameters": {
                    "UserPoolId": user_pool_id,
                    "Username": username,
                    "MessageAction": "SUPPRESS",
                    "TemporaryPassword": password,
                },
                "physical_resource_id": PhysicalResourceId.of(f"AwsCustomResource-CreateUser-{username}"),
            },
            on_delete={
                "service": "CognitoIdentityServiceProvider",
                "action": "adminDeleteUser",
                "parameters": {
                    "UserPoolId": user_pool_id,
                    "Username": username,
                },
            },
            policy=AwsCustomResourcePolicy.from_sdk_calls(resources=AwsCustomResourcePolicy.ANY_RESOURCE),
            install_latest_aws_sdk=True,
        )

        # Force the password for the user, because by default when new users are created
        # they are in FORCE_PASSWORD_CHANGE status. The newly created user has no way to change it though
        admin_set_user_password = AwsCustomResource(
            self,
            "AwsCustomResource-ForcePassword",
            on_create={
                "service": "CognitoIdentityServiceProvider",
                "action": "adminSetUserPassword",
                "parameters": {
                    "UserPoolId": user_pool_id,
                    "Username": username,
                    "Password": password,
                    "Permanent": True,
                },
                "physical_resource_id": PhysicalResourceId.of(f"AwsCustomResource-ForcePassword-{username}"),
            },
            policy=AwsCustomResourcePolicy.from_sdk_calls(resources=AwsCustomResourcePolicy.ANY_RESOURCE),
            install_latest_aws_sdk=True,
        )
        admin_set_user_password.node.add_dependency(admin_create_user)

        # If a Group Name is provided, also add the user to this Cognito UserPool Group
        if group_name:
            user_to_group_attachment = CfnUserPoolUserToGroupAttachment(
                self,
                "AttachUserToGroup",
                user_pool_id=user_pool_id,
                group_name=group_name,
                username=username,
            )
            user_to_group_attachment.node.add_dependency(admin_create_user)
            user_to_group_attachment.node.add_dependency(admin_set_user_password)
            user_to_group_attachment.node.add_dependency(user_pool)
