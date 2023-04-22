from pathlib import Path

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam, CfnOutput,
)
from constructs import Construct

from core import conf
from core.constructs.admin_user import AdminUser
from core.constructs.bastion import Bastion
from core.constructs.vpc import VPC


class ClusterStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # provisiong a cluster
        cluster = eks.Cluster(
            self,
            conf.CLUSTER_EKS_NAME,
            cluster_name=conf.CLUSTER_EKS_NAME,
            version=eks.KubernetesVersion.V1_25,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,  # PUBLIC_AND_PRIVATE by default, doesn't seem secure, PRIVATE
            default_capacity=2,
            default_capacity_instance=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
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
            # vpc=vpc,
            # vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)]
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
        cluster.add_manifest("hello-kub", service, deployment)

        # # apply a kubernetes manifest to the cluster
        # cluster.add_manifest(
        #     "SamplePod",
        #     {
        #         "apiVersion": "v1",
        #         "kind": "Pod",
        #         "metadata": {"name": "samplepod"},
        #         "spec": {
        #             "containers": [{
        #                 "name": "hello",
        #                 "image": "paulbouwer/hello-kubernetes:1.5",
        #                 "ports": [{"container_port": 8080}]
        #             }],
        #         }
        #     },
        # )

        # # another manifest
        # namespace = cluster.add_manifest("my-namespace", {
        #     "api_version": "v1",
        #     "kind": "Namespace",
        #     "metadata": {"name": "my-app"}
        # })
        #
        # service = cluster.add_manifest("my-service", {
        #     "metadata": {
        #         "name": "myservice",
        #         "namespace": "my-app"
        #     },
        #     "spec": {}
        # })
        #
        # service.node.add_dependency(namespace)

        # # yet another manifest
        # # cluster: eks.Cluster
        #
        # app_label = {"app": "hello-kubernetes"}
        #
        # deployment = {
        #     "api_version": "apps/v1",
        #     "kind": "Deployment",
        #     "metadata": {"name": "hello-kubernetes"},
        #     "spec": {
        #         "replicas": 3,
        #         "selector": {"match_labels": app_label},
        #         "template": {
        #             "metadata": {"labels": app_label},
        #             "spec": {
        #                 "containers": [{
        #                     "name": "hello-kubernetes",
        #                     "image": "paulbouwer/hello-kubernetes:1.5",
        #                     "ports": [{"container_port": 8080}]
        #                 }
        #                 ]
        #             }
        #         }
        #     }
        # }
        #
        # service = {
        #     "api_version": "v1",
        #     "kind": "Service",
        #     "metadata": {"name": "hello-kubernetes"},
        #     "spec": {
        #         "type": "LoadBalancer",
        #         "ports": [{"port": 80, "target_port": 8080}],
        #         "selector": app_label
        #     }
        # }
        #
        # # option 1: use a construct
        # eks.KubernetesManifest(self, "hello-kub",
        #     cluster=cluster,
        #     manifest=[deployment, service]
        # )
        #
        # # or, option2: use `addManifest`
        # cluster.add_manifest("hello-kub", service, deployment)

        # # some other services definitions
        # nodejs_service_details = {
        #     "service_name": "ecsdemo-nodejs",
        #     "replicas": 3,
        #     "labels": {
        #         "app": "ecsdemo-nodejs"
        #     },
        #     "image": "brentley/ecsdemo-nodejs:latest",
        #     "port": 3000,
        #     "service_type": "backend"
        # }
        #
        # crystal_service_details = {
        #     "service_name": "ecsdemo-crystal",
        #     "replicas": 3,
        #     "labels": {
        #         "app": "ecsdemo-crystal",
        #     },
        #     "image": "brentley/ecsdemo-crystal:latest",
        #     "port": 3000,
        #     "service_type": "backend"
        # }
        #
        # frontend_service_details = {
        #     "service_name": "ecsdemo-frontend",
        #     "replicas": 3,
        #     "labels": {
        #         "app": "ecsdemo-frontend",
        #     },
        #     "image": "brentley/ecsdemo-frontend:latest",
        #     "port": 3000,
        #     "service_type": "frontend",
        #     "env": [
        #         {"name": "CRYSTAL_URL", "value": "http://ecsdemo-crystal.default.svc.cluster.local/crystal"},
        #         {"name": "NODEJS_URL", "value": "http://ecsdemo-nodejs.default.svc.cluster.local/"},
        #     ]
        # }

        # add asg capacity, or node group capacity are two distinct ways to add capacity to an EKS cluster (worker nodes)
        cluster.add_auto_scaling_group_capacity(
            conf.CLUSTER_ASG_NAME,
            auto_scaling_group_name=conf.CLUSTER_ASG_NAME,
            instance_type=ec2.InstanceType("t3.small"),
            machine_image_type=eks.MachineImageType.BOTTLEROCKET,  # or amazon linux
            min_capacity=1,
            desired_capacity=1,
            max_capacity=3,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            # bootstrap options not supported on BOTTLEROCKET
            # bootstrap_options=eks.BootstrapOptions(
            #     kubelet_extra_args="--node-labels foo=bar,goo=far",
            #     aws_api_retry_attempts=5,
            # ),
        )

        # add service account for fluent-bit
        service_account: eks.ServiceAccount = cluster.add_service_account(
            id="fluent-bit",
            name="fluent-bit",
        )
        service_account.add_to_principal_policy(iam.PolicyStatement(
            actions=["es:ESHttp*"],
            resources=["*"],  # lax permissions
            effect=iam.Effect.ALLOW
        ))
        # print the IAM role arn for this service account
        CfnOutput(
            self,
            "ServiceAccountIamRole",
            value=service_account.role.role_arn,
        )

        # # add service account - to provide pods with access to aws resources
        # service_account = cluster.add_service_account("MyServiceAccount")
        # bucket = s3.Bucket(self, "Bucket")
        # bucket.grant_read_write(service_account)
        # mypod = cluster.add_manifest("mypod", {
        #     "api_version": "v1",
        #     "kind": "Pod",
        #     "metadata": {"name": "mypod"},
        #     "spec": {
        #         "service_account_name": service_account.service_account_name,
        #         "containers": [{
        #             "name": "hello",
        #             "image": "paulbouwer/hello-kubernetes:1.5",
        #             "ports": [{"container_port": 8080}]
        #         }
        #         ]
        #     }
        # })
        # # create the resource after the service account.
        # mypod.node.add_dependency(service_account)
        # # print the IAM role arn for this service account
        # CfnOutput(self, "ServiceAccountIamRole", value=service_account.role.role_arn)
