"""A module for querying Cisco's Support API end-points

This module provides an interface for querying Cisco's EoX and sn2info
Support APIs.
"""
from __future__ import annotations

import time
from typing import Dict
from typing import List

import httpx


class ApixSupport():
    """Cisco Support API handler

    Provides a handler for interacting with the Cisco Support API
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

    def __send_query(self, url: str) -> Dict:
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
            )
            response.raise_for_status()  # Raises an HTTPStatusError if the request returned an error status code
            return response.json()

    def eox_query_by_pid(self, pids: List[str]) -> None:
        """Query EoX API end-point by PID

        Queries the EoX API end-point by prodict ID (PID). This takes a list
        of PID's, deduplicates the list as well as filters out some common
        blacklisted PID's that are often discovered by various data gathering
        sources (ex. Netmiko and textfsm parsing 'show inventory').

        Args:
            pids: A list of strings, each item representing a PID to query

        Raises:
            requests.exceptions.HTTPError: An HTTP errors occured when querying
                the API. Usually a 4xx client error or 5xx server error
                response
        """
        BLACK_LIST = ['', 'n/a', 'b', 'p', '^mf', 'unknown', 'unspecified', 'x']
        MAX_ITEMS = 20

        self.records = []   # Clear previous records before starting the new query
        self.items = []     # Clear previous items before starting the new query

        self.items = list({pid.strip() for pid in pids if pid.strip().lower() not in BLACK_LIST})

        API_URL = 'https://apix.cisco.com/supporttools/eox/rest/5/EOXByProductID/{}/{}'

        start_index = 0
        end_index = MAX_ITEMS
        while start_index <= len(self.items) - 1:
            page_index = 1
            pagination = True
            while pagination:
                url = API_URL.format(
                    page_index,
                    (',').join(self.items[start_index:end_index]),
                )
                resp = self.__send_query(url)

                if resp.get('EOXRecord'):
                    self.records = self.records + resp['EOXRecord']

                if page_index >= resp['PaginationResponseRecord']['LastIndex']:
                    pagination = False
                else:
                    page_index += 1

                # Play nice with Cisco API's and rate limit your queries
                time.sleep(0.5)

            start_index = end_index
            end_index += MAX_ITEMS

    def sn2info_query_by_sn(self, serial_numbers: List[str]) -> None:
        """
        Query SN2Info API end-point by serial numbers.

        Queries the SN2Info API end-point and retrieves coverage summary
        for each provided serial number. Serial numbers are deduplicated before querying.

        Args:
            serial_numbers: A list of strings, each item representing a serial number to query.

        Raises:
            requests.exceptions.HTTPError: An HTTP error occurred when querying
                the API. Usually a 4xx client error or 5xx server error response.
        """
        MAX_ITEMS = 75
        BLACK_LIST = ['', 'n/a', 'unknown', 'unspecified']

        self.records = []   # Clear previous records before starting the new query
        self.items = []     # Clear previous items before starting the new query

        self.items = list({sr_no for sr_no in serial_numbers if sr_no.lower() not in BLACK_LIST})

        API_URL = 'https://apix.cisco.com/sn2info/v2/coverage/summary/serial_numbers/{}'

        start_index = 0
        end_index = MAX_ITEMS
        while start_index < len(self.items):
            # Join serial numbers to create a query string
            query_string = ','.join(self.items[start_index:end_index])
            url = API_URL.format(query_string)
            resp = self.__send_query(url)

            if resp.get('serial_numbers'):
                self.records.extend(resp['serial_numbers'])

            # Increment the index window for the next set of serial numbers
            start_index += MAX_ITEMS
            end_index += MAX_ITEMS

            # Play nice with Cisco API's and rate limit your queries
            time.sleep(0.5)
