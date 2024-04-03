"""A module for querying Cisco's Service API end-points

This module provides an interface for querying Cisco's inventory 
hardware and network elements Service APIs.
"""
from typing import Optional
from typing import Dict
import time
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
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, 
                                  headers=self.url_headers, 
                                  params=params)
            response.raise_for_status()
            return response.json()

    def query_hardware_inventory(self, customer_id: str, inventory_name: Optional[str] = None, hw_type: Optional[str] = None) -> None:
        """
        Query Cisco hardware inventory API.

        Args:
            customer_id: Unique identifier of a Cisco customer (required).
            inventoryName: Name of the inventory (optional).
            hw_type: The physical type of the hardware (optional), such as Chassis, Module, etc.

        Raises:
            httpx.HTTPStatusError: Raised if an HTTP error occurs when querying the API.
        """
        API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/hardware'

        self.records = []   # Clear previous records before starting the new query

        # Construct the query parameters
        params = {'customerId': customer_id}
        if inventory_name:
            params['inventoryName'] = inventory_name
        if hw_type:
            params['hwType'] = hw_type

        resp = self.__send_query(API_URL, params=params)
        if resp.get('data'):
                    self.records =  resp['data']
        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)


    def query_network_elements_inventory(self, customer_id: str, inventory_name: Optional[str] = None) -> None:
            """
            Query Cisco network elements inventory API.

            Args:
                customer_id: Unique identifier of a Cisco customer (required).
                inventoryName: Name of the inventory (optional).

            Raises:
                httpx.HTTPStatusError: Raised if an HTTP error occurs when querying the API.
            """
            API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/network-elements'

            self.records = []   # Clear previous records before starting the new query

            # Construct the query parameters
            params = {'customerId': customer_id}
            if inventory_name:
                params['inventoryName'] = inventory_name

            resp = self.__send_query(API_URL, params=params)
            if resp.get('data'):
                        self.records =  resp['data']
            # Play nice with Cisco API's and rate limit your queries
            time.sleep(0.5)