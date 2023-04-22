import pathlib
from typing import Mapping, Any, List, Optional

from aws_cdk import (
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    custom_resources, CustomResource, BundlingOptions,
)
from aws_cdk.aws_iam import IRole
from constructs import Construct


class ESRequests(Construct):
    _function_role: IRole
    _es_domain_endpoint: str
    _name: str

    def __init__(self, scope: Construct, name: str, function_role: IRole, es_domain_endpoint: str):
        super().__init__(scope, name)
        self._name = name
        self._es_domain_endpoint = es_domain_endpoint
        self._function_role = function_role

    def _get_function(self, function_name: str, function_role: IRole, function_environment: Mapping[str, str]) -> lambda_.Function:
        _function_name = f"{self._name}-{function_name}"

        _function = lambda_.Function(
            scope=self,
            id=_function_name,
            function_name=_function_name,
            code=lambda_.Code.from_asset(
                str(pathlib.Path(__file__).parent.joinpath(f"es_requests_lambda").resolve()),
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ],
                ),
            ),
            environment={
                **function_environment,
            },
            layers=[],
            role=function_role,
            memory_size=128,
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.minutes(15),
            handler=f"{function_name}.lambda_handler",
        )
        _function.add_to_role_policy(
            iam.PolicyStatement(
                resources=["*"],
                actions=["es:*"],
                effect=iam.Effect.ALLOW
            )
        )
        return _function

    def add_function(self):
        # Utility lambda to make Opensearch admin requests
        return self._get_function(
            function_name="es_request",
            function_role=self._function_role,
            function_environment={
                "ES_DOMAIN_ENDPOINT": self._es_domain_endpoint,
            },
        )

    def add_custom_resource(
            self,
            properties: Optional[Mapping[str, Any]] = None,
            all_access_roles: Optional[List[str]] = None,
            security_manager_roles: Optional[List[str]] = None,
            kibana_user_roles: Optional[List[str]] = None,
    ):
        # custom lambda specially designed to be called from custom resources, to make Opensearch admin requests
        _provider_function = self._get_function(
            function_name="es_request_provider",
            function_role=self._function_role,
            function_environment={
                "ES_DOMAIN_ENDPOINT": self._es_domain_endpoint,
            },
        )
        _provider = custom_resources.Provider(
            scope=self,
            id="ESRequestsProvider",
            on_event_handler=_provider_function,
        )
        _provider.node.add_dependency(_provider_function)
        if properties:
            _properties = properties
        else:
            _properties = {"requests": [
                {
                    "method": "PUT",
                    "path": "_opendistro/_security/api/rolesmapping/all_access",
                    "body": {
                        "backend_roles": all_access_roles if all_access_roles else [],
                        "hosts": [],
                        "users": [],
                    }
                },
                {
                    "method": "PUT",
                    "path": "_opendistro/_security/api/rolesmapping/security_manager",
                    "body": {
                        "backend_roles": security_manager_roles if security_manager_roles else [],
                        "hosts": [],
                        "users": [],
                    }
                },
                {
                    "method": "PUT",
                    "path": "_opendistro/_security/api/rolesmapping/kibana_user",
                    "body": {
                        "backend_roles": kibana_user_roles if kibana_user_roles else [],
                        "hosts": [],
                        "users": [],
                    }
                },
            ]}
        _custom_resource = CustomResource(
            scope=self,
            id="ESRequestsCustomResource",
            service_token=_provider.service_token,
            properties=_properties,
        )
        _custom_resource.node.add_dependency(_provider)
