import pandas as pd
from webscrapers.get_affiliations import addAffiliation
from webscrapers.get_globalfirepower import getGlobalFirepower
from webscrapers.get_nuclear import getNuclear
from datetime import datetime
import asyncio

# Main Function to create the table of military data

async def createTable(gfp_url, gfp_base_url, nuclear_url):
    
    # If Load was successful
    success = True
    # The result data frame
    final_df = None

    # Will be used to filter the table by category groups, this is why we needed button_text
    category_filter = {}

    # Hyperlink mapping between column names and urls
    column_hyperlinks = {}


    # Load data into dataframe from webscraping
    final_df, category_filter, column_hyperlinks = await addAffiliation(final_df, category_filter, column_hyperlinks)
    final_df, category_filter, column_hyperlinks = await getGlobalFirepower(final_df, category_filter, column_hyperlinks, gfp_url, gfp_base_url)
    final_df, category_filter, column_hyperlinks = await getNuclear(final_df, category_filter, column_hyperlinks, nuclear_url)
    

    if final_df is not None and len(final_df.columns) <= 2:
        df = pd.read_csv("../data/compiled_data.csv")
        final_df = df

    # Fill N/A only for 'affiliation' column
    if final_df is not None:
        final_df['Affiliation'] = final_df['Affiliation'].fillna('N/A')

    # Fill 0 for all remaining NaN values in the DataFrame
    final_df.fillna(0, inplace=True)

    # Used to create back-up files if can not connect to database. 

    '''
    if result[0] is not None:
    
        # Save the DataFrame to an Excel file
        result[0].to_excel('compiled_data.xlsx', index=False)
        result[0].to_csv('compiled_data.csv', index=False)
        
    
    else:
        print("No data was extracted, final_df is None.")
    '''

    return final_df, category_filter, column_hyperlinks

async def loadDatabase(db, gfp_url, gfp_base_url, nuclear_url, input_name):
    df, category_filter, column_hyperlinks = await createTable(gfp_url, gfp_base_url, nuclear_url)


    output_name = str(input_name).replace(" ", "-")
    collection = db[output_name]

    # Convert numeric columns to appropriate numeric types
    numeric_columns = df.columns.difference(['Country Name', 'Affiliation'])
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

    # Convert DataFrame to dictionary
    data_dict = df.to_dict(orient='list')

    # Create a dictionary with JSON strings for each column
    data = {
        'dataframe' : data_dict,
        'category_fitler': category_filter,
        'column_hyperlinks': column_hyperlinks
    }

    # Insert the document into the collection
    insert_result = collection.insert_one(data)

    # Check if the insertion was acknowledged
    if insert_result.acknowledged:
        print("Insertion was acknowledged by the server.")

    # Retrieve the unique identifier (_id) of the inserted document
    inserted_id = insert_result.inserted_id
    print("Inserted document ID:", inserted_id)

    return output_name


async def loadDatabaseCustom(db, df, category_filter, column_hyperlinks, input_name):
    output_name = str(input_name).replace(" ", "-")
    collection = db[output_name]

    # Convert numeric columns to appropriate numeric types
    numeric_columns = df.columns.difference(['Country Name', 'Affiliation'])
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

    # Convert DataFrame to dictionary
    data_dict = df.to_dict(orient='list')

    # Create a dictionary with JSON strings for each column
    data = {
        'dataframe' : data_dict,
        'category_fitler': category_filter,
        'column_hyperlinks': column_hyperlinks
    }

    # Insert the document into the collection
    insert_result = collection.insert_one(data)

    # Check if the insertion was acknowledged
    if insert_result.acknowledged:
        print("Insertion was acknowledged by the server.")

    # Retrieve the unique identifier (_id) of the inserted document
    inserted_id = insert_result.inserted_id
    print("Inserted document ID:", inserted_id)

    return output_name




    






