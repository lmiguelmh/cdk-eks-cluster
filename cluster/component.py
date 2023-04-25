from pathlib import Path

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_ssm as ssm,
    lambda_layer_kubectl_v25 as lambda_layer_kubectl_v25,
    aws_iam as iam, CfnOutput, CfnJson,
)
from cdk_ec2_key_pair import KeyPair
from constructs import Construct

from core import conf
from core.constructs.admin_user import AdminUser
from core.constructs.bastion import Bastion
from core.constructs.vpc import VPC


class ClusterStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #
        key_pair = KeyPair(
            self,
            conf.CLUSTER_SSH_KEY_NAME,
            name=conf.CLUSTER_SSH_KEY_NAME,
            resource_prefix=conf.CLUSTER_SSH_KEY_NAME,
        )

        # provision a cluster
        cluster = eks.Cluster(
            self,
            conf.CLUSTER_EKS_NAME,
            cluster_name=conf.CLUSTER_EKS_NAME,
            version=eks.KubernetesVersion.V1_25,
            kubectl_layer=lambda_layer_kubectl_v25.KubectlV25Layer(self, "kubectl"),
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            default_capacity=0,  # will customize it using an ASG
            # default_capacity_instance=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.SMALL),
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
            # masters_role=iam.Role(
            #     self,
            #     "EKSClusterRole",
            #     assumed_by=iam.AccountRootPrincipal(),
            # )
            # vpc=vpc,
            # vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)]
            # vpc_subnets=[aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)])
        )
        # cluster.aws_auth.add_masters_role()
        # add asg capacity for worker nodes, we can also use node group capacity
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
            # bootstrap options not supported on BOTTLEROCKET
            # bootstrap_options=eks.BootstrapOptions(
            #     kubelet_extra_args="--node-labels foo=bar,goo=far",
            #     aws_api_retry_attempts=5,
            # ),
        )
        # # add node group capacity, here we can specify a role
        # lt = ec2.CfnLaunchTemplate(
        #     self,
        #     "SSMLaunchTemplate",
        #     launch_template_data={
        #         "instanceType": "t3.small",
        #         # "tagSpecifications": [
        #         #     {
        #         #         "resourceType": "instance",
        #         #         "tags": [
        #         #             {"key": "Name", "value": f"app-{props['nameSuffix']}"},
        #         #             {"key": "Environment", "value": props["nameSuffix"]},
        #         #         ],
        #         #     },
        #         #     {
        #         #         "resourceType": "volume",
        #         #         "tags": [{"key": "Environment", "value": props["nameSuffix"]}],
        #         #     },
        #         # ],
        #     },
        # )
        # node_role = iam.Role(
        #     self,
        #     "EksNodeRole",
        #     assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        # )
        # node_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy")
        # )
        # node_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name(
        #         "AmazonEC2ContainerRegistryReadOnly"
        #     )
        # )
        # node_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        # )
        # cluster.add_nodegroup_capacity(
        #     "app-ng",
        #     launch_template_spec={
        #         "id": lt.ref,
        #         "version": lt.attr_latest_version_number,
        #     },
        #     min_size=1,
        #     max_size=2,
        #     ami_type=eks.NodegroupAmiType.AL2_X86_64,
        #     node_role=node_role,
        # )

        CfnOutput(
            self,
            "OIDC Issuer URL",
            value=cluster.cluster_open_id_connect_issuer_url,
        )
        CfnOutput(
            self,
            "OIDC Issuer",
            value=cluster.cluster_open_id_connect_issuer,
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

        # add service account for EBS CSI according:
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
        CfnOutput(
            self,
            "EbsCsiServiceAccountIamRole",
            value=ebs_csi_service_account.role.role_arn,
        )
        # add add-on
        eks.CfnAddon(
            self,
            'aws-ebs-csi-driver',
            addon_name='aws-ebs-csi-driver',
            cluster_name=cluster.cluster_name,
            preserve_on_delete=False,
            service_account_role_arn=ebs_csi_service_account.role.role_arn,
            # addon_version='addonVersion',
            # configuration_values='configurationValues',
            # resolve_conflicts='resolveConflicts',
            # tags=[{
            #     key: 'key',
            #     value: 'value',
            # }],
        )

        # aud = f"{cluster.cluster_open_id_connect_issuer}:aud"
        # sub = f"{cluster.cluster_open_id_connect_issuer}:sub"
        # conditions = CfnJson(self, "awsNodeOIDCCondition", value={
        #     aud: "sts.amazonaws.com",
        #     sub: "system:serviceaccount:kube-system:aws-node",
        # })
        # awsNodeIamRole = iam.Role(
        #     self,
        #     "awsNodeIamRole",
        #     assumed_by=iam.WebIdentityPrincipal(
        #         f"arn:aws:iam::{conf.AWS_ACCOUNT_ID}:oidc-provider/{cluster.cluster_open_id_connect_issuer}"
        #     ).with_conditions({
        #         "StringEquals": conditions,
        #     })
        # )
        # awsNodeIamRole.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy")
        # )
        # awsNodeCniPatch = eks.KubernetesPatch(
        #     self,
        #     "serviceAccount/aws-node",
        #     cluster=cluster,
        #     resource_name="serviceAccount/aws-node",
        #     resource_namespace="kube-system",
        #     apply_patch={
        #         "metadata": {
        #             "annotations": {
        #                 "eks.amazonaws.com/role-arn": awsNodeIamRole.role_arn
        #             }
        #         }
        #     },
        #     restore_patch={
        #         "metadata": {
        #             "annotations": {}
        #         }
        #     }
        # )

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
