import pandas as pd
import re

# Function used to remove the units from column data and add it to the column header

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


# Function to merge new data frame from web scraping to the final data frame that is being merged

def mergeDataFrames(final_df, new_df):

    if new_df is None:
        return final_df
    
    if final_df is None:
        final_df = new_df
    else:
        if new_df is not None:
            # Identify common columns, excluding the merge key 'Country Name'
            common_cols = [col for col in new_df.columns if col in final_df.columns and col != 'Country Name']
            
            # Drop common columns from final_df before merging
            final_df = final_df.drop(columns=common_cols, errors='ignore')
            
            # Merge the dataframes without creating _left and _right suffixes
            final_df = pd.merge(final_df, new_df, on='Country Name', how='outer')

    return final_df