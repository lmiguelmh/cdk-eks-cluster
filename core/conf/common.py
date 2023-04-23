import os

ENV = os.getenv('ENV')
AWS_ACCOUNT_ID = "802430592232"
AWS_REGION = "us-west-2"
PROJECT_NAME = "eks"
RANDOM_SUFFIX = "007"

# ClusterStack
CLUSTER_STACK_NAME = f"{PROJECT_NAME}-cluster"
CLUSTER_EKS_NAME = f"{CLUSTER_STACK_NAME}-eks"
CLUSTER_ASG_NAME = f"{CLUSTER_STACK_NAME}-asg"
CLUSTER_SSH_KEY_NAME = f"{CLUSTER_STACK_NAME}-ssh-key"
CLUSTER_FLUENT_BIT_SERVICE_ACCOUNT_ROLE_ARN_SSM = f"{CLUSTER_STACK_NAME}-fluent-bit-service-account-role-arn"

# LoggingStack
LOGGING_STACK_NAME = f"{PROJECT_NAME}-logging"
LOGGING_ES_DOMAIN_NAME = f"{LOGGING_STACK_NAME}-es-domain-{RANDOM_SUFFIX}"
LOGGING_ES_DOMAIN_USER_POOL_NAME = f"{LOGGING_STACK_NAME}-es-domain-user"
LOGGING_ES_DOMAIN_USER_POOL_DOMAIN_NAME = f"{LOGGING_STACK_NAME}-es-domain-user-domain-{RANDOM_SUFFIX}"
LOGGING_ES_DOMAIN_USER_POOL_ADMIN_GROUP_NAME = f"{LOGGING_STACK_NAME}-es-domain-admins"
LOGGING_ES_DOMAIN_DEFAULT_ADMIN_EMAIL = "lmiguelmh@gmail.com"
LOGGING_ES_DOMAIN_DEFAULT_ADMIN_PASSWORD = "Abcd1234!"  # TODO read this from a secret
LOGGING_ES_DOMAIN_IDENTITY_POOL_NAME = f"{LOGGING_STACK_NAME}-es-domain-identity"
LOGGING_ES_DOMAIN_ADMIN_FN_ROLE_NAME = f"{LOGGING_STACK_NAME}-es-domain-admin-fn"
LOGGING_ES_DOMAIN_ADMIN_USER_ROLE_NAME = f"{LOGGING_STACK_NAME}-es-domain-admin-user"
LOGGING_ES_DOMAIN_LIMITED_USER_ROLE_NAME = f"{LOGGING_STACK_NAME}-es-domain-limited-user"
LOGGING_ES_DOMAIN_ES_REQUESTS_NAME = f"{LOGGING_STACK_NAME}-es-domain-es-requests"
LOGGING_ES_DOMAIN_ENDPOINT_SSM = f"{LOGGING_STACK_NAME}-es-domain-endpoint"

# ClusterLoggingRolesStack
CLUSTER_LOGGING_ROLES_STACK_NAME = f"{PROJECT_NAME}-logging-roles"
