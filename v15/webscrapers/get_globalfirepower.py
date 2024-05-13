from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from requests.exceptions import RequestException
from utils.helper_functions import *

# Function to get all categories from globalfirewpower website

def getGlobalFirepower(result, url, base_url):

    final_df = result[0]
    category_filter = result[1]
    column_hyperlinks = result[2]

    try:
        # Attempt to fetch the webpage content
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            webpage = response.content
            soup = BeautifulSoup(webpage, 'html.parser')

            # Retrieve all links
            category_links = []
            category_links = getCategoryLinksWithGroup(soup)

            # If web scraping by category groups fails, try to attempt webscraping 'Overview' section
            if category_links == []:
                category_links = getCategoryLinks(soup)

            # Need to process href and add it to the base url, open the full url and get the data
            for href, button_text in category_links:
                full_url = base_url.rstrip('/') + '/' + href.lstrip('/')
                extracted_df = fetch_and_extract_data(full_url, button_text, category_filter, column_hyperlinks)

                # Merge new data frame with the existing
                if extracted_df is not None:
                    final_df = mergeDataFrames(final_df, extracted_df)

            result = [final_df, category_filter, column_hyperlinks]

            return result, True
        
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return result, False
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return result, False


# Function used to extract country data per category

def fetch_and_extract_data(url, button_text, category_filter, column_hyperlinks):
    try:
        # Attempt to fetch the webpage content
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            webpage = response.content
            soup = BeautifulSoup(webpage, 'html.parser')
            
            # Prepare a list to hold row data
            rows = []
            column_header = soup.find('h1', class_='textJumbo').text.strip()

            # Split the string at " by Country" and take the first part
            column_header = column_header.split(" by Country", 1)[0]

            # Iterate over each 'topRow' div
            for top_row in soup.find_all('div', class_='topRow'):
                country_name = top_row.select_one('span.textWhite.textLarge.textShadow').text.strip() # Extracts the country name
                property_text = top_row.select_one('span[style="background-color:#000; padding:3px 7px 3px 7px; border-bottom:thin solid #666;"]').text.strip() # Extracts the value
                property_text = property_text.replace(",", "")  # Remove commas for thousands
                property_text = re.sub(r'\s+', ' ', property_text)

                # Function to add the units from the property text into the column header
                column_header_modified, property_text_digits = modify_property_text_and_header(column_header, property_text)

                # Append this row of data to our list
                rows.append([country_name, property_text_digits])

            # Will update the category filter to filter the table
            button_text = button_text.replace(" [+]", "")
            category_filter[column_header_modified] = button_text   

            # Update column name : hyperlink mapping
            column_hyperlinks[column_header_modified] = url


            # Convert the list to a DataFrame
            df = pd.DataFrame(rows, columns=['Country Name', column_header_modified])
            return df
        
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return None
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return None

# ------------------- Main --------------


def getCategoryLinksWithGroup(soup):

    '''
    DOM Structure:
    - DOM MODEL: div: contentSpecs that is AFTER button : collapsible --> div: specsGenContainers picTrans3 zoom --> href
    - Variables: buttons --> content_spec_divs (that is after buttons) --> button_content_pairs (has both button and content_spec_div pair) --> categories --> href
    - 'button' element of class 'collapsible' (Need this to get the category group)
    - 'div element of class 'contentSpecs' that is next to above button element
    - in 'contentSpecs' need the 'div' element of class 'specsGenContainers picTrans3 zoom' which is the category (this has the links)
    - in 'categories', will extract the href link, add it to the base, and then extract country data for the category using in df format. Will merge this df into final_df
    '''

    # Initialize a list to hold your button text (the category group 'button_text) and all included categories ('content_specs_div')
    button_content_pairs = []

    # Find all buttons with class 'collapsible'
    buttons = soup.find_all('button', class_='collapsible')

    for button in buttons:
        # Capture the button's text
        button_text = button.text.strip()
        
        # Find the immediately following 'contentSpecs' div for the button
        content_specs_div = button.find_next('div', class_='contentSpecs')
        
        # Combine the button text with the 'contentSpecs' div for further processing
        button_content_pairs.append((button_text, content_specs_div))

    category_links = []

    for button_text, content_specs_div in button_content_pairs:

        # Find all <div> elements with class "specsGenContainers picTrans3 zoom" within the content_specs_div
        categories = content_specs_div.find_all('div', class_='specsGenContainers picTrans3 zoom')
        
        # For each category, check if its parent is an 'a' tag and if so, get the href
        for category in categories:
            parent_a = category.find_parent('a')
            if parent_a and 'href' in parent_a.attrs:
                href = parent_a['href']
                # Append both the href and the button_text (as metadata) to category links
                category_links.append((href, button_text))

    return category_links


def getCategoryLinks(soup):

    '''
    DOM Structure
    - DOM Model: div: contentSpecs --> div: picTrans --> a --> extract href
    - Variables: content_spec_divs --> categories    --> href
    - content_spec_divs: 'Overview' section is in 'div' element with 'contentSpecs' class
    - categories: are in 'div' elements with 'picTrans' class
    '''

    # Initialize an empty list to store the category links
    category_links = []

    # Parse the main page for "picTrans" elements inside "contentSpecs" div and extract links

    # Find all <div> elements with class "contentSpecs"
    content_specs_divs = soup.find_all('div', class_='contentSpecs')

    # Iterate through each div found
    for div in content_specs_divs:
        # Find all <a> elements with class "picTrans" within the current div
        categories = div.find_all('a', class_='picTrans')
        
        # If there are any such <a> elements, extend the category_links list with their 'href' attributes. Added "ALL" which can be used as category group. 
        if categories:
            category_links.extend([(category['href'], "ALL") for category in categories if 'href' in category.attrs])

    return category_links


