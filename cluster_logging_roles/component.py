from aws_cdk import (
    aws_iam as iam,
    aws_ssm as ssm,
    Stack
)
from constructs import Construct

from core import conf
from core.constructs.es_requests import ESRequests


class ClusterLoggingRolesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        es_admin_fn_role = iam.Role.from_role_name(
            self,
            id=conf.LOGGING_ES_DOMAIN_ADMIN_FN_ROLE_NAME,
            role_name=conf.LOGGING_ES_DOMAIN_ADMIN_FN_ROLE_NAME,
        )
        es_admin_user_role = iam.Role.from_role_name(
            self,
            id=conf.LOGGING_ES_DOMAIN_ADMIN_USER_ROLE_NAME,
            role_name=conf.LOGGING_ES_DOMAIN_ADMIN_USER_ROLE_NAME,
        )
        es_limited_user_role = iam.Role.from_role_name(
            self,
            id=conf.LOGGING_ES_DOMAIN_LIMITED_USER_ROLE_NAME,
            role_name=conf.LOGGING_ES_DOMAIN_LIMITED_USER_ROLE_NAME,
        )
        es_domain_endpoint = ssm.StringParameter.value_for_string_parameter(
            self,
            conf.LOGGING_ES_DOMAIN_ENDPOINT_SSM
        )
        cluster_fluent_bit_service_account_role_arn = ssm.StringParameter.value_for_string_parameter(
            self,
            conf.CLUSTER_FLUENT_BIT_SERVICE_ACCOUNT_ROLE_ARN_SSM
        )

        es_requests = ESRequests(
            scope=self,
            name=conf.LOGGING_ES_DOMAIN_ES_REQUESTS_NAME,
            function_role=es_admin_fn_role,
            es_domain_endpoint=es_domain_endpoint,
        )
        es_requests.add_function()
        es_requests.add_custom_resource(
            all_access_roles=[
                es_admin_fn_role.role_arn,
                es_admin_user_role.role_arn,
                cluster_fluent_bit_service_account_role_arn,
            ],
            security_manager_roles=[
                es_admin_fn_role.role_arn,
                es_admin_user_role.role_arn,
            ],
            kibana_user_roles=[
                es_limited_user_role.role_arn,
            ],
        )
