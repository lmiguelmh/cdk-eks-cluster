import os

ENV = os.getenv('ENV')
AWS_ACCOUNT_ID = "802430592232"
AWS_REGION = "us-west-2"
PROJECT_NAME = "cdk-eks-cluster"

# Bastion
CLUSTER_STACK_NAME = f"{PROJECT_NAME}-cluster"
CLUSTER_EKS_NAME = f"{CLUSTER_STACK_NAME}-eks"
CLUSTER_ASG_NAME = f"{CLUSTER_STACK_NAME}-asg"  # auto scaling group
