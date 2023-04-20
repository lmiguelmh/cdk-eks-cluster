from typing import Optional

from aws_cdk import (
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_iam as iam,
)
from cdk_ec2_key_pair import KeyPair
from constructs import Construct


class Bastion(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            instance_name: str,
            instance_type: str,
            vpc: ec2.IVpc,
            user_data: ec2.UserData,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id)

        self._instance_role = iam.Role(
            self,
            "InstanceRole",
            role_name=f"{construct_id}-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        # add permissions for SSM Agent
        self._instance_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )

        self._instance_security_group = ec2.SecurityGroup(
            self,
            "InstanceSecurityGroup",
            security_group_name=f"{construct_id}-security-group",
            vpc=vpc,
            allow_all_outbound=True,
            description="Bastion instance security group",
        )
        self._instance_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "Allows SSH access from any IP"
        )

        self._instance_key_pair = KeyPair(
            self,
            "InstanceKeyPair",
            name=f"{construct_id}-key-pair",
            resource_prefix=f"{construct_id}",
            store_public_key=True,
        )

        self._instance = ec2.Instance(
            self,
            "Instance",
            instance_name=instance_name,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            role=self._instance_role,
            security_group=self._instance_security_group,
            key_name=self._instance_key_pair.key_pair_name,
            instance_type=ec2.InstanceType(instance_type),
            # Amazon Linux
            # machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            # Ubuntu LTS
            machine_image=ec2.MachineImage.from_ssm_parameter(
                parameter_name="/aws/service/canonical/ubuntu/server/focal/stable/current/amd64/hvm/ebs-gp2/ami-id",
                os=ec2.OperatingSystemType.LINUX,
            ),
            user_data=user_data,
        )

        @property
        def instance_role(self):
            return self._instance_role

        @property
        def instance_security_group(self):
            return self._instance_security_group

        @property
        def instance_key_pair(self):
            return self._instance_key_pair

        @property
        def instance(self):
            return self._instance
