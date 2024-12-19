"""A module for handling authentication Cisco Support and Service API's

This module provides an interface for authenticating against the Cisco
Support and Service API. You will require a valid client ID and secret. Once
authenticated, you can use the auth_token attribute for querying
the various support and Service API end-points.

    Typical usage example:

    creds = ApixLogin("my_client_key", "my_client_secret")
    SupportApiX(creds.auth_token, additional_parameters)
    creds.auth_still_valid()
    ServiceApiY(creds.auth_token, additional_parameters)

"""
from __future__ import annotations

import time

import httpx


class ApixLogin():
    """Cisco Support and Service API login handlers

    Provides base modules for the Cisco Support and Service API
    such as login functionality and token renewal. This supports
    a grant type of client credentials.
    """

    def __init__(self, client_key: str, client_secret: str) -> None:
        """Initializes the class and logs in

        Logs into the Cisco Support and Service API with the provided
        client ID and secret.

        Args:
            client_key: A string representing the API client key
            client_secret: A string representing the API client secret
        """
        self.__client_key = client_key
        self.__client_secret = client_secret
        self.login()

    def login(self) -> None:
        """Authenticates against the Cisco Support and Service API

        Authenticates against the Cisco Support and Service API using the
        initilized client ID and client secret.

        Attributes:
            auth_token: A string representing the URL header for authorization
                which will be used for subsequent API calls. The URL headers
                include a MIME type and an authorization header comprised of an
                access token and token type. An example:

                'Bearer 0123456789abcdef'

        Raises:
            requests.exceptions.HTTPError: An HTTP errors occured when querying
                the API. Usually a 4xx client error or 5xx server error
                response
        """
        self.auth_token = None
        self.auth_start = time.time()
        SSO_URL = 'https://id.cisco.com/oauth2/default/v1/token'

        params = {
            'grant_type': 'client_credentials',
            'client_id': self.__client_key,
            'client_secret': self.__client_secret,
        }

        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    SSO_URL,
                    data=params,
                )

            response.raise_for_status()
            self.auth_resp = response.json()

            self.auth_token = f"{self.auth_resp['token_type']} {self.auth_resp['access_token']}"

        except httpx.HTTPStatusError as http_err:
            # Handle HTTP errors
            print(f'HTTP error occurred: {http_err}')
            raise
        except Exception as err:
            # Handle general errors
            print(f'An error occurred: {err}')
            raise

    def auth_still_valid(self) -> bool:  # The return type hint should be `bool`
        """Determines if the auth token is still valid

        Compares the time the token was received with the current time
        and determines if the current time has surpassed the expiration time
        of the token. If the token has expired, a new token will be generated.

        Returns:
            True if the auth token is still valid, False otherwise.
        """

        current_time = time.time()
        # Calculate the expiration time based on auth_start and expires_in
        expiration_time = self.auth_start + self.auth_resp.get('expires_in', 0)

        if current_time >= expiration_time:
            # Token has expired, login again which will refresh the token
            self.login()
            return False

        # Token is still valid
        return True
