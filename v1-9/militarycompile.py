from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from requests.exceptions import RequestException


# Function used to extract the units from column value and add it to the 

def modify_property_text_and_header(column_header, property_text):
    # Capture non-digit characters
    non_digit_strings = ''.join(re.findall(r'\D+', property_text)).strip()
    # Remove non-digit characters from property_text
    property_text_digits_only = re.sub(r'\D+', '', property_text)
    
    # If there are non-digit characters captured, append them to the column header
    if non_digit_strings:
        column_header_modified = f"{column_header} ({non_digit_strings})"
    else:
        column_header_modified = column_header
    
    return column_header_modified, property_text_digits_only

def fetch_and_extract_data(url, button_text):
    try:
        # Attempt to fetch the webpage content
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            webpage = response.content
            soup = BeautifulSoup(webpage, 'html.parser')
            # Continue with your scraping logic here...
            
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
            global category_filter
            button_text = button_text.replace(" [+]", "")
            category_filter[column_header_modified] = button_text

            # Convert the list to a DataFrame
            df = pd.DataFrame(rows, columns=['Country Name', column_header_modified])
            return df
        
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return None
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return None

'''
#----------- WORKS BELOW without FILTER ---------------

def fetch_and_extract_data(url):
    try:
        # Attempt to fetch the webpage content
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            webpage = response.content
            soup = BeautifulSoup(webpage, 'html.parser')
            # Continue with your scraping logic here...
            
            # Prepare a list to hold row data
            rows = []
            column_header = soup.find('h1', class_='textJumbo').text.strip()
            # Split the string at " by Country" and take the first part
            column_header = column_header.split(" by Country", 1)[0]

            # Iterate over each 'topRow' div
            for top_row in soup.find_all('div', class_='topRow'):
                country_name = top_row.select_one('span.textWhite.textLarge.textShadow').text.strip()
                property_text = top_row.select_one('span[style="background-color:#000; padding:3px 7px 3px 7px; border-bottom:thin solid #666;"]').text.strip()
                property_text = property_text.replace(",", "")  # Remove commas for thousands
                property_text = re.sub(r'\s+', ' ', property_text)

                
                column_header_modified, property_text_digits = modify_property_text_and_header(column_header, property_text)
                # Append this row of data to our list
                rows.append([country_name, property_text_digits])

            # Convert the list to a DataFrame
            
            df = pd.DataFrame(rows, columns=['Country Name', column_header_modified])

            return df
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return None
    except RequestException as e:
        print(f"Request failed: {e}")
        return None
'''

# ------------------- Main --------------

''' THIS IS USED TO EXTRACT 
final_df = None

#  Step 1: Fetch the main page 
url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'
response = requests.get(url)
base_url = 'https://www.globalfirepower.com'
soup = BeautifulSoup(response.content, 'html.parser')


# Step 2: Parse the main page for "picTrans" elements inside "contentSpecs" div and extract links
# Find all <div> elements with class "contentSpecs"
content_specs_divs = soup.find_all('div', class_='contentSpecs')

# Initialize an empty list to store the category links
category_links = []

# Iterate through each div found
for div in content_specs_divs:
    # Find all <a> elements with class "picTrans" within the current div
    categories = div.find_all('a', class_='picTrans')
    
    # If there are any such <a> elements, extend the category_links list with their 'href' attributes
    if categories:
        category_links.extend([category['href'] for category in categories if 'href' in category.attrs])

# Print the category_links list

for href in category_links:
    full_url = base_url.rstrip('/') + '/' + href.lstrip('/')
    #print(full_url)
    extracted_df = fetch_and_extract_data(full_url)

    if final_df is None:
        final_df = extracted_df
    else:
        #print(final_df)
        if extracted_df is not None:
            final_df = pd.merge(final_df, extracted_df, on='Country Name', how='outer', suffixes=('_left', '_right'))

# Ensure final_df is a DataFrame before attempting to fill NaN values
if final_df is not None:
   
    # Save the DataFrame to an Excel file
    final_df.to_excel('compiled_data.xlsx', index=False)
    final_df.to_csv('compiled_data.csv', index=False)
else:
    print("No data was extracted, final_df is None.")



'''

final_df = None

# Fetch the main page 
url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Required later when fetching the specific links
base_url = 'https://www.globalfirepower.com'


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
            # Append both the href and the button_text (as metadata) to your list
            category_links.append((href, button_text))

# Will be used to filter the table by category groups, this is why we needed button_text
category_filter = {}

# Need to process href and add it to the base url, open the full url and get the data
for href, button_text in category_links:
    full_url = base_url.rstrip('/') + '/' + href.lstrip('/')
    extracted_df = fetch_and_extract_data(full_url, button_text)

    if final_df is None:
        final_df = extracted_df
    else:
        if extracted_df is not None:
            final_df = pd.merge(final_df, extracted_df, on='Country Name', how='outer', suffixes=('_left', '_right'))


# Ensure final_df is a DataFrame before attempting to fill NaN values
if final_df is not None:
   
    # Save the DataFrame to an Excel file
    final_df.to_excel('compiled_data.xlsx', index=False)
    final_df.to_csv('compiled_data.csv', index=False)
else:
    print("No data was extracted, final_df is None.")



