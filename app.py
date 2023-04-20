#!/usr/bin/env python3

import aws_cdk as cdk

from core import conf
from workload import Workload

app = cdk.App()
aws_env = cdk.Environment(
    account=conf.AWS_ACCOUNT_ID,
    region=conf.AWS_REGION,
)
Workload(
    scope=app,
    construct_id=f"{conf.ENV}",
    aws_env=aws_env,
)
app.synth()
