from aws_cdk import Environment
from constructs import Construct

from cluster.component import ClusterStack
from cluster_logging.component import ClusterLoggingStack
from cluster_logging_roles.component import ClusterLoggingRolesStack
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

        _cluster = ClusterStack(
            scope,
            construct_id=conf.CLUSTER_STACK_NAME,
            stack_name=conf.CLUSTER_STACK_NAME,
            env=aws_env,
        )

        _cluster_logging = ClusterLoggingStack(
            scope,
            construct_id=conf.LOGGING_STACK_NAME,
            stack_name=conf.LOGGING_STACK_NAME,
            env=aws_env,
        )

        _cluster_logging_roles = ClusterLoggingRolesStack(
            scope,
            construct_id=conf.CLUSTER_LOGGING_ROLES_STACK_NAME,
            stack_name=conf.CLUSTER_LOGGING_ROLES_STACK_NAME,
            env=aws_env,
        )
        _cluster_logging_roles.add_dependency(_cluster)
        _cluster_logging_roles.add_dependency(_cluster_logging)
