from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    CfnOutput
)
from constructs import Construct

from core import conf


class AdminUser(Construct):
    def __init__(self, scope: Construct, construct_id: str, user_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        # # Create group
        # group = iam.Group(self, "example-group", managed_policies=[
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ReadOnlyAccess")
        # ])

        # Create Managed Policy
        administrator_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            "AdministratorAccess"
        )

        # # Create Permissions Boundary
        # permissions_boundary = iam.ManagedPolicy(
        #     self,
        #     "example-permissions-boundary",
        #     statements=[
        #         iam.PolicyStatement(
        #             effect=iam.Effect.DENY,
        #             actions=["sqs:*"],
        #             resources=["*"]
        #         )
        #     ]
        # )

        # Create User
        user = iam.User(
            self,
            "User",
            user_name=user_name,
            managed_policies=[administrator_policy],
            # groups=[group],
            # permissions_boundary=permissions_boundary,
        )

        access_key = iam.CfnAccessKey(
            self,
            'UserAccessKey',
            user_name=user.user_name,
        )

        # access_key.node.add_dependency(user.node)
        # CfnOutput(
        #     self,
        #     'accessKeyId',
        #     value=access_key.ref
        # )
        # CfnOutput(
        #     self,
        #     'secretAccessKey',
        #     value=access_key.attr_secret_access_key
        # )
        ssm.StringParameter(
            self,
            conf.ADMIN_USER_ACCESS_KEY_ID_SSM,
            parameter_name=conf.ADMIN_USER_ACCESS_KEY_ID_SSM,
            string_value=access_key.ref
        )
        ssm.StringParameter(
            self,
            conf.ADMIN_USER_ACCESS_KEY_SECRET_SSM,
            parameter_name=conf.ADMIN_USER_ACCESS_KEY_SECRET_SSM,
            string_value=access_key.attr_secret_access_key
        )

        # # add a managed policy to the user
        # user.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
        # )

        # # create an inline policy
        # inline_policy = iam.Policy(
        #     self,
        #     "cloudwatch-logs-policy",
        #     statements=[
        #         iam.PolicyStatement(
        #             actions=["logs:PutLogEvents"],
        #             resources=["*"]
        #         )
        #     ])
        #
        # # attach the inline policy to the user
        # user.add_inline_policy(inline_policy)
