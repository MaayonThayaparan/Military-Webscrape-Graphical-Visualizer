import pandas as pd
from utils.helper_functions import *


# add Affiliation, would like to make this into a web crawl as well:

def addAffiliation(result):

    final_df = result[0]
    category_filter = result[1]
    column_hyperlinks = result[2]

   # DataFrames for NATO and BRICS countries
    aff = pd.DataFrame({
        'Country Name': [
            'Albania', 'Belgium', 'Bulgaria', 'Canada', 'Croatia', 'Czechia',
            'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece',
            'Hungary', 'Iceland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg',
            'Montenegro', 'Netherlands', 'North Macedonia', 'Norway', 'Poland',
            'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain', 'Sweden',
            'Turkiye', 'United Kingdom', 'United States',
            'Brazil', 'Russia', 'India', 'China', 'South Africa', 
            'Egypt', 'Ethiopia', 'Iran', 'United Arab Emirates'
        ],
        'Affiliation': ['NATO','NATO','NATO','NATO','NATO','NATO','NATO','NATO',
                        'NATO','NATO','NATO','NATO','NATO','NATO','NATO','NATO',
                        'NATO','NATO','NATO','NATO','NATO','NATO','NATO','NATO',
                        'NATO','NATO','NATO','NATO','NATO','NATO','NATO','NATO',
                        'BRICS','BRICS','BRICS','BRICS','BRICS','BRICS','BRICS','BRICS','BRICS'
        ]  
    })

 
    # Merging DataFrames
    final_df = mergeDataFrames(final_df, aff)
    
    result = [final_df, category_filter, column_hyperlinks]

    return result, True