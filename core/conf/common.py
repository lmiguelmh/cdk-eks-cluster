import os

ENV = os.getenv('ENV')
AWS_ACCOUNT_ID = "802430592232"
AWS_REGION = "us-west-2"
PROJECT_NAME = "eks"
RANDOM_SUFFIX = "007"

# ClusterStack
CLUSTER_STACK_NAME = f"{PROJECT_NAME}-cluster"
CLUSTER_EKS_NAME = f"{CLUSTER_STACK_NAME}-eks"
CLUSTER_ASG_NAME = f"{CLUSTER_STACK_NAME}-asg"  # autoscaling group

# LoggingStack
LOGGING_STACK_NAME = f"{PROJECT_NAME}-logging"
LOGGING_ES_DOMAIN_NAME = f"{LOGGING_STACK_NAME}-es-domain-{RANDOM_SUFFIX}"
LOGGING_ES_DOMAIN_USER_POOL_NAME = f"{LOGGING_STACK_NAME}-es-domain-user"
LOGGING_ES_DOMAIN_USER_POOL_DOMAIN_NAME = f"{LOGGING_STACK_NAME}-es-domain-user-domain-{RANDOM_SUFFIX}"
LOGGING_ES_DOMAIN_USER_POOL_ADMIN_GROUP_NAME = f"{LOGGING_STACK_NAME}-es-domain-admins"
LOGGING_ES_DOMAIN_IDENTITY_POOL_NAME = f"{LOGGING_STACK_NAME}-es-domain-identity"
LOGGING_ES_DOMAIN_ADMIN_FN_ROLE_NAME = f"{LOGGING_STACK_NAME}-es-domain-admin-fn"
LOGGING_ES_DOMAIN_ADMIN_USER_ROLE_NAME = f"{LOGGING_STACK_NAME}-es-domain-admin-user"
LOGGING_ES_DOMAIN_ES_REQUESTS_NAME = f"{LOGGING_STACK_NAME}-es-domain-es-requests"
