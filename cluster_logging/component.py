from aws_cdk import (
    aws_iam as iam,
    aws_cognito as cognito,
    aws_elasticsearch as elasticsearch,
    CfnOutput, Stack, CustomResource, custom_resources,CfnJson
)
from constructs import Construct

from core import conf
from core.constructs.es_requests import ESRequests


class ClusterLoggingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_pool = cognito.CfnUserPool(
            scope=self,
            id=conf.LOGGING_ES_DOMAIN_USER_POOL_NAME,
            user_pool_name=conf.LOGGING_ES_DOMAIN_USER_POOL_NAME,
            admin_create_user_config=cognito.CfnUserPool.AdminCreateUserConfigProperty(
                allow_admin_create_user_only=True
            ),
            username_attributes=["email"],
            auto_verified_attributes=["email"],
        )

        cognito.CfnUserPoolDomain(
            scope=self,
            id=conf.LOGGING_ES_DOMAIN_USER_POOL_DOMAIN_NAME,
            domain=conf.LOGGING_ES_DOMAIN_USER_POOL_DOMAIN_NAME,
            user_pool_id=user_pool.ref,
        )

        identity_pool = cognito.CfnIdentityPool(
            scope=self,
            id=conf.LOGGING_ES_DOMAIN_IDENTITY_POOL_NAME,
            identity_pool_name=conf.LOGGING_ES_DOMAIN_IDENTITY_POOL_NAME,
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[],
        )

        self._es_limited_user_role = iam.Role(
            scope=self,
            id=conf.LOGGING_ES_DOMAIN_LIMITED_USER_ROLE_NAME,
            role_name=conf.LOGGING_ES_DOMAIN_LIMITED_USER_ROLE_NAME,
            assumed_by=iam.FederatedPrincipal(
                federated="cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            )
        )

        self._es_admin_fn_role = iam.Role(
            scope=self,
            id=conf.LOGGING_ES_DOMAIN_ADMIN_FN_ROLE_NAME,
            role_name=conf.LOGGING_ES_DOMAIN_ADMIN_FN_ROLE_NAME,
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
        )
        self._es_admin_fn_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        self._es_admin_user_role = iam.Role(
            scope=self,
            id=conf.LOGGING_ES_DOMAIN_ADMIN_USER_ROLE_NAME,
            role_name=conf.LOGGING_ES_DOMAIN_ADMIN_USER_ROLE_NAME,
            assumed_by=iam.FederatedPrincipal(
                federated='cognito-identity.amazonaws.com',
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            )
        )

        es_search_http_policy = iam.ManagedPolicy(
            scope=self,
            id=f"ESHttpPolicy",
            roles=[self._es_admin_user_role, self._es_admin_fn_role],
        )

        cognito.CfnUserPoolGroup(
            scope=self,
            id=conf.LOGGING_ES_DOMAIN_USER_POOL_ADMIN_GROUP_NAME,
            group_name=conf.LOGGING_ES_DOMAIN_USER_POOL_ADMIN_GROUP_NAME,
            user_pool_id=user_pool.ref,
            role_arn=self._es_admin_user_role.role_arn,
        )

        domain_arn = f"arn:aws:es:{self.region}:{self.account}:domain/{conf.LOGGING_ES_DOMAIN_NAME}/*"
        es_search_http_policy.add_statements(
            iam.PolicyStatement(
                resources=[domain_arn],
                actions=[
                    "es:ESHttpPost",
                    "es:ESHttpGet",
                    "es:ESHttpPut",
                ],
                effect=iam.Effect.ALLOW,
            )
        )

        es_role = iam.Role(
            scope=self,
            id=f"ESRole",
            assumed_by=iam.ServicePrincipal("es.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonESCognitoAccess")]
        )

        self._es_domain = elasticsearch.CfnDomain(
            scope=self,
            id=f"SearchDomain",
            elasticsearch_cluster_config=elasticsearch.CfnDomain.ElasticsearchClusterConfigProperty(
                instance_type="t3.small.elasticsearch",
            ),
            ebs_options=elasticsearch.CfnDomain.EBSOptionsProperty(
                volume_size=10,
                ebs_enabled=True,
            ),
            elasticsearch_version="7.9",
            domain_name=conf.LOGGING_ES_DOMAIN_NAME,
            node_to_node_encryption_options=elasticsearch.CfnDomain.NodeToNodeEncryptionOptionsProperty(
                enabled=True,
            ),
            encryption_at_rest_options=elasticsearch.CfnDomain.EncryptionAtRestOptionsProperty(
                enabled=True,
            ),
            advanced_security_options=elasticsearch.CfnDomain.AdvancedSecurityOptionsInputProperty(
                enabled=True,
                master_user_options=elasticsearch.CfnDomain.MasterUserOptionsProperty(
                    master_user_arn=self._es_admin_fn_role.role_arn
                ),
            ),
            domain_endpoint_options=elasticsearch.CfnDomain.DomainEndpointOptionsProperty(
                enforce_https=True
            ),
            cognito_options=elasticsearch.CfnDomain.CognitoOptionsProperty(
                enabled=True,
                identity_pool_id=identity_pool.ref,
                role_arn=es_role.role_arn,
                user_pool_id=user_pool.ref
            ),
            # don't use this without fine-grained access control, vpc support, or ip based restrictions as this allows anonymous access
            access_policies={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "*"
                        },
                        "Action": "es:ESHttp*",
                        "Resource": domain_arn
                    }
                ]
            }
        )

        user_pool_clients = custom_resources.AwsCustomResource(
            scope=self,
            id=f"ClientIdResource",
            policy=custom_resources.AwsCustomResourcePolicy.from_sdk_calls(resources=[user_pool.attr_arn]),
            on_create=custom_resources.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="listUserPoolClients",
                parameters={
                    "UserPoolId": user_pool.ref
                },
                physical_resource_id=custom_resources.PhysicalResourceId.of(f"ClientId-{conf.LOGGING_ES_DOMAIN_USER_POOL_DOMAIN_NAME}")
            )
        )
        user_pool_clients.node.add_dependency(self._es_domain)

        client_id = user_pool_clients.get_response_field("UserPoolClients.0.ClientId")
        provider_name = f"cognito-idp.{self.region}.amazonaws.com/{user_pool.ref}:{client_id}"

        cognito.CfnIdentityPoolRoleAttachment(
            scope=self,
            id=f"UserPoolRoleAttachment",
            identity_pool_id=identity_pool.ref,
            roles={
                "authenticated": self._es_limited_user_role.role_arn
            },
            role_mappings=CfnJson(
                scope=self,
                id=f"RoleMappingsJson",
                value={
                    provider_name: {
                        "Type": "Token",
                        "AmbiguousRoleResolution": "AuthenticatedRole"
                    }
                }
            )
        )

        _es_requests = ESRequests(
            scope=self,
            name=conf.LOGGING_ES_DOMAIN_ES_REQUESTS_NAME,
            function_role=self._es_admin_fn_role,
            es_domain_endpoint=self._es_domain.attr_domain_endpoint,
        )
        self._es_request_function = _es_requests.add_function()
        _es_requests.add_custom_resource(
            all_access_roles=[
                self._es_admin_fn_role.role_arn,
                self._es_admin_user_role.role_arn,
            ],
            security_manager_roles=[
                self._es_admin_fn_role.role_arn,
                self._es_admin_user_role.role_arn,
            ],
            kibana_user_roles=[
                self._es_limited_user_role.role_arn,
            ],
        )
        _es_requests.node.add_dependency(self._es_domain)

        CfnOutput(
            self,
            'createUserUrl',
            description="ES users and user groups",
            value=f"https://{self.region}.console.aws.amazon.com/cognito/users?region={self.region}#/pool/{user_pool.ref}/users"
        )
        CfnOutput(
            self,
            'kibanaUrl',
            description="ES kibana URL",
            value=f"https://{self._es_domain.attr_domain_endpoint}/_plugin/kibana/"
        )
