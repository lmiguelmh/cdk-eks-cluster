import aws_cdk as cdk

from core import conf
from pipeline import PipelineStack
from workload import Workload

app = cdk.App()
aws_env = cdk.Environment(
    account=conf.AWS_ACCOUNT_ID,
    region=conf.AWS_REGION,
)

# allow workload to be deployed without ci/cd
Workload(
    scope=app,
    construct_id=f"{conf.ENV}",
    aws_env=aws_env,
)

# allow deployment of ci/cd pipeline
PipelineStack(
    scope=app,
    construct_id=conf.PIPELINE_STACK_NAME,
    env=aws_env,
    target_aws_env=aws_env,
)

app.synth()
