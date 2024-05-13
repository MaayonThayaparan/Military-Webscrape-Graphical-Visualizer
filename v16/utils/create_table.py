from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from requests.exceptions import RequestException
from webscrapers.get_affiliations import addAffiliation
from webscrapers.get_globalfirepower import getGlobalFirepower
from webscrapers.get_nuclear import getNuclear
import os


# Main Function to create the table of military data

def createTable(gfp_url, gfp_base_url, nuclear_url):
    
    # If Load was successful
    success = True
    # The result data frame
    final_df = None

    # Will be used to filter the table by category groups, this is why we needed button_text
    category_filter = {}

    # Hyperlink mapping between column names and urls
    column_hyperlinks = {}

    # Final object that will include data frame, category group mapping, and hyperlink mapping
    result = [final_df, category_filter, column_hyperlinks]

    # Load data into dataframe from webscraping
    result = addAffiliation(result)[0]
    result = getNuclear(result, nuclear_url)[0]
    #result = getGlobalFirepower(result, gfp_url, gfp_base_url)[0]

    if len(result[0].columns) <=2:
        df = pd.read_csv("../data/compiled_data.csv")
        result[0] = df
        success = False

    # Fill N/A only for 'affiliation' column
    if result[0] is not None:
        result[0]['Affiliation'] = result[0]['Affiliation'].fillna('N/A')

    # Fill 0 for all remaining NaN values in the DataFrame
    result[0].fillna(0, inplace=True)

    # Used to create back-up files if can not connect to database. 

    '''
    if result[0] is not None:
    
        # Save the DataFrame to an Excel file
        result[0].to_excel('compiled_data.xlsx', index=False)
        result[0].to_csv('compiled_data.csv', index=False)
        
    
    else:
        print("No data was extracted, final_df is None.")
    '''

    return result, success





    






