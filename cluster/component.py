from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_ssm as ssm,
    lambda_layer_kubectl_v25 as lambda_layer_kubectl_v25,
    aws_iam as iam, CfnOutput, )
from cdk_ec2_key_pair import KeyPair
from constructs import Construct

from core import conf


class ClusterStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # provision a cluster
        cluster = eks.Cluster(
            self,
            conf.CLUSTER_EKS_NAME,
            cluster_name=conf.CLUSTER_EKS_NAME,
            version=eks.KubernetesVersion.V1_25,
            kubectl_layer=lambda_layer_kubectl_v25.KubectlV25Layer(self, "kubectl"),
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            default_capacity=0,  # will customize it using an ASG
            alb_controller=eks.AlbControllerOptions(
                version=eks.AlbControllerVersion.V2_4_1,
            ),
            cluster_logging=[
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR,
                eks.ClusterLoggingTypes.CONTROLLER_MANAGER,
                eks.ClusterLoggingTypes.SCHEDULER,
            ],
        )

        # add asg capacity for worker nodes
        key_pair = KeyPair(
            self,
            conf.CLUSTER_SSH_KEY_NAME,
            name=conf.CLUSTER_SSH_KEY_NAME,
            resource_prefix=conf.CLUSTER_SSH_KEY_NAME,
        )
        cluster.add_auto_scaling_group_capacity(
            conf.CLUSTER_ASG_NAME,
            auto_scaling_group_name=conf.CLUSTER_ASG_NAME,
            instance_type=ec2.InstanceType("t3.medium"),
            machine_image_type=eks.MachineImageType.AMAZON_LINUX_2,  # or BOTTLEROCKET
            min_capacity=1,
            desired_capacity=1,
            max_capacity=3,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            key_name=key_pair.key_pair_name,
        )

        # add a sample manifest to the cluster
        app_name = "my-app-001"
        app_label = {
            "app": app_name
        }
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": app_name},
            "spec": {
                "replicas": 2,
                "selector": {
                    "matchLabels": app_label
                },
                "template": {
                    "metadata": {
                        "labels": app_label
                    },
                    "spec": {
                        "containers": [{
                            "name": app_name,
                            "image": "paulbouwer/hello-kubernetes:1.5",
                            "ports": [{"containerPort": 8080}]
                        }]
                    }
                }
            }
        }
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": app_name},
            "spec": {
                "type": "LoadBalancer",
                "ports": [{"port": 80, "targetPort": 8080}],
                "selector": app_label
            }
        }
        manifest = cluster.add_manifest("hello-kub", service, deployment)
        if cluster.alb_controller:
            # important to avoid dangling resources
            manifest.node.add_dependency(cluster.alb_controller)

        # add service account for fluent-bit
        service_account: eks.ServiceAccount = cluster.add_service_account(
            id="fluent-bit",
            name="fluent-bit",
        )
        service_account.add_to_principal_policy(iam.PolicyStatement(
            actions=["es:ESHttp*"],
            resources=["*"],  # TODO point to the ES cluster arn
            effect=iam.Effect.ALLOW
        ))
        CfnOutput(
            self,
            "ServiceAccountIamRole",
            value=service_account.role.role_arn,
        )
        ssm.StringParameter(
            self,
            conf.CLUSTER_FLUENT_BIT_SERVICE_ACCOUNT_ROLE_ARN_SSM,
            parameter_name=conf.CLUSTER_FLUENT_BIT_SERVICE_ACCOUNT_ROLE_ARN_SSM,
            string_value=service_account.role.role_arn,
        )

        # add service account and add-on for EBS CSI
        # https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html
        # https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html
        ebs_csi_service_account: eks.ServiceAccount = cluster.add_service_account(
            id="ebs-csi",
            name="ebs-csi",
            namespace="kube-system",  # Important!
        )
        ebs_csi_service_account.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEBSCSIDriverPolicy")
        )
        eks.CfnAddon(
            self,
            'aws-ebs-csi-driver',
            addon_name='aws-ebs-csi-driver',
            cluster_name=cluster.cluster_name,
            preserve_on_delete=False,
            service_account_role_arn=ebs_csi_service_account.role.role_arn,
        )
