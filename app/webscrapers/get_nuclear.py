from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from requests.exceptions import RequestException
from utils.helper_functions import *
from urllib.parse import urlparse

# Function to webscrape and get Nuclear data

async def getNuclear(final_df, category_filter, column_hyperlinks, url):

    try:
        # Attempt to fetch the webpage content
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            webpage = response.content
            soup = BeautifulSoup(webpage, 'html.parser')

            # -------------- Get Headers -------------- #

            # find the table that has the header names
            table_headers = soup.find('table', class_='tablepress tablepress-id-2')

            column_headers = []

            # Check if the table_headers is not None to avoid AttributeError
            if table_headers:
                # Extract all <th> elements within the <thead>
                head = table_headers.find('thead')
                headers = [th.get_text(strip=True) for th in head.find_all('th')]
                
                # Create a list of headers, adjusting based on specified rules
                column_headers = [
                    "Country Name" if header == "Country" else f"Nuclear - {header}"
                    for header in headers
                ]
            else:
                column_headers = []
            

            # -------------- Get Rows  -------------- #
                    
            # Parse the table (Adjust the selector as needed)
            table = soup.find('table', {'id': 'tablepress-2'})

            # Extract data and create a DataFrame
            rows = []
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    rows.append([col.text for col in cols])

            '''
            Code for only Total Nuclear

            df = pd.DataFrame(rows, columns=['Country', 'Deployed Strategic', 'Deployed Nonstrategic', 'Reserve/Nondeployed', 'Military Stockpile', 'Total Inventory'])

            #Filter, rename, and clean data
            col_name = "Total Nuclear Weapons"
            df = df[['Country', 'Total Inventory']].rename(columns={'Country': 'Country Name', 'Total Inventory': col_name})
            df['Total Nuclear Weapons'] = df['Total Nuclear Weapons'].apply(lambda x: re.sub(r'\D', '', x))

            # Exclude 'Totals' row
            df = df[df['Country Name'] != 'Totals']

            # Will update the category filter to filter the table
            category_filter[col_name] = "NUCLEAR"  

            # Update column name : hyperlink mapping
            column_hyperlinks[col_name] = url
            '''
            # Create dataframe using rows and headers
            df = pd.DataFrame(rows, columns=column_headers)

            # Remove non-digit characters from all rows except 'Country Name'. 

            # Clean non-digit characters from all columns except 'Country Name', add hyperlinks and column groupings
            for col in df.columns:
                if col != 'Country Name':
                    df[col] = df[col].apply(lambda x: re.sub(r'\D', '', x))

            # Exclude 'Totals' row
            df = df[df['Country Name'] != 'Totals']

            # Make blanks to zero
            df.replace(['', 'NA', None], 0, inplace=True)

            # Setup Hyperlinks and groups
            for col in column_headers:
                if col != 'Country Name':
                    column_hyperlinks[col] = url
                    category_filter[col] = 'NUCLEAR'

            # Merge new data frame with the existing

            final_df = mergeDataFrames(final_df, df)


            return final_df, category_filter, column_hyperlinks
        
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return final_df, category_filter, column_hyperlinks
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return final_df, category_filter, column_hyperlinks
    