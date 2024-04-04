"""Example usage of Cisco Support API utilities
"""

import csv
from dotenv import dotenv_values
from apix.apix_login import ApixLogin
from apix.apix_support import ApixSupport


def main():
    """Example usage of Cisco Support API utilities

    This example requires a Cisco Support API client key and secret
    stored in a .env file in the current directory. These credentials
    are used to login to the Cisco Support API to obtain an authentication
    token, which is then used with the EoX API end-point. Two example
    Cisco PID's are used to show the use of the EoX API and the results
    are saved to a CSV file.
    """

    client_key = dotenv_values('.env')['CLIENT_KEY']
    client_secret = dotenv_values('.env')['CLIENT_SECRET']

    creds = ApixLogin(client_key, client_secret)
    support_api = ApixSupport(creds.auth_token)
    pids = ['WS-C3750X-48PF-S', 'C3KX-PWR-1100WAC', ]
    support_api.eox_query_by_pid(pids)

    FNAME = 'eox_report.csv'
    with open(FNAME, mode='w') as fhand:
        writer = csv.writer(fhand, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['EOLProductID',
                         'ProductIDDescription',
                         'LastDateOfSupport',
                         'EndOfSWMaintenanceReleases',
                         'EOXExternalAnnouncementDate',
                         'EndOfSaleDate',
                         'EndOfSecurityVulSupportDate',
                         'EndOfRoutineFailureAnalysisDate',
                         'EndOfServiceContractRenewal',
                         'EndOfSvcAttachDate',
                         'LinkToProductBulletinURL', ])
        for record in support_api.records:
            writer.writerow([record['EOLProductID'],
                             record['ProductIDDescription'],
                             record['LastDateOfSupport']['value'],
                             record['EndOfSWMaintenanceReleases']['value'],
                             record['EOXExternalAnnouncementDate']['value'],
                             record['EndOfSaleDate']['value'],
                             record['EndOfSecurityVulSupportDate']['value'],
                             record['EndOfRoutineFailureAnalysisDate']['value'],
                             record['EndOfServiceContractRenewal']['value'],
                             record['EndOfSvcAttachDate']['value'],
                             record['LinkToProductBulletinURL'], ])

    print(f'EOX records written to file {FNAME}')


if __name__ == "__main__":
    main()
