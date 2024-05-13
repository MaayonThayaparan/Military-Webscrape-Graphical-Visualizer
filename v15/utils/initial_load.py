from create_table import *
import pandas as pd
from pymongo import MongoClient
import tkinter as tk
from tkinter import ttk

#2021
gfp_url_2021 = 'https://web.archive.org/web/20210310190505/https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america' 
gfp_base_url_2021 = 'https://web.archive.org/web/20210715131940/https://www.globalfirepower.com/'
nuclear_url_2021 = 'https://web.archive.org/web/20230603062334/https://fas.org/web/20230603062334/https://fas.org/initiative/status-world-nuclear-forces/'

#2022
gfp_url_2022 = 'https://web.archive.org/web/20220602110022/https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america' 
gfp_base_url_2022 = 'https://web.archive.org/web/20220309082626/https://www.globalfirepower.com/'
nuclear_url_2022 = 'https://web.archive.org/web/20230603062334/https://fas.org/web/20230603062334/https://fas.org/initiative/status-world-nuclear-forces/'


#2023
gfp_url_2022 = 'https://web.archive.org/web/20230311214617/https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america' 
gfp_base_url_2022 = 'https://web.archive.org/web/20230306105107/https://www.globalfirepower.com/'
nuclear_url_2022 = 'https://web.archive.org/web/20230603062334/https://fas.org/web/20230603062334/https://fas.org/initiative/status-world-nuclear-forces/'

#2024 (Current Load)
nuclear_url = 'https://fas.org/initiative/status-world-nuclear-forces/'
gfp_url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'
gfp_base_url = 'https://www.globalfirepower.com'