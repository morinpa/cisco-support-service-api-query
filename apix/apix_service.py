"""A module for querying Cisco's Service API end-points

This module provides an interface for querying Cisco's inventory
hardware and network elements Service APIs.
"""
from __future__ import annotations

import logging
import time
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

import httpx
from httpx import HTTPStatusError
from httpx import ReadTimeout


logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')


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
        self.numberItems = []
        self.pagination = []
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

    def with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        A generic retry function that will execute the passed function with provided
        arguments and keyword arguments, retrying on failure.

        Args:
            func: The function that needs to be executed.
            *args: Arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            The result of the function call.

        Raises:
            Exception: Re-raises any exception after the retry limit is exceeded.
        """
        max_retries = 3
        interval = 5  # seconds to wait between retries
        func_name = getattr(func, '__name__', str(func))
        logger = logging.getLogger(__name__)  # Get a logger instance for this module

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (ReadTimeout, HTTPStatusError) as e:
                last_attempt = attempt == max_retries
                retry_message = f'Attempt {attempt + 1} failed for {func_name}: {e}.'

                if isinstance(e, HTTPStatusError) and not last_attempt:
                    # Handle specific HTTP status errors (like 502) that you're willing to retry
                    retry_message += f' Encountered HTTPStatusError with code {e.response.status_code}.'

                if not last_attempt:
                    # print(f'{retry_message} Retrying in {interval} seconds...')
                    logger.warning(f'{retry_message} Retrying in {interval} seconds...')
                    time.sleep(interval)
                else:
                    # print(f'{retry_message} No more retries left.')
                    logger.error(f'{retry_message} No more retries left.')
                    raise

    def __process_response(self, response) -> None:
        """
        Process the API response, setting records and pagination attributes.

        Args:
            response: The response object from the API call.
        """
        # Reset records and pagination each time this method is called
        self.records = []
        self.numberItems = 0
        self.pagination = []

        if response:
            # Set records and calculate the number of items if 'data' in response
            self.records = response.get('data', [])
            self.numberItems = len(self.records)

            # Set pagination if 'pagination' in response
            self.pagination = response.get('pagination', self.pagination)

    def query_hardware_inventory(self, **kwargs) -> None:
        """
        Query Cisco hardware inventory API.

        Args:
            Parameter	        Type	Max	Required	Description
                                        Length
            customerId	        NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	    STRING	25	Optional	Name of the inventory.
            managedNeInstanceId	NUMBER	19	Optional	Identifier for the managed NetworkElement. In the case of a composite, multiple NetworkElements make up the whole. Each members of the composite is identified by its own neInstanceId. For example, a stack with 3 members has a total of 4 NetworkElements that consists of one managed NetworkElement (identified by managedNeInstanceId) and 3 additional NetworkElements (identified by neInstanceId). For information on Composite, refer Glossary.
            neInstanceId	    NUMBER	19	Optional	Unique id used to identify an instance of a network element. Network element is a manageable logical entity uniting one or more physical devices. This allows distributed devices to be managed in a unified way using one management system.
            hwInstanceId	    NUMBER	22	Optional	Unique identifier of the physical hardware.
            hwType	            STRING	512	Optional	The physical type of the hardware. Valid values include Chassis, Module, Fan, Power Supply, Other.
            productSubtype	    STRING	512	Optional	Further classification for hardware within a Product Type. It primarily exists for Data Center (UCS), Wireless (LWAP), and Collaboration (IP Phone) use-cases.
            productType	        STRING	512	Optional	Broad classification of Cisco product that categorizes its function.
            productFamily	    STRING	512	Optional	Grouping of similar Cisco products.
            productId	        STRING	512	Optional	The alphanumeric unique identifier of a Cisco Product. The id is used by customers to order Cisco products. For example: CISCO2921/K9, WS-C3750X-24S-S, WS-X6748-GE-TX.
            serialNumber	    STRING	512	Optional	A serial number is a unique number used for identification. For example: FTX1512AHK2, FDO1541Z067, SAD07370169.
            dimensionsFormat	STRING		Optional	Product dimensions (dimension format). "Dimensions (HxWxD)
            dimensions	        STRING		Optional	Product dimensions (dimension value). "31.25 x 17.2 x 22.75 in. (79.4 x 43.7 x 57.8 cm)
            weight	            STRING		Optional	"235 lb. (106.6 kg) fully-configured chassis.
            formFactor	        STRING		Optional	"18 rack units (RU) Mounting: 19 in. rack mountable\n(front or rear); 2 units per 7 ft. rack. \nNote: Mounting in 23 in. racks is possible with optional third-party hardware", "product_support_page": "",
            supportPage	        STRING		Optional	URL of the Cisco.com support product model (or series) page.
            visioStencilUrl	    STRING		Optional	URL from which the .zip file of the Visio stencils for a given product can be downloaded if it exists.
            smallImageUrl	    STRING		Optional	List of small image URLs for a given product if they exist. If multiple URLs exist, the URLs in the list will be separated by commas.
            largeImageUrl	    STRING		Optional	List of large image URLs for a given product if they exist. If multiple URLs exist, the URLs in the list will be separated by commas.
            baseProductId	    STRING		Optional	Manufacturing (or base) product ID for a given serial number. (UBR10012)
            productReleaseDate	DATE		Optional	Product release date in the following format: YYYY-MM-DD.
            page	            NUMBER		Optional	Page number of the response.
            rows	            NUMBER		Optional	Number of rows of data per page.
            snapshot	        STRING		Optional	Option is "LATEST" and the value is case insensitive. Report includes inventory from latest upload only.
            sort	            STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	            STRING		Optional	Requested fields in the response.
        """
        API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/hardware'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)
        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_network_elements_inventory(self, **kwargs) -> None:
        """
        Query Cisco network elements inventory API.

        Args:
            Parameter	        Type	Max	    Required	Description
                                        Length
            customerId	        NUMBER	12	    Required	Unique identifier of a Cisco customer.
            inventoryName	    STRING	25	    Optional	Name of the inventory.
            neInstanceId	    NUMBER	19	    Optional	Unique id used to identify an instance of a network element. Network element is a manageable logical entity uniting one or more physical devices. This allows distributed devices to be managed in a unified way using one management system.
            managedNeInstanceId	NUMBER	19	    Optional	Identifier for the managed NetworkElement. In the case of a composite, multiple NetworkElements make up the whole. Each members of the composite is identified by its own neInstanceId. For example, a stack with 3 members has a total of 4 NetworkElements that consists of one managed NetworkElement (identified by managedNeInstanceId) and 3 additional NetworkElements (identified by neInstanceId). For information on Composite, refer Glossary.
            productFamily	    STRING	512	    Optional	Grouping of similar Cisco Products. Example: Cisco 2900 Series Integrated Services Routers.
            isManagedNe	        STRING	1	    Optional	Indicates whether the device is directly managed by the collector.
            ipAddress	        STRING	1024	Optional	A numerical label assigned to each device (for example, computer, printer) participating in a computer network that uses the Internet Protocol for communication.
            hostname	        STRING	512	    Optional	Human-readable nicknames that correspond to the address of a device connected to a network.
            sysName	            STRING	255	    Optional	SNMP sysName of the network element. It will be a fully-qualified name, if domain name is set on the device.
            swVersion	        STRING	128	    Optional	A version of operating system installed on the Network Element. Example: 15.1(4)M4.
            swType	            STRING	512	    Optional	Type of software that is installed on this host/system.
            neType	            STRING	128	    Optional	Type of the network element. Values include COMPOSITE, COMPOSED, VIRTURAL, APPLICATION, STANDALONE.
            page	            NUMBER		    Optional	Page number of the response.
            rows	            NUMBER		    Optional	Number of rows of data per page.
            snapshot	        STRING		    Optional	Option is "LATEST" and the value is case insensitive. Report includes inventory from latest upload only.
            sort	            STRING		    Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	            STRING		    Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/network-elements'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_software_inventory(self, **kwargs) -> None:
        """
        Query Cisco software inventory API.

        Args:
            Parameter	        Type	Max	Required	Description
                                        Length
            customerId	        NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	    STRING	25	Optional	Name of the inventory.
            managedNeInstanceId	NUMBER	19	Optional	Identifier for the managed NetworkElement. In the case of a composite, multiple NetworkElements make up the whole. Each members of the composite is identified by its own neInstanceId. For example, a stack with 3 members has a total of 4 NetworkElements that consists of one managed NetworkElement (identified by managedNeInstanceId) and 3 additional NetworkElements (identified by neInstanceId). For information on Composite, refer Glossary.
            swType	            STRING	255	Optional	Type of software that is installed on this host/system.
            swVersion	        STRING	512	Optional	A version of operating system installed on the Network Element. Example: 15.1(4)M4.
            swCategory	        STRING	128	Optional	Broader category of the software record. The role of the software running on a network element. For example, System Software, Application Software Patch, Package .
            swStatus	        STRING	128	Optional	Status of the software running on the network element. Default value is ACTIVE. For PIE and SMU it can be COMMITTED.
            swName	            STRING	512	Optional	Name of the software running on the network element. For System SW, the value is image name. For PIE, the value is package name and SMU, the value is SMU name. For example, asr9k-p-4.2.3.CSCtz41749-1.0.0 .
            page	            NUMBER		Optional	Page number of the response.
            rows	            NUMBER		Optional	Number of rows of data per page.
            snapshot	        STRING		Optional	Option is "LATEST" and the value is case insensitive. Report includes inventory from latest upload only.
            sort	            STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	            STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/inventory/software'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_customer_details(self, **kwargs) -> None:
        """
        Query Cisco Customer Details API.

        Args:
            Parameter	Type	Max	Required	Description
                                Length
            page	    NUMBER	    Optional	Page number of the response.
            rows	    NUMBER	    Optional	Number of rows of data per page.
            format	    STRING	    Optional	Supported extension of files such
                                                as JSON, CSV, TSV.
            sort	    STRING	    Optional	Supported sort criteria are either
                                                ‘asc’ for ascending or ‘desc’ for descending.
            fields	    STRING	    Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/customer-info/customer-details'

        self.records = []   # Clear previous records before starting the new query

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_inventory_groups(self, **kwargs) -> None:
        """
        Query Cisco customer Inventory Groups API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	Type	Max	Required	Description
                                Length
            customerId	NUMBER	12	Required	Unique identifier of a Cisco customer.
            page	    NUMBER		Optional	Page number of the response.
            rows	    NUMBER		Optional	Number of rows of data per page.
            format	    STRING		Optional	Supported extension of files such as JSON, CSV, TSV.
            sort	    STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	    STRING		Optional	Requested fields in the response.

        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/customer-info/inventory-groups'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_contract_details(self, **kwargs) -> None:
        """
        Query Cisco Contract Details API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	        Type	Max	Required	Description
                                        Length
            customerId	        NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	    STRING	25	Optional	Name of the inventory.
            contractStatus	    STRING	128	Optional	[Masking Applicable] Status of the contract. For example, unmasked value can be Active, Signed, QA Hold, Overdue, Terminated, Service, Entered, Expired & Inactive and masked value will be Confidential. For more details, refer Masking Details section.
            contractStartDate	DATE		Optional	[Masking Applicable] Provides the service contract details from start date to current date. GMT date format: YYYY-MM-DD. For example, unmasked value can be YYYY-MM-DD and masked value will be Confidential. For more details, refer Masking Details section.
            contractEndDate	    DATE		Optional	[Masking Applicable] Lists the details of service contract from commencing to end date. GMT date format: YYYY-MM-DD. For example, unmasked value can be YYYY-MM-DD and masked value will be Confidential. For more details, refer Masking Details section.
            contractNumber	    NUMBER	512	Optional	Contract identifier of the service contract. For example, 2689444, 91488861, 92246411.
            serviceLevel	    STRING	128	Optional	[Masking Applicable] Alphanumeric code that denotes the purchased support service. For example, unmasked value can be NSOP, PSSE, NC2P and masked value will be Confidential. For more details, refer Masking Details section.
            page	            NUMBER		Optional	Page number of the response.
            rows	            NUMBER		Optional	Number of rows of data per page.
            snapshot	        STRING		Optional	Option is "LATEST" and value is case insensitive. Report includes contract details of latest inventory upload only.
            sort	            STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	            STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/contracts/contract-details'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_contracts_coverage(self, **kwargs) -> None:
        """
        Query Cisco Contracts Coverage API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	        Type	Max	Required	Description
                                        Length
            customerId	        NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	    STRING	25	Optional	Name of the inventory.
            serialNumber	    STRING	512	Optional	A serial number is a unique number used for identification. For example: FTX1512AHK2, FDO1541Z067, SAD07370169.
            productId	        STRING	128	Optional	The alphanumeric unique identifier of a Cisco Product. The id is used by customers to order Cisco products. For example: CISCO2921/K9, WS-C3750X-24S-S, WS-X6748-GE-TX.
            coverageStatus	    STRING	128	Optional	The contract coverage status of a piece of hardware. For example, Active, Signed, QA Hold, Overdue.
            coverageStartDate	DATE		Optional	[Masking Applicable] Start date of the coverage. GMT date format: YYYY-MM-DD. For example, unmasked value can be YYYY-MM-DD and masked value will be Confidential. For more details, refer Masking Details section.
            coverageEndDate	    DATE		Optional	[Masking Applicable] End date of the coverage. GMT date format: YYYY-MM-DD. For example, unmasked value can be YYYY-MM-DD and masked value will be Confidential. For more details, refer Masking Details section.
            contractStatus	    STRING	128	Optional	[Masking Applicable] Status of the contract. For example, unmasked value can be Active, Signed, QA Hold, Overdue, Terminated, Service, Entered, Expired & Inactive and masked value will be Confidential. For more details, refer Masking Details section.
            contractNumber	    NUMBER	512	Optional	Contract identifier of the service contract. For example, 2689444, 91488861, 92246411.
            serviceLevel	    STRING	128	Optional	[Masking Applicable] Alphanumeric code that denotes the purchased support service. For example, unmasked value can be NSOP, PSSE, NC2P and masked value will be Confidential. For more details, refer Masking Details section.
            serviceLineStatus	STRING	128	Optional	Status of the service line. For example: Active, Signed, QA Hold, Overdue.
            billtoPartyId	    NUMBER		Optional	[Masking Applicable] Unique identifier of an Entitled Party where the contract was billed to. For example, unmasked value can be 30411234 and masked value will be Confidential. For more details, refer Masking Details section.
            page	            NUMBER		Optional	Page number of the response.
            rows	            NUMBER		Optional	Number of rows of data per page.
            snapshot	        STRING		Optional	Option is "LATEST" and value is case insensitive. Report includes coverage details of latest inventory upload only.
            sort	            STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	            STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/contracts/coverage'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_contracts_not_covered(self, **kwargs) -> None:
        """
        Query Cisco Contracts Not-Covered API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	            Type	Max	Required	Description
                                            Length
            customerId	            NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	        STRING	25	Optional	Name of the inventory.
            serialNumber	        STRING	512	Optional	A serial number is a unique number used for identification. For example: FTX1512AHK2, FDO1541Z067, SAD07370169.
            productId	            STRING	128	Optional	The alphanumeric unique identifier of a Cisco Product. The id is used by customers to order Cisco products. For example: CISCO2921/K9, WS-C3750X-24S-S, WS-X6748-GE-TX.
            contractInstanceNumber	NUMBER	128	Optional	Unique identifier for a contract.
            page	                NUMBER		Optional	Page number of the response.
            rows	                NUMBER		Optional	Number of rows of data per page.
            snapshot	            STRING		Optional	Option is "LATEST" and value is case insensitive. Report includes inventory not covered by any contract from latest upload only.
            sort	                STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/contracts/not-covered'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_field_notices(self, **kwargs) -> None:
        """
        Query Cisco Field Notices API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	        Type	Max	Required	Description
                                        Length
            customerId	        NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	    STRING	25	Optional	Name of the inventory.
            neInstanceId	    NUMBER	19	Optional	Unique id used to identify an instance of a network element. Network element is a manageable logical entity uniting one or more physical devices. This allows distributed devices to be managed in a unified way using one management system.
            managedNeInstanceId	NUMBER	32	Optional	The unique, generated ID of the network element.
            hwInstanceId	    NUMBER		Optional	hardware instance ID.
            vulnerabilityStatus	STRING	30	Optional	The vulnerability status of a Network element. Permitted Values: Potentially Vulnerable, Not Vulnerable and Vulnerable.
            bulletinNumber	    NUMBER		Optional	Cisco.com bulletin number for Field Notices.
            swType	            STRING	255	Optional	Software Type.
            hostname	        STRING	512	Optional	Hostnames are human-readable nicknames that correspond to the address of a device connected to a network.
            page	            NUMBER		Optional	Page number of the response.
            rows	            NUMBER		Optional	Number of rows of data per page.
            snapshot	        STRING		Optional	Option is "LATEST" and value is case insensitive. Report includes field notices for latest upload only.
            sort	            STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	            STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/field-notices'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_field_notice_bulletins(self, **kwargs) -> None:
        """
        Query Cisco Field Notice Bulletins API.

        Args:
            Parameter	            Type	Max	Required	Description
                                            Length
            bulletinNumber	        NUMBER	38	Optional	Cisco.com bulletin number for Field Notices.
            bulletinFirstPublished	DATE		Optional	Date when the bulletin was first published to Cisco.com.
            page	                NUMBER		Optional	Page number of the response.
            rows	                NUMBER		Optional	Number of rows of data per page.
            sort	                STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/field-notice-bulletins'

        self.records = []   # Clear previous records before starting the new query

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_hardware_eol(self, **kwargs) -> None:
        """
        Query Cisco Hardware End Of Life API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	            Type	Max	Required	Description
                                            Length
            customerId	            NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	        STRING	25	Optional	Name of the inventory.
            neInstanceId	        NUMBER	19	Optional	Unique id used to identify an instance of a network element. Network element is a manageable logical entity uniting one or more physical devices. This allows distributed devices to be managed in a unified way using one management system.
            managedNeInstanceId	    NUMBER	32	Optional	The unique, generated ID of the network element.
            hwInstanceId	        NUMBER		Optional	hardware instance ID.
            hostname	            NUMBER	512	Optional	Hostname of the Network Element.
            hwType	                STRING	255	Optional	Physical type of the hardware such as Chassis, Module, Fan, Power Supply, and Other.
            currentHwEolMilestone	STRING	255	Optional	Latest hardware end-of-life milestone that has passed for the product. Example: EoSale, LDoS.
            nextHwEolMilestone	    STRING	255	Optional	Next hardware end-of-life milestone that is coming up. If the device is already LDoS it will not have a next milestone. Example: EoSale, LDoS.
            page	                NUMBER		Optional	Page number of the response.
            rows	                NUMBER		Optional	Number of rows of data per page.
            snapshot	            STRING		Optional	Option is "LATEST" and value is case insensitive. Report includes hardware EOL information for latest upload only.
            sort	                STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/hardware-eol'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_hardware_eol_bulletins(self, **kwargs) -> None:
        """
        Query Cisco Hardware End Of Life Bulletins API.

        Args:
            Parameter	                    Type	Max	    Required	Description
                                                    Length
            hwEolInstanceId	                NUMBER	38	    Optional	The unique identifier for hardware bulletin.
            bulletinProductId	            STRING	50	    Optional	Cisco product published at the time of EOL announcement.
            bulletinNumber	                STRING	24	    Optional	Cisco.com bulletin number for an End-of-Life bulletin and Field Notices.
            bulletinTitle	                STRING	1000	Optional	Cisco.com Title/Headline for the bulletin.
            eoLifeAnnouncementDate	        DATE		    Optional	Date the document that announces the end-of-sale and end-of-life of a product is distributed to the general public. GMT date format YYYY-MM-DD.
            eoSaleDate	                    DATE		    Optional	Last date to order the product through Cisco point-of-sale mechanisms. The product is no longer for sale after this date. GMT date format YYYY-MM-DD.
            lastShipDate	                DATE		    Optional	Last possible ship date that can be requested of Cisco and/or its contract manufacturers. Actual ship date is dependent on lead time.
            eoSwMaintenanceReleasesDate	    DATE		    Optional	Last date that Cisco engineering may release any final software maintenance releases or bug fixes. After this date, Cisco engineering will no longer develop, repair, maintain, or test the product software. GMT date format YYYY-MM-DD.
            eoRoutineFailureAnalysisDate	DATE		    Optional	Last possible date a routine failure analysis may be performed to determine the cause of hardware product failure or defect. GMT date format YYYY-MM-DD.
            eoNewServiceAttachmentDate	    DATE		    Optional	For equipment and software that is not covered by a service and support contract, this is the last date to order a new service and support contract or add the equipment and/or software to an existing service-and-support contract. GMT date format YYYY-MM-DD.
            eoServiceContractRenewalDate	DATE		    Optional	Last date to extend or renew a service contract for the product. GMT date format YYYY-MM-DD.
            lastDateOfSupport	            DATE		    Optional	Last date to receive applicable service and support for the product as entitled by active service contracts or by warranty terms and conditions. After this date, all support services for the product will be unavailable and the product becomes obsolete. GMT date format YYYY-MM-DD.
            eoVulnerabilitySecuritySupport	DATE		    Optional	Last date that Cisco engineering may release a planned maintenance release or scheduled software remedy for a security vulnerability issue. GMT date format YYYY-MM-DD.
            page	                        NUMBER		    Optional	Page number of the response.
            rows	                        NUMBER		    Optional	Number of rows of data per page.
            sort	                        STRING		    Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                        STRING		    Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/hardware-eol-bulletins'

        self.records = []   # Clear previous records before starting the new query

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_security_advisories(self, **kwargs) -> None:
        """
        Query Cisco Security Advisories API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	                Type	Max	Required	Description
                                                Length
            customerId	                NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	            STRING	25	Optional	Name of the inventory.
            hostname	                STRING	512	Optional	Host Name.
            swType	                    STRING	255	Optional	Software type.
            neInstanceId	            NUMBER	19	Optional	Unique id used to identify an instance of a network element. Network element is a manageable logical entity uniting one or more physical devices. This allows distributed devices to be managed in a unified way using one management system.
            hwInstanceId	            NUMBER		Optional	hardware instance ID.
            managedNeInstanceId	        NUMBER	32	Optional	The unique, generated ID of the network element.
            vulnerabilityStatus	        STRING	30	Optional	Vulnerability status of a Network element. Permitted Values: POTVUL, VUL.
            securityAdvisoryInstanceId	NUMBER		Optional	Internally generated ID for a security advisory.
            page	                    NUMBER		Optional	Page number of the response.
            rows	                    NUMBER		Optional	Number of rows of data per page.
            snapshot	                STRING		Optional	Option is "LATEST" and value is case insensitive. Report includes security advisory information for latest upload only.
            sort	                    STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                    STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/security-advisories'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_security_advisory_bulletins(self, **kwargs) -> None:
        """
        Query Cisco Security Advisory Bulletins API.

        Args:
            Parameter	                    Type	Max	    Required	Description
                                                    Length
            advisoryId	                    STRING	200	    Optional	Published identifier of a security advisory.
            securityAdvisoryInstanceId	    NUMBER	38	    Optional	Internally generated ID for a security advisory.
            bulletinFirstPublished	        DATE		    Optional	Date when the bulletin was first published to Cisco.com.
            bulletinLastUpdated	            DATE		    Optional	Date when the bulletin was last revised and published to Cisco.com. GMT date format YYYY-MM-DD.
            securityImpactRating	        STRING	12	    Optional	Security Impact Rating (SIR) for Cisco Security Advisories.
            cveId	                        STRING	1000	Optional	Common Vulnerabilities and Exposures (CVE) Identifier.
            bulletinTitle	                STRING	200	    Optional	The Cisco.com Title/Headline for the bulletin.
            page	                        NUMBER		    Optional	Page number of the response.
            rows	                        NUMBER		    Optional	Number of rows of data per page.
            sort	                        STRING		    Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                        STRING		    Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/security-advisory-bulletins'

        self.records = []   # Clear previous records before starting the new query

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_software_eol(self, **kwargs) -> None:
        """
        Query Cisco Software End Of Life API.

        The customer ID is automatically included from the instance's attribute,
        if present.

        Args:
            Parameter	            Type	Max	Required	Description
                                            Length
            customerId	            NUMBER	12	Required	Unique identifier of a Cisco customer.
            inventoryName	        STRING	25	Optional	Name of the inventory.
            neInstanceId	        NUMBER	19	Optional	Unique id used to identify an instance of a network element. Network element is a manageable logical entity uniting one or more physical devices. This allows distributed devices to be managed in a unified way using one management system.
            managedNeInstanceId	    NUMBER	32	Optional	The unique, generated ID of the network element.
            hostname	            NUMBER	512	Optional	Hostname of the Network Element.
            swType	                STRING	255	Optional	ype of software that is installed on this host/system. Common values include IOS, IOS XR, IOS-XE, NX-OS.
            currentSwEolMilestone	STRING	255	Optional	Latest software end-of-life milestone that has passed for the product. If more than one milestone falls on the same date, the returned value will be a comma-separated list. For example, EoSale, LDoS.
            nextSwEolMilestone	    STRING	255	Optional	Next software end-of-life milestone that is coming up. If more than one milestone falls on the same date, the returned value will be a comma-separated list. If the device is already LDoS it will not have a next milestone. Example: EoSale, LDoS.
            swVersion	            STRING	255	Optional	A version of operating system installed on the Network Element. Example: 15.1(4)M4.
            page	                NUMBER		Optional	Page number of the response.
            rows	                NUMBER		Optional	Number of rows of data per page.
            snapshot	            STRING		Optional	Option is "LATEST" and value is case insensitive. Report includes hardware EOL information for latest upload only.
            sort	                STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/software-eol'

        self.records = []   # Clear previous records before starting the new query

        # Ensure 'customerId' key is present in kwargs
        if 'customerId' not in kwargs:
            kwargs['customerId'] = self.customerId

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)

    def query_software_eol_bulletins(self, **kwargs) -> None:
        """
        Query Cisco Software End Of Life Bulletins API.

        Args:
            Parameter	                    Type	Max Required	Description
                                                    Length
            swEolInstanceId	                NUMBER	38	Optional	Unique identifier for software end-of-life entry in a data store.
            swMajorVersion	                STRING	50	Optional	Major version of the software version. For example, 15.1.
            swTrain	                        STRING	10	Optional	Form of software release schedule in, which a number of distinct series of versioned software releases for multiple products are released as a number of different trains on a regular schedule.
            swType	                        STRING	50	Optional	Type of software that is installed on this host/system. Common values include IOS, IOS XR, IOS-XE, NX-OS.
            bulletinNumber	                STRING	24	Optional	Cisco.com bulletin number for an End-of-Life bulletin.
            bulletinTitle	                STRING	200	Optional	The Cisco.com Title/Headline for the bulletin.
            eoLifeAnnouncementDate	        DATE		Optional	Date the document that announces the end-of-sale and end-of-life of a product is distributed to the general public. GMT date format YYYY-MM-DD.
            eoSaleDate	                    DATE		Optional	Last date to order the product through Cisco point-of-sale mechanisms. The product is no longer for sale after this date. GMT date format YYYY-MM-DD.
            eoSwMaintenanceReleasesDate	    DATE		Optional	Last date that Cisco engineering may release any final software maintenance releases or bug fixes. After this date, Cisco engineering will no longer develop, repair, maintain, or test the product software. GMT date format YYY.
            eoVulnerabilitySecuritySupport	DATE		Optional	Last date that Cisco Engineering may release a planned maintenance release or scheduled software remedy for a security vulnerability issue. GMT date format YYYY-MM-DD.
            lastDateOfSupport	            DATE		Optional	Last date to receive applicable service and support for the product as entitled by active service contracts or by warranty terms and conditions. After this date, all support services for the product will be unavailable and the product.
            page	                        NUMBER		Optional	Page number of the response.
            rows	                        NUMBER		Optional	Number of rows of data per page.
            sort	                        STRING		Optional	Supported sort criteria are either ‘asc’ for ascending or ‘desc’ for descending.
            fields	                        STRING		Optional	Requested fields in the response.
        """

        API_URL = 'https://apix.cisco.com/cs/api/v1/product-alerts/software-eol-bulletins'

        self.records = []   # Clear previous records before starting the new query

        resp = self.__send_query(API_URL, params=kwargs)
        self.__process_response(resp)

        # Play nice with Cisco API's and rate limit your queries
        time.sleep(0.5)
