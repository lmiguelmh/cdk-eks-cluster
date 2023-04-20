from aws_cdk import Environment
from constructs import Construct

from cluster.component import ClusterStack
from core import conf


class Workload(Construct):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            aws_env: Environment,
            **kwargs
    ):
        super().__init__(scope, construct_id)

        ClusterStack(
            scope,
            construct_id=conf.CLUSTER_STACK_NAME,
            stack_name=conf.CLUSTER_STACK_NAME,
            env=aws_env,
        )
