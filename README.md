# Military-Webscrape-Graphical-Visualizer

## Description

This program webscrapes military data from various website and displays data in graphical/tabular format. This program is deployed on AWS via Docker at: http://3.131.168.18:8050


Some notable features:
- 3 graph types to visualize data
     - Bar: group by Country/Affiliation (x-axis) and select a category to visualize (y-axis). Additional option to sort.
     - Pie: group by Country/Affiliation and select a category to visualize.
     - Multi-bar: group by Country/Affiliation (x-axis) and select a category group to visualize (y-axis). 
- Table Features:
     - Table is fully editable and will edited data will be displayed in the graph (shortcut to 'Reset' data available). 
     - Selected or filtered rows are what will display in graph (shortcuts for 'Select All', 'Deselect All', and 'First 10' (respects current sort).
     - Can filter rows using boolean operators. 
     - Can save custom table to database, can delete custom tables as well.
- Database Features:
     - Data loaded from MongoDB Atlas.
     - Aftering editing table, can save custom table to MongoDB for later selection using 'Save Custom Table to Database' button. 
     - Can initiate a fresh webscrape instance by clicking on 'Webscrape New Collection' which will also save to database.
     - Option to delete database will be displayed when custom database is being displayed (future enhancement to add Google Auth/sign-in so you can only view and delete your own custom databases). 
     - Since data is webscraped, there is potential for webscraping logic of the DOM to get out of date. All source links are presented if source references need to be identified for DOM structure. 

![image](https://github.com/MaayonThayaparan/Military-Webscrape-Graphical-Visualizer/assets/43158629/8c8f6b06-fe17-48a1-b665-53ffe6675449)
![image](https://github.com/MaayonThayaparan/Military-Webscrape-Graphical-Visualizer/assets/43158629/5224fb59-7220-4980-89f2-1c5a197eb60c)







