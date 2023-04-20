from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_cloud9 as cloud9,
    aws_ec2 as ec2,
    CfnOutput
)
from constructs import Construct

from core import conf


class VPC(Construct):
    def __init__(self, scope: Construct, construct_id: str, vpc_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._vpc = ec2.Vpc(
            self,
            "VPC",
            vpc_name=vpc_name,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                ),
            ],
            max_azs=2,
        )

    @property
    def vpc(self) -> ec2.Vpc:
        return self._vpc
