from typing import Union, Mapping, Any

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


class ESRequest:
    _domain: str
    _es_api_client: OpenSearch

    @property
    def es_api_client(self) -> OpenSearch:
        return self._es_api_client

    @property
    def domain(self) -> str:
        return self._domain

    def __init__(self, domain: str, region: str):
        """
        Constructor.

        Parameters
        ----------
        domain : str
            Domain name, as it is given by attr_domain_endpoint (without the protocol/port)
        region : str
            AWS region
        """
        credentials = boto3.Session().get_credentials()
        auth = AWSV4SignerAuth(credentials, region)
        self._domain = domain
        self._es_api_client = OpenSearch(
            hosts=[{'host': domain, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

    def send_request(
            self,
            method: str,
            path: str,
            body: Union[str, Mapping[str, Any]],
            security_tenant: str = None
    ):
        """
        Perform an admin request.

        Parameters
        ----------
        method : str
        path : str
        body: str or Mapping[str, Any]
        security_tenant : Optional[str]

        Returns
        -------
        dict
        """
        headers = {
            "Content-Type": "application/json",
            "host": self._domain,
            # todo add Content-Length - required for DELETE requests
        }
        # if this is a kibana request (dashboards on OS) add a xsrf header
        if path.startswith("_plugin/kibana/") or path.startswith("_dashboards"):
            headers['kbn-xsrf'] = 'kibana'
        if security_tenant:
            headers['securitytenant'] = security_tenant

        path = path if path.startswith("/") else f"/{path}"
        response = self._es_api_client.transport.perform_request(
            method=method,
            url=path,
            headers=headers,
            body=body,
        )
        return response
