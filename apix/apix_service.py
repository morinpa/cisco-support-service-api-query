"""A module for querying Cisco's Service API end-points

This module provides an interface for querying Cisco's inventory
hardware and network elements Service APIs.
"""
from __future__ import annotations

import time
from typing import Dict
from typing import Optional

import httpx


class ApixService:
    """Cisco Service API handler

    Provides a handler for interacting with the Cisco Service API
    """
    def __init__(self, auth_token: str, mime_type: str = 'application/json') -> None:
        """Initializes the class

        Initilizes the class and sets the authorization token and MIME type
        to be used within the URL headers.

        Args:
            auth_token: A string represting the authorization token
            mime_type:
                A string representing the content-type for the response data

        Attributes:
            records: A list of dictionaries representing EOXRecord
                responses from the Cisco Support Bug API.
        """
        self.url_headers = {
            'Accept': mime_type,
            'Authorization': auth_token,
        }
        self.customerId: Optional[str] = None
        self.items = []
        self.records = []

    def __send_query(self, url: str, params: Dict[str, str]) -> Dict:
        """Send query to a specific URL

        Sends a requests get to the provided URL. The self.url_headers
        attribute will be used in the request.

        Args:
            url: A string representing the URL to query

        Returns:
            A dict representing the JSON response from the requests library

        Raises:
            httpx.HTTPStatusError: An HTTP error occurred when querying
                the API. Usually a 4xx client error or 5xx server error
                response.
        """
        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                url,
                headers=self.url_headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    def query_hardware_inventory(self, **kwargs) -> None:
        """
        Query Cisco hardware inventory API.

        Args:
            This function accepts various keyword arguments that correspond
            to query parameters in the API request. The customer ID is
            automatically included from the instance's attribute. Other
            accepted parameters can be included as keyword arguments, and they
            will be directly passed to the API endpoint.

            Examples of accepted keyword arguments include:
            - inventoryName: Name of the inventory (optional).
            - hwType: The physical type of the hardware (optional), such as Chassis, Module, etc.

            service_api.query_hardware_inventory(inventoryName="some_inventory", hwType="Chassis")

            Each keyword argument correlates with query parameters of the API request.

        Raises:
            httpx.HTTPStatusError: Raised if an HTTP error occurs when querying the API.
        """
        API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/hardware'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        if resp.get('data'):
            self.records = resp['data']
            self.items = len(resp['data'])
        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_network_elements_inventory(self, **kwargs) -> None:
        """
        Query Cisco network elements inventory API.

        Args:
            This function accepts various keyword arguments that correspond
            to query parameters in the API request. The customer ID is
            automatically included from the instance's attribute. Other
            accepted parameters can be included as keyword arguments, and they
            will be directly passed to the API endpoint.

        Raises:
            httpx.HTTPStatusError: Raised if an HTTP error occurs when querying the API.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/network-elements'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        if resp.get('data'):
            self.records = resp['data']
            self.items = len(resp['data'])

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_software_inventory(self, **kwargs) -> None:
        """
        Query Cisco software inventory API.

        Args:
            This function accepts various keyword arguments that correspond
            to query parameters in the API request. The customer ID is
            automatically included from the instance's attribute. Other
            accepted parameters can be included as keyword arguments, and they
            will be directly passed to the API endpoint.

        Raises:
            httpx.HTTPStatusError: Raised if an HTTP error occurs when querying the API.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/software'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        if resp.get('data'):
            self.records = resp['data']
            self.items = len(resp['data'])

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)
