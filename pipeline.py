from typing import Any

import aws_cdk as cdk
from aws_cdk import (
    aws_codepipeline as codepipeline,
    pipelines,
    aws_s3 as s3,
    aws_iam as iam,
    Stage
)
from constructs import Construct
from varname import nameof

from core import conf
from workload import Workload


class PipelineStack(cdk.Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            target_aws_env: cdk.Environment,
            **kwargs: Any,
    ):
        super().__init__(scope, construct_id, **kwargs)

        pipeline = codepipeline.Pipeline(
            scope=self,
            id="Pipeline",
            pipeline_name=conf.PIPELINE_STACK_NAME,
            restart_execution_on_update=True,
            artifact_bucket=s3.Bucket(
                self,
                conf.PIPELINE_ARTIFACT_BUCKET_NAME,
                bucket_name=conf.PIPELINE_ARTIFACT_BUCKET_NAME,
                auto_delete_objects=True,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            ),
        )

        # 1. Rol del pipeline.
        pipeline_role = iam.Role(
            pipeline,
            conf.PIPELINE_ROLE_NAME,
            role_name=conf.PIPELINE_ROLE_NAME,
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
        )
        pipeline_role.attach_inline_policy(
            iam.Policy(
                id="FullAccessPolicy",
                scope=pipeline,
                # TODO reduce permissions
                statements=[iam.PolicyStatement(
                    resources=["*"],
                    actions=["*"],
                    effect=iam.Effect.ALLOW,
                )]
            )
        )

        # 2. Paso de sintetización a Cloudformation.
        synth = pipelines.CodeBuildStep(
            id="Synth",
            role=pipeline_role,
            # 3. Datos del repositorio.
            input=pipelines.CodePipelineSource.connection(
                repo_string=conf.PIPELINE_GITHUB_REPOSITORY,
                branch=conf.PIPELINE_GITHUB_BRANCH,
                connection_arn=conf.PIPELINE_GITHUB_CONNECTION_ARN,
            ),
            env={
                nameof(conf.ENV): conf.ENV,
            },
            install_commands=[
                "python -m pip install -r requirements.txt",
            ],
            commands=[
                f"npx cdk synth {conf.PIPELINE_STACK_NAME}",
            ],
        )
        code_pipeline = pipelines.CodePipeline(
            scope=self,
            id="CodePipeline",
            code_pipeline=pipeline,
            docker_enabled_for_synth=True,
            publish_assets_in_parallel=True,
            synth=synth,
        )

        # 5. Paso de despliegue.
        stage = Stage(
            scope=code_pipeline,
            id="Deploy",
            env=target_aws_env,
        )
        workload = Workload(
            scope=stage,
            construct_id=conf.PIPELINE_WORKLOAD_NAME,
            aws_env=target_aws_env,
        )
        stage_deployment = code_pipeline.add_stage(stage)

        # 4. Pasos de ejecución.
        deploy_step = pipelines.CodeBuildStep(
            "PostDeploy",
            env_from_cfn_outputs={
                "EKS_UPDATE_KUBECONFIG": workload.cluster.eks_update_kubeconfig_cfn_output,
                "ES_ENDPOINT": workload.cluster_logging.es_domain_endpoint_cfn_output,
                # AWS_REGION is already defined on the environment
            },
            role=pipeline_role,
            commands=[
                "mkdir -p ~/.kube",
                "eval $EKS_UPDATE_KUBECONFIG",

                # deploy fluent-bit
                "cat fluentbit.yaml | envsubst > fluentbit.yaml",
                "kubectl apply -f fluentbit.yaml ",  # 2nd run it fails with error: no objects passed to apply
                "kubectl --namespace=logging get sa",
                "kubectl --namespace=logging get pods",
            ],
        )
        stage_deployment.add_post(deploy_step)
