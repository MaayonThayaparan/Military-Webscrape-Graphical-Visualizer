from utils.create_table import createTable
import pandas as pd
from pymongo import MongoClient
import tkinter as tk
from tkinter import ttk
from utils.helper_functions import convert_nested_df_to_json


#2024 (Current Load)
nuclear_url = 'https://fas.org/initiative/status-world-nuclear-forces/'
gfp_url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'
gfp_base_url = 'https://www.globalfirepower.com'


result = createTable(gfp_url, gfp_base_url, nuclear_url)[0]
df = result[0]
category_filter = result[1]
column_hyperlinks = result[2]

# Connect to MongoDB Atlas cluster
client = MongoClient("mongodb+srv://readwriteuser:e35BMIMnmYaOOgRG@cluster0.w1obusd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['military_data']
collection = db['2023']

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



