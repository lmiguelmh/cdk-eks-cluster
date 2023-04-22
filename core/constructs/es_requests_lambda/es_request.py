import logging
import os
from typing import Dict, Any, Optional

from util import ESRequest

logger = logging.getLogger()
logger.setLevel(logging.INFO)

es_request: Optional[ESRequest] = None
ES_DOMAIN_ENDPOINT: str = os.environ["ES_DOMAIN_ENDPOINT"]
AWS_REGION: str = os.environ["AWS_REGION"]


def initialize_globals():
    global es_request
    if es_request is None:
        es_request = ESRequest(
            domain=ES_DOMAIN_ENDPOINT,
            region=AWS_REGION
        )


def main(event: Dict[str, Any]):
    request = event["request"]
    response = es_request.send_request(
        method=request["method"],
        path=request["path"],
        body=request.get("body"),
        security_tenant=request.get("securitytenant"),
    )
    logger.info(f"send_request: response={response}, request={request}")
    return response


def lambda_handler(event: Dict[str, Any], context):
    initialize_globals()
    logger.info("handler")
    try:
        response = main(event)
        return {
            "status": 200,
            "body": response,
        }
    except Exception as e:
        logger.error("an error occurred when sending request")
        logger.exception(e)
        return {
            "status": 500,
            "body": str(e),
        }
