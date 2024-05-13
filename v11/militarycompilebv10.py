from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from requests.exceptions import RequestException
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context, no_update
from collections import defaultdict
from dash.dependencies import Input, Output, ClientsideFunction
import json


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


# Function to merge new data frame from web scraping to the final data frame that is being merged

def mergeDataFrames(final_df, new_df):
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

# Function to get all categories from globalfirewpower website

def getGlobalFirepower(result):

    final_df = result[0]
    category_filter = result[1]
    column_hyperlinks = result[2]

    # Main webpage to retrieve all category links
    url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'

    # Required later when fetching the specific links
    base_url = 'https://www.globalfirepower.com'

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
                final_df = mergeDataFrames(final_df, extracted_df)

            result = [final_df, category_filter, column_hyperlinks]

            return result
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return None
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return None
    
# Function to webscrape and get Nuclear data

def getNuclear(result):

    final_df = result[0]
    category_filter = result[1]
    column_hyperlinks = result[2]

    url = 'https://fas.org/initiative/status-world-nuclear-forces/'

    try:
        # Attempt to fetch the webpage content
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            webpage = response.content
            soup = BeautifulSoup(webpage, 'html.parser')
            

            # Parse the table (Adjust the selector as needed)
            table = soup.find('table', {'id': 'tablepress-2'})

            # Extract data and create a DataFrame
            rows = []
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    rows.append([col.text for col in cols])

            df = pd.DataFrame(rows, columns=['Country', 'Deployed Strategic', 'Deployed Nonstrategic', 'Reserve/Nondeployed', 'Military Stockpile', 'Total Inventory'])

            #Filter, rename, and clean data
            col_name = "Total Nuclear Weapons"
            df = df[['Country', 'Total Inventory']].rename(columns={'Country': 'Country Name', 'Total Inventory': col_name})
            df['Total Nuclear Weapons'] = df['Total Nuclear Weapons'].apply(lambda x: re.sub(r'\D', '', x))

            # Exclude 'Totals' row
            df = df[df['Country Name'] != 'Totals']

            # Will update the category filter to filter the table
            category_filter[col_name] = "NUCLEAR"  

            # Update column name : hyperlink mapping
            column_hyperlinks[col_name] = url

            # Merge new data frame with the existing

            final_df = mergeDataFrames(final_df, df)

            result = [final_df, category_filter, column_hyperlinks]

            return result
        
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
            return None
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return None

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

    return result



# Main Function to create the table of military data

def createTable():
    
    # The result data frame
    final_df = None

    # Will be used to filter the table by category groups, this is why we needed button_text
    category_filter = {}

    # Hyperlink mapping between column names and urls
    column_hyperlinks = {}

    # Final object that will include data frame, category group mapping, and hyperlink mapping
    result = [final_df, category_filter, column_hyperlinks]

    # Load data into dataframe from webscraping
    result = addAffiliation(result)
    result = getNuclear(result)
    result = getGlobalFirepower(result)

    # Fill N/A only for 'affiliation' column
    if result[0] is not None:
        result[0]['Affiliation'] = result[0]['Affiliation'].fillna('N/A')

    # Fill 0 for all remaining NaN values in the DataFrame
    result[0].fillna(0, inplace=True)
    

    # DEBUG
    #print(category_filter)
    #print(column_hyperlinks)

    # Ensure final_df is a DataFrame before attempting to fill NaN values
    if result[0] is not None:
    
        # Save the DataFrame to an Excel file
        result[0].to_excel('compiled_data.xlsx', index=False)
        result[0].to_csv('compiled_data.csv', index=False)
        
    
    else:
        print("No data was extracted, final_df is None.")
        
    return result

# ----------------------------------- DASH ---------------------------------------------------

result = createTable() 
df = result[0]
category_filter = result[1]
column_hyperlinks = result[2]
print(column_hyperlinks)


columns = []
for col in df.columns:
    # Determine if the column should be treated as numeric
    if col not in ['Country Name', 'Affiliation']:
        df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert column to numeric
        col_type = "numeric"
    else:
        col_type = "text"

    # Define the column settings for Dash DataTable
    columns.append({
        "name": col, 
        "id": col,
        "editable": True,  # Allow editing
        "selectable": True,  # Allow selection
        "type": col_type,
        "presentation": "markdown" if col in column_hyperlinks else None
    })

# We invert the mapping to get groups to list of column names NOTE:need to fix this later, to avoid redundant step 
group_to_columns = defaultdict(list)
for column, group in category_filter.items():
    group_to_columns[group].append(column)


# Dropdown for selecting group on table
group_selector_dropdown = dcc.Dropdown(
    id='group-selector-dropdown',
    options=[{'label': group, 'value': group} for group in group_to_columns.keys()],
    value=None,  # Default value
    multi=False,  # Allow selecting only one group
    placeholder="Select a Category (to group similar columns)"
)

# Dropdown for selecting group for multi-bar-graph
group_selector_dropdown_multibar = dcc.Dropdown(
    id='group-selector-dropdown-multibar',
    options=[{'label': group, 'value': group} for group in group_to_columns.keys()],
    value=None,  # Default value
    multi=False,  # Allow selecting only one group
    placeholder="Select a Category (to group similar columns)"
)

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    dcc.Dropdown(
        id='graph-type-dropdown',
        options=[
            {'label': 'Bar Graph', 'value': 'bar'},
            {'label': 'Pie Chart', 'value': 'pie'},
            {'label': 'Multi-Bar Graph', 'value': 'multi-bar'}
        ],
        value='bar',  # Default to bar graph
        style={'width': '300px', 'margin': '10px'}
    ),
    dcc.Dropdown(
        id='x-axis-selector-dropdown',
        options=[{'label': col, 'value': col} for col in df.columns if col in ['Country Name', 'Affiliation']],
        value='Country Name',  # Default to 'Country Name'
        style={'width': '300px', 'margin': '10px'},  # Initially visible
        placeholder="Select X-axis"
    ),
    dcc.Dropdown(
        id='y-axis-selector-dropdown',
        options=[{'label': col, 'value': col} for col in df.columns if col not in ['Country Name', 'Affiliation']],
        value=df.columns[2],  # Assume some default
        style={'width': '300px', 'margin': '10px', 'display': 'none'},  # Initially hidden
        placeholder="Select Y-axis"
    ),
    html.Div(
        id='sort-direction-dropdown-container',
        children=dcc.Dropdown(
            id='sort-direction-dropdown',
            options=[
                {'label': 'Ascending', 'value': 'asc'},
                {'label': 'Descending', 'value': 'desc'}
            ],
            value='desc',
            style={'width': '300px', 'margin': '10px'}
        ),
        style={'display': 'none'}  # Initially hidden
    ),
    dcc.Dropdown(
        id='group-selector-dropdown-multibar',
        options=[{'label': group, 'value': group} for group in group_to_columns.keys()],
        value=None,
        multi=False,
        placeholder="Select a Category Group for Multi-Bar Graph",
        style={'width': '300px', 'margin': '10px', 'display': 'none'}  # Initially hidden
    ),
    html.Button('Create Graph', id='create-graph-button', n_clicks=0, style={'margin': '10px'}),
    html.Div(id='graph-output', style={'margin': '20px'}),
    html.Hr(),
    html.H3('Data Table', style={'margin': '10px'}),
    html.Button('Reset Data', id='reset-button', n_clicks=0, style={'margin': '10px'}),
    html.Button('Select All', id='select-all-button', n_clicks=0),
    html.Button('Deselect All', id='deselect-all-button', n_clicks=0),
    group_selector_dropdown,
    dash_table.DataTable(
        id='datatable',
        columns=columns,
        data=df.to_dict('records'),
        editable=True,  # Ensure global editability
        row_selectable='multi',  # Enable row selection
        selected_rows=[],  # No rows are selected by default
        sort_action='native',  # Enable sorting
        filter_action='native',  # Enable filtering
        page_action='none',  # Show all rows
        style_cell={'textAlign': 'left', 'padding': '5px'},  # Left align cell content
        style_header={'textAlign': 'left', 'fontWeight': 'bold', 'padding': '5px'}, # Left align headers and make them bold
        sort_by=[{"column_id": df.columns[2], "direction": "desc"}]  # Default sorting
    )
   
    
])

@app.callback(
    [
        Output('x-axis-selector-dropdown', 'style'),
        Output('y-axis-selector-dropdown', 'style'),
        Output('sort-direction-dropdown-container', 'style'),
        Output('group-selector-dropdown-multibar', 'style')
    ],
    [Input('graph-type-dropdown', 'value')]
)
def update_ui_visibility(graph_type):
    if graph_type == 'multi-bar':
        # Show only the X-axis selector and the multi-bar group selector
        return (
            {'display': 'block'},  # X-axis selector
            {'display': 'none'},   # Y-axis selector
            {'display': 'none'},   # Sort direction selector
            {'display': 'block'}   # Multi-bar group selector
        )
    if graph_type == "bar":
        # Show X-axis, Y-axis, and sort direction selectors for bar and pie graphs
        return (
            {'display': 'block'},  # X-axis selector
            {'display': 'block'},  # Y-axis selector
            {'display': 'block'},  # Sort direction selector
            {'display': 'none'}    # Multi-bar group selector
        )
    if graph_type == "pie":
        # Show X-axis, Y-axis, and sort direction selectors for bar and pie graphs
        return (
            {'display': 'block'},  # X-axis selector
            {'display': 'block'},  # Y-axis selector
            {'display': 'none'},  # Sort direction selector
            {'display': 'none'}    # Multi-bar group selector
        )


@app.callback(
    Output('graph-output', 'children'),
    [Input('create-graph-button', 'n_clicks'),
     Input('group-selector-dropdown-multibar', 'value'),
     Input('sort-direction-dropdown', 'value')],
    [State('datatable', 'derived_virtual_data'),
     State('datatable', 'derived_virtual_selected_rows'),
     State('graph-type-dropdown', 'value'),
     State('x-axis-selector-dropdown', 'value'),
     State('y-axis-selector-dropdown', 'value')]
)
def update_graph(n_clicks, selected_group, sort_direction, virtual_data, selected_rows, graph_type, x_axis_selection, y_axis_selection):
    if not n_clicks or virtual_data is None:
        return html.Div("Click the button to generate the graph or no data to display.")

    df_current_view = pd.DataFrame(virtual_data)

    # Convert all values in the x_axis_selection column to string to avoid comparison error
    df_current_view[x_axis_selection] = df_current_view[x_axis_selection].astype(str)

    if selected_rows is not None and len(selected_rows) > 0:
        df_filtered = df_current_view.iloc[selected_rows, :]
    else:
        df_filtered = df_current_view

    if y_axis_selection != 'Affiliation':
        df_filtered[y_axis_selection] = pd.to_numeric(df_filtered[y_axis_selection], errors='coerce').fillna(0)

    if graph_type == 'multi-bar' and selected_group:
        group_columns = group_to_columns[selected_group]
        # Sum the data for each x-axis category
        df_to_plot = df_filtered.groupby(x_axis_selection)[group_columns].sum().reset_index()
        fig = px.bar(df_to_plot, x=x_axis_selection, y=group_columns, barmode='group', title="Multi-Bar Graph")
        return dcc.Graph(figure=fig)

    if graph_type == 'bar':
        # Sum the data for each x-axis category if needed
        if y_axis_selection != 'Affiliation':
            df_to_plot = df_filtered.groupby(x_axis_selection)[y_axis_selection].sum().reset_index()
        else:
            df_to_plot = df_filtered

        # Sorting, if applicable
        if y_axis_selection != 'Affiliation':
            is_ascending = sort_direction == 'asc'
            df_to_plot = df_to_plot.sort_values(by=y_axis_selection, ascending=is_ascending)
        fig = px.bar(df_to_plot, x=x_axis_selection, y=y_axis_selection, title="Bar Graph")
        return dcc.Graph(figure=fig)

    elif graph_type == 'pie':
        fig = px.pie(df_filtered, names=x_axis_selection, values=y_axis_selection, title="Pie Chart")
        return dcc.Graph(figure=fig)

    else:
        return html.Div('Invalid graph type selected.')

    return dcc.Graph(figure=fig)


# Call back to update table

@app.callback(
    Output('datatable', 'columns'),
    [Input('group-selector-dropdown', 'value')]
)
def update_table_columns(selected_group):
    if selected_group:
        # Get the columns for the selected group
        columns_for_group = group_to_columns[selected_group]
        # Filter and return columns that are in the selected group
        return [{"name": col, "id": col} for col in df.columns if col in columns_for_group or col == 'Country Name' or col == 'Affiliation']
    else:
        # If no group is selected, show all columns
        return [{"name": col, "id": col} for col in df.columns]
    
# Reset the table back to original data if edited
@app.callback(
    Output('datatable', 'data'),
    [Input('reset-button', 'n_clicks')],
    prevent_initial_call=True  # Prevents the callback from firing upon the initial load
)
def reset_table(n_clicks):
    return df.to_dict('records')


# Place this in an external JS file under the assets folder
app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_header_links'
    ),
    Output('dummy-output', 'children'),
    [Input('datatable', 'derived_virtual_data')],
    [State('column-links-store', 'data')]
)

@app.callback(
    Output('datatable', 'selected_rows'),
    [Input('select-all-button', 'n_clicks'),
     Input('deselect-all-button', 'n_clicks')],
    [State('datatable', 'data')]
)
def update_selected_rows(select_all_clicks, deselect_all_clicks, rows):
    if not callback_context.triggered:
        return no_update

    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'select-all-button':
        return list(range(len(rows)))
    elif button_id == 'deselect-all-button':
        return []

    return no_update


if __name__ == '__main__':
    app.run_server(debug=True)

