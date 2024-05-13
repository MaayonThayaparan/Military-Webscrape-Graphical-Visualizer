from utils.load_data import createTable, loadDatabase
import pandas as pd
from pymongo import MongoClient
import tkinter as tk
from tkinter import ttk
from utils.helper_functions import convert_nested_df_to_json
import asyncio


# Connect to MongoDB Atlas cluster
client = MongoClient("mongodb+srv://readwriteuser:e35BMIMnmYaOOgRG@cluster0.w1obusd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['military_data']
collection = db['2023']

#2024 (Current Load)
nuclear_url = 'https://fas.org/initiative/status-world-nuclear-forces/'
gfp_url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'
gfp_base_url = 'https://www.globalfirepower.com'

async def loadData(): 
    word = await loadDatabase(db, gfp_url, gfp_base_url, nuclear_url, '2024-All-Data')
    print(word)

asyncio.run(loadData())



