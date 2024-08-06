# cisco-support-service-api-query

A utility package which can be used to query Cisco's Support and Service API's

# Introduction

This repo provides utilities to work with Cisco's Support and Service  API's
for querying different information such as EoX records. Additional API end-points
will be added as time permits.

You will need to have your own API client key and secret with a grant type of
client_credentials.

Refer to [Cisco's API Documentation](https://developer.cisco.com/docs/support-apis/)
for complete details on how to register an application and obtain API keys.

# Example

An more complete example is provided provided in example.py, but a general workflow
of using these utilities can be seen as follows

```
from apix.apix_login import ApixLogin
from apix.apix_support import ApixSupport
from apix.apix_service import ApixService

# Replace with your own API key and secret
creds = ApixLogin("my_client_key", "my_client_secret")

support_api = ApixSupport(creds.auth_token)
support_api.eox_query_by_pid([' WS-C3750X-48PF-S','ISR4431/K9'])
print(support_api.records)

# Sometime later
creds.auth_still_valid()
support_api.eox_query_by_pid(['N5K-C5020P-BF','N5K-C5020-FAN', 'CISCO2851', 'NM-HDV2-1T1/E1'])
print(support_api.records)

support_api.sn2info_query_by_sn(['SN1','SN2','SN3'])
print("now SN2INFO")
print(support_api.records)

service_api = ApixService(creds.auth_token)
service_api.customerId = "1234"
service_api.query_hardware_inventory(inventoryName='inventory_name', hwType='Chassis')
print("now hardware")
print(service_api.records)

service_api.query_network_elements_inventory(inventoryName='inventory_name')
print("now network elements")
print(service_api.records)
```

# Cisco Support EoX API End-Point

The [Cisco Support EoX API end-point](https://developer.cisco.com/docs/support-apis/#!eox) allows you to query Cisco's Support API for end-of-life information. Their API
has a few end-points that allow you to query by

- Dates
- Product ID's
- Serial Numbers
- Software Release Strings

The apix.apix_support.py script currently permits querying EoX by hardware Product ID's and
deduplicates the list of PID's that are provided for more efficient API queries. Up
to 20 PID's can be included in each API call and the script maximizes this effort.

Upon querying Cisco's EoX API an EOXRecord(s) is returned. The apix.apix_support.py script
records this information in the self.records attribute as a list:

```
# Keys for each record are as follows
>>> eox.records[0].keys()
dict_keys(['EOLProductID', 'ProductIDDescription', 'ProductBulletinNumber', 'LinkToProductBulletinURL', 'EOXExternalAnnouncementDate', 'EndOfSaleDate', 'EndOfSWMaintenanceReleases', 'EndOfSecurityVulSupportDate', 'EndOfRoutineFailureAnalysisDate', 'EndOfServiceContractRenewal', 'LastDateOfSupport', 'EndOfSvcAttachDate', 'UpdatedTimeStamp', 'EOXMigrationDetails', 'EOXInputType', 'EOXInputValue'])

# An example record
>>> eox.records
[{'EOLProductID': 'WS-C3750X-48PF-S', 'ProductIDDescription': 'Catalyst 3750X 48 Port Full PoE IP Base', 'ProductBulletinNumber': 'EOL10623', 'LinkToProductBulletinURL': 'http://www.cisco.com/c/en/us/products/collateral/switches/catalyst-3560-x-series-switches/eos-eol-notice-c51-736139.html', 'EOXExternalAnnouncementDate': {'value': '2015-10-31', 'dateFormat': 'YYYY-MM-DD'}, 'EndOfSaleDate': {'value': '2016-10-30', 'dateFormat': 'YYYY-MM-DD'}, 'EndOfSWMaintenanceReleases': {'value': '2017-10-30', 'dateFormat': 'YYYY-MM-DD'}, 'EndOfSecurityVulSupportDate': {'value': '2019-10-30', 'dateFormat': 'YYYY-MM-DD'}, 'EndOfRoutineFailureAnalysisDate': {'value': '2017-10-30', 'dateFormat': 'YYYY-MM-DD'}, 'EndOfServiceContractRenewal': {'value': '2021-01-28', 'dateFormat': 'YYYY-MM-DD'}, 'LastDateOfSupport': {'value': '2021-10-31', 'dateFormat': 'YYYY-MM-DD'}, 'EndOfSvcAttachDate': {'value': '2017-10-30', 'dateFormat': 'YYYY-MM-DD'}, 'UpdatedTimeStamp': {'value': '2015-11-02', 'dateFormat': 'YYYY-MM-DD'}, 'EOXMigrationDetails': {'PIDActiveFlag': 'Y', 'MigrationInformation': 'Cisco Catalyst 3850 48 Port Full PoE IP Base', 'MigrationOption': 'Enter PID(s)', 'MigrationProductId': 'WS-C3850-48F-S', 'MigrationProductName': '', 'MigrationStrategy': '', 'MigrationProductInfoURL': 'http://www.cisco.com/c/en/us/products/switches/catalyst-3850-series-switches/index.html'}, 'EOXInputType': 'ShowEOXByPids', 'EOXInputValue': 'WS-C3750X-48PF-S '}]
```
# Cisco Support Serial Number to Information API End-Point

The [Cisco Support Serial Number to Information API end-point](https://developer.cisco.com/docs/support-apis/#!serial-number-to-information/introduction) allows you to query Cisco's Support API for information for specific serial numbers. Their API
has a few end-points that allow you to query for

- Coverage Status by Serial Number
- Coverage Summary by Serial Number
- Coverage Summary by Instance Number
- Orderable Product Identifier by Serial Number
- Owner Coverage Status by Serial Number

The apix.apix_support.py script currently permits querying coverage summary by serial number
and deduplicates the list of PID's that are provided for more efficient API queries. Up
to 75 serial numbers can be included in each API call and the script maximizes this effort.

# Cisco Service inventory API End-Point

The [Cisco service Inventory API end-point](https://developer.cisco.com/docs/service-apis/#!inventory/inventory) allows you to query Cisco's SService API for inventory information for specific Customer. Their API
has a few end-points that allow you to query for

- Hardware
- Network Elements
- Software

The apix.apix_service.py script currently permits querying hardware by Customer ID, inventory name
and hardware type.  It also permits querying network elements by Customer ID and inventory name.
