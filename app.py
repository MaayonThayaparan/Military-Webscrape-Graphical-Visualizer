import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context, no_update
from collections import defaultdict
from dash.dependencies import Input, Output, ClientsideFunction
from utils.load_data import createTable, loadDatabase, loadDatabaseCustom
from pymongo import MongoClient
from dash.exceptions import PreventUpdate
import json
import dash_bootstrap_components as dbc
import asyncio
import os
from dotenv import load_dotenv
from io import StringIO


# Connect to MongoDB Atlas cluster
database_url = os.getenv("DATABASE_URL")
database_name = os.getenv("DATABASE_NAME")
client = MongoClient("mongodb+srv://readwriteuser:e35BMIMnmYaOOgRG@cluster0.w1obusd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["military_data"]


# ----------------------------------- DASH ---------------------------------------------------


# URL for the Bootstrap CSS CDN (using Bootstrap 5 for this example)
bootstrap_cdn_url = "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[bootstrap_cdn_url], serve_locally=True)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='store-df'),
    dcc.Store(id='store-category-filter'),
    dcc.Store(id='store-column-hyperlinks'),
    dcc.Store(id='store-columns'),
    dcc.Store(id='store-group-to-columns'),
    dcc.Store(id='store-group-selector-dropdown'),
    dcc.Store(id='store-group-selector-dropdown-multi'),
    html.Div([
        html.H1('Webscraped Military Strength Graph', className='text-center mt-4'),
        html.Div(className='mt-4'),  # Adding margin-top space
        html.Div(className='row align-items-end', children=[
            html.Div(className='col-md-2', children=[
                html.Label('Select Database Collection:', htmlFor='collection-selector-dropdown'),
                dcc.Dropdown(
                    id='collection-selector-dropdown',
                    options=[{'label': collection, 'value': collection} for collection in db.list_collection_names()],
                    value=None,
                    placeholder="Select...",
                    className='form-select'
                )
            ]),
            html.Div(className='col-md-4', children=[
                html.Div(className='row', children=[
                    html.Div(className='col', id='webscrape-button-div', style={'display': 'none'}, children=[
                        html.Button('Webscrape New Collection', id='webscrape-button', className='btn btn-primary me-2')
                    ]),
                    html.Div(className='col', id='save-custom-table-button-div', style={'display': 'none'}, children=[
                        html.Button('Save Custom Table to Database', id='save-custom-table-button', className='btn btn-success')
                    ])
                ])
            ]),
           html.Div(className='col-md-2', children=[
                html.Div(className='row', children=[
                    html.Div(className='col', id='delete-collection-button-div', style={'display': 'none'}, children=[
                        html.Button('Delete Selected Custom Collection', id='delete-collection-button', className='btn btn-danger')
                    ])
                ])
            ])
        ]),
        html.Div(className='mt-4'),  # Adding margin-top space
        html.Div(id='dynamic-content')
    ], className='container py-4'),
    dbc.Modal(
        id='modal-webscrape',
        is_open=False,
        children=[
            dbc.ModalBody([
                dbc.Input(id='instance-name', type='text', placeholder='Name Instance', className='mb-2'),
                dbc.Button('Submit', id='submit-instance', className='btn btn-success'),
                dcc.Loading(id="loading-area", children=[html.Div(id='loading-output')], type="default")
            ])
        ]
    ),
    dbc.Modal(
        id='modal-custom',
        is_open=False,
        children=[
            dbc.ModalBody([
                dbc.Input(id='instance-name-custom', type='text', placeholder='Name Instance', className='mb-2'),
                dbc.Button('Submit', id='submit-instance-custom', className='btn btn-success'),
                dcc.Loading(id="loading-area-custom", children=[html.Div(id='loading-output-custom')], type="default")
            ])
        ]
    ),
    dbc.Modal(
        id='modal-delete-collection',
        is_open=False,
        children=[
            dbc.ModalHeader('Delete Collection'),
            dbc.ModalBody('Are you sure you want to delete the selected collection?'),
            dbc.ModalFooter([
                dbc.Button('Cancel', id='close-delete-button', className='btn btn-secondary'),
                dbc.Button('Delete', id='confirm-delete-button', className='btn btn-danger')
            ]),
            dcc.Loading(id="loading-area-delete", children=[html.Div(id='loading-output-delete')], type="default")
        ]
    )
], className='bg-light')

def retrieve_data(selected_collection):
    collection = db[selected_collection]
    document = collection.find_one({})

    # Retrieve required components from the collection
    data_dict = document['dataframe']
    df = pd.DataFrame(data_dict)
    category_filter = document['category_fitler']
    column_hyperlinks = document['column_hyperlinks']

    return df, category_filter, column_hyperlinks


@app.callback(
    [
        Output('dynamic-content', 'children'),
        Output('store-df', 'data'),
        Output('store-category-filter', 'data'),
        Output('store-column-hyperlinks', 'data'),
        Output('store-columns', 'data'),
        Output('store-group-to-columns', 'data'),
        Output('store-group-selector-dropdown', 'data'),
        Output('store-group-selector-dropdown-multi', 'data')
    ],
    Input('collection-selector-dropdown', 'value')
)

def update_content(value):

    df, category_filter, column_hyperlinks = retrieve_data(str(value))

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

    # Prepare DataFrame for JSON serialization
    df_json = df.to_json(date_format='iso', orient='split')
    category_filter_json = json.dumps(category_filter)
    column_hyperlinks_json = json.dumps(column_hyperlinks)
    regular_dict = dict(group_to_columns)
    group_to_columns_json = json.dumps(regular_dict)
    columns_json = json.dumps(columns)
    dropdown_options = [{'label': group, 'value': group} for group in group_to_columns.keys()]
    dropdown_data = {
        'options': dropdown_options,
        'value': None,
        'placeholder': "Select a Category (to group similar columns)",
        'multi': False
    }
    group_selector_dropdown_json = json.dumps(dropdown_data)
    group_selector_dropdown__multibar_json = json.dumps(dropdown_data)


    htmlDiv =   html.Div(children=[
                    html.Div(className='row align-items-end', children=[
                        html.Div(className='col-md-2', children=[
                            html.Label('Graph Type:', htmlFor='graph-type-dropdown'),
                            dcc.Dropdown(
                                id='graph-type-dropdown',
                                options=[
                                    {'label': 'Bar Graph', 'value': 'bar'},
                                    {'label': 'Pie Chart', 'value': 'pie'},
                                    {'label': 'Multi-Bar Graph', 'value': 'multi-bar'}
                                ],
                                value='bar',
                                className='form-select'
                            )
                        ]),
                        html.Div(id='x-axis-selector-dropdown-div', className='col-md-2', children=[
                            html.Label('Country Grouping:', htmlFor='x-axis-selector-dropdown'),
                            dcc.Dropdown(
                                id='x-axis-selector-dropdown',
                                options=[{'label': 'Country', 'value': 'Country Name'}] + [{'label': col, 'value': col} for col in df.columns if col == 'Affiliation'],
                                value='Country Name',
                                className='form-select'
                            )
                        ]),
                        html.Div(id='y-axis-selector-dropdown-div', className='col-md-4', children=[
                            html.Label('Category:', htmlFor='y-axis-selector-dropdown'),
                            dcc.Dropdown(
                                id='y-axis-selector-dropdown',
                                options=[{'label': col, 'value': col} for col in df.columns if col not in ['Country Name', 'Affiliation']],
                                value=df.columns[2],
                                className='form-select'
                            )
                        ]),
                        html.Div(id='sort-direction-dropdown-div', className='col-md-4', children=[
                            html.Label('Sort:', htmlFor='sort-direction-dropdown'),
                            dcc.Dropdown(
                                id='sort-direction-dropdown',
                                options=[
                                    {'label': 'Ascending', 'value': 'asc'},
                                    {'label': 'Descending', 'value': 'desc'}
                                ],
                                value='desc',
                                className='form-select'
                            )
                        ]),
                        html.Div(id='group-selector-dropdown-multibar-div', className='col-md-4', children=[
                            html.Label('Category Grouping:', htmlFor='group-selector-dropdown-multibar'),
                            dcc.Dropdown(
                                id='group-selector-dropdown-multibar',
                                options=[{'label': group, 'value': group} for group in group_to_columns.keys()],
                                className='form-select'
                            )
                        ])
                    ]),
                    html.Button('Create Graph', id='create-graph-button', n_clicks=0, className='btn btn-primary mt-4'),
                    html.Div(id='graph-output', className='mt-3'),
                    # Add this Div inside your main html.Div container where you configure your Dash layout
                    html.Div([
                        html.H5("References:"),  # Title for the references section
                        html.Div(id='source-links')  # This will display the hyperlinks
                    ], className='mt-3', id="source-links-div", style={'display': 'none'}),  # Add some margin-top for spacing
                    html.Hr(),
                    html.Div(className='row align-items-center', children=[
                        html.Div(className='col-4', children=[
                            html.Button('Reset Data', id='reset-button', n_clicks=0, className='btn btn-warning me-2'),
                            html.Button('Select All', id='select-all-button', n_clicks=0, className='btn btn-secondary me-2'),
                            html.Button('Deselect All', id='deselect-all-button', n_clicks=0, className='btn btn-secondary me-2'),
                            html.Button('First 10', id='select-first-ten-button', n_clicks=0, className='btn btn-secondary')
                        ]),
                        html.Div(className='col-4', children=[
                            html.Label('Column Grouping:', htmlFor='group-selector-dropdown', className='text-center'),
                            dcc.Dropdown(
                                id='group-selector-dropdown',
                                options=[{'label': group, 'value': group} for group in group_to_columns.keys()],
                                className='form-select'
                            )
                        ]),
                        html.Div(className='col-4', children=[
                            html.Label([
                                'Column References: ',
                                dcc.Link('Open Selected Reference', href='', target='_blank', id='column-references-link', style={'display': 'none'})
                            ], htmlFor='column-references-dropdown', className='text-center'),
                            dcc.Dropdown(
                                id='column-references-dropdown',
                                options=[
                                    {'label': f'{name}: {link}', 'value': f'{name}||{link}'}
                                    for name, link in column_hyperlinks.items()
                                ],
                                className='form-select',
                                style={'white-space': 'nowrap'},  # Changed to 'normal' to allow text wrapping within the dropdown
                                value=None  # Ensuring no value is selected initially
                            )
                        ])
                    ]),
                    html.H3('Data Table', className='scrollbar-top mt-3'),
                    dcc.Loading(
                        id="loading-datatable",
                        type="default",
                        children=[  
                            dash_table.DataTable(
                            id='datatable',
                            columns=columns,
                            data=df.to_dict('records'),
                            editable=True,
                            row_selectable='multi',
                            selected_rows=[],
                            sort_action='native',
                            filter_action='native',
                            page_action='none',
                            #fixed_columns={'headers': True, 'data': 1},  # Fixing the first two columns
                            #style_table={
                            #    'overflowX': 'auto',
                            #    'width' : '100%', # Enable horizontal scrolling on the table
                            #    'minWidth' : '100%'
                            #},  
                            style_cell={'textAlign': 'left', 'padding': '5px'},
                            style_header={
                                'textAlign': 'left',
                                'fontWeight': 'bold',
                                'padding': '5px',
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'borderBottom': '1px solid black'
                            },
                            style_data_conditional=[
                                {'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'}
                            ],
                            sort_by=[{'column_id': df.columns[2], 'direction': 'desc'}]
                        )
                    ])
     
                ])
    
    return htmlDiv, df_json, category_filter_json, column_hyperlinks_json, columns_json, group_to_columns_json, group_selector_dropdown_json, group_selector_dropdown__multibar_json


# Define a utility function to run async functions within callbacks
def async_to_sync(func):
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper

...

@app.callback(
    [
        Output('loading-output', 'children'),
        Output('modal-webscrape', 'is_open'),
        Output('instance-name', 'value'),
        Output('collection-selector-dropdown', 'options'),
        Output('collection-selector-dropdown', 'value'),
        Output('loading-output-custom', 'children'),
        Output('modal-custom', 'is_open'),
        Output('instance-name-custom', 'value'),
        Output('loading-output-delete', 'children'),
        Output('modal-delete-collection', 'is_open')
    ],
    [
        Input('webscrape-button', 'n_clicks'),
        Input('submit-instance', 'n_clicks'),
        Input('save-custom-table-button', 'n_clicks'),
        Input('submit-instance-custom', 'n_clicks'),
        Input('delete-collection-button', 'n_clicks'),
        Input('close-delete-button', 'n_clicks'),
        Input('confirm-delete-button', 'n_clicks'),
    ],
    [
        State('modal-webscrape', 'is_open'),
        State('instance-name', 'value'),
        State('datatable', 'derived_virtual_data'),
        State('store-column-hyperlinks', 'data'),
        State('store-category-filter', 'data'),
        State('modal-custom', 'is_open'),
        State('instance-name-custom', 'value'),
        State('modal-delete-collection', 'is_open'),
        State('collection-selector-dropdown', 'value'),
    ],
    prevent_initial_call=True,
    allow_duplicate=True
)
@async_to_sync
async def perform_upload(n_clicks_button, n_clicks_submit, n_clicks_custom, n_clicks_submit_custom, n_clicks_delete, n_clicks_delete_cancel, n_clicks_delete_confirm,
                         is_open_modal, instance_name, 
                         derived_virtual_data, store_column_hyperlinks, store_category_filter, is_open_custom, instance_name_custom,
                         is_open_delete, selected_collection):
    
    if n_clicks_button is None and n_clicks_submit is None and n_clicks_custom is None and n_clicks_submit_custom is None and n_clicks_delete is None and n_clicks_delete_cancel is None and n_clicks_delete_confirm is None:
        raise PreventUpdate

    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    # Determine the trigger
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Default values for outputs
    loading_output = no_update
    modal_is_open = is_open_modal
    instance_value = instance_name
    options = no_update
    selected_value = no_update
    loading_output_custom = no_update
    modal_is_open_custom = is_open_custom
    instance_value_custom = instance_name_custom
    loading_output_delete = no_update
    modal_is_open_delete = is_open_delete

    
    if trigger_id == 'webscrape-button' and n_clicks_button:
        modal_is_open = True
        instance_value = ""  # Clear instance name input
        loading_output = html.Div("")

    elif trigger_id == 'save-custom-table-button' and n_clicks_custom: 
        modal_is_open_custom = True
        instance_value_custom = ""  # Clear instance name input
        loading_output_custom = html.Div("")

    elif trigger_id == 'delete-collection-button' and n_clicks_delete: 
        modal_is_open_delete = True
        loading_output_delete = html.Div("")
        

    elif trigger_id == 'submit-instance' and n_clicks_submit:
        # Simulate a loading message and a long-running process
        
        nuclear_url = 'https://fas.org/initiative/status-world-nuclear-forces/'
        gfp_url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'
        gfp_base_url = 'https://www.globalfirepower.com'
        output_name = await loadDatabase(db, gfp_url, gfp_base_url, nuclear_url, instance_name)
        loading_output = html.Div(f"Data for {output_name} successfully scraped and saved. Click elsewhere to close.")

        # Retrieve the updated options for the dropdown
        options = [{'label': collection, 'value': collection} for collection in db.list_collection_names()]
        # Select the newest instance
        selected_value = output_name  
        # Close the pop-up.      
        modal_is_open = False

    elif trigger_id == 'submit-instance-custom' and n_clicks_submit_custom:
        # Convert the derived_virtual_data to a DataFrame
        df = pd.DataFrame(derived_virtual_data)
        column_hyperlinks = json.loads(store_column_hyperlinks)
        category_filter = json.loads(store_category_filter)
        output_name = await loadDatabaseCustom(db, df, category_filter, column_hyperlinks, instance_name_custom)
        # Close the pop-up.
        modal_is_open_custom = False
        loading_output_custom = html.Div(f"Data for {output_name} successfully saved custom table. Click elsewhere to close.")
        

        # Retrieve the updated options for the dropdown
        options = [{'label': collection, 'value': collection} for collection in db.list_collection_names()]
        # Select the newest instance
        selected_value = output_name  

    elif trigger_id == 'close-delete-button' and n_clicks_delete_cancel:
        # Close the pop-up. 
        modal_is_open_delete = False
    
    elif trigger_id == 'confirm-delete-button' and n_clicks_delete_confirm:
        db[selected_collection].drop()
        options = [{'label': collection, 'value': collection} for collection in db.list_collection_names()]
        selected_value = '2024-All-Data'
        # Close the pop-up. 
        modal_is_open_delete = False
        # If pop-up fails to close. 
        loading_output_delete = html.Div(f"Data for {selected_collection} successfully deleted. Click elsewhere to close.")
        

    return loading_output, modal_is_open, instance_value, options, selected_value, loading_output_custom, modal_is_open_custom, instance_value_custom, loading_output_delete, modal_is_open_delete



# Call back to determine what options display depending on graph type. 

@app.callback(
    [
        Output('x-axis-selector-dropdown-div', 'style'),
        Output('y-axis-selector-dropdown-div', 'style'),
        Output('sort-direction-dropdown-div', 'style'),
        Output('group-selector-dropdown-multibar-div', 'style')
    ],
    Input('graph-type-dropdown', 'value')
)
def update_ui_visibility(graph_type):
    if graph_type == 'multi-bar':
        return ({'display': 'block'}, {'display': 'none'}, {'display': 'none'}, {'display': 'block'})
    elif graph_type == "bar":
        return ({'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'none'})
    elif graph_type == "pie":
        return ({'display': 'block'}, {'display': 'block'}, {'display': 'none'}, {'display': 'none'})


@app.callback(
    [
        Output('graph-output', 'children'),
        Output('source-links', 'children'),
        Output('source-links-div', 'style')
    ],
    [Input('create-graph-button', 'n_clicks'),
     Input('group-selector-dropdown-multibar', 'value'),
     Input('sort-direction-dropdown', 'value')],
    [State('datatable', 'derived_virtual_data'),
     State('datatable', 'derived_virtual_selected_rows'),
     State('graph-type-dropdown', 'value'),
     State('x-axis-selector-dropdown', 'value'),
     State('y-axis-selector-dropdown', 'value'),
     State('store-group-to-columns', 'data'),
     State('store-column-hyperlinks', 'data')]
)

# Call back to upgrade the graph

def update_graph(n_clicks, selected_group, sort_direction, virtual_data, selected_rows, graph_type, x_axis_selection, y_axis_selection, store_group_to_columns, store_column_hyperlinks):

    if not n_clicks or virtual_data is None:
        return html.Div("Click the button to generate the graph or no data to display.")
    
    # Retrieve Data from Dcc.Store: 
    group_to_columns_dict = json.loads(store_group_to_columns)
    group_to_columns = defaultdict(list, group_to_columns_dict)
    column_hyperlinks = json.loads(store_column_hyperlinks)

    df_current_view = pd.DataFrame(virtual_data)

    # Convert all values in the x_axis_selection column to string to avoid comparison error
    df_current_view[x_axis_selection] = df_current_view[x_axis_selection].astype(str)

    if selected_rows is not None and len(selected_rows) > 0:
        df_filtered = df_current_view.iloc[selected_rows, :]
    else:
        df_filtered = df_current_view
    
        # Convert all numeric columns (except 'Country Name' and 'Affiliation') to integers
    for col in df_current_view.columns:
        if col not in ['Country Name', 'Affiliation']:
            df_current_view[col] = pd.to_numeric(df_current_view[col], errors='coerce').fillna(0).astype(int)

    hyperlink_elements = []

    if graph_type == 'multi-bar' and selected_group:
        group_columns = group_to_columns[selected_group]
        # Sum the data for each x-axis category
        df_to_plot = df_filtered.groupby(x_axis_selection)[group_columns].sum().reset_index()
        fig = px.bar(df_to_plot, x=x_axis_selection, y=group_columns, barmode='group', title="Multi-Bar Graph")
        hyperlink_elements = [html.Div([html.A(col, href=column_hyperlinks.get(col, "#"), target="_blank")]) for col in group_columns if col in column_hyperlinks]
        return dcc.Graph(figure=fig), html.Div(hyperlink_elements), {'display': 'block'}

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
        hyperlink_elements = [html.Div([html.A(y_axis_selection, href=column_hyperlinks.get(y_axis_selection, "#"), target="_blank")]) if y_axis_selection in column_hyperlinks else ""]
        return dcc.Graph(figure=fig), html.Div(hyperlink_elements), {'display': 'block'}

    elif graph_type == 'pie':
        fig = px.pie(df_filtered, names=x_axis_selection, values=y_axis_selection, title="Pie Chart")
        hyperlink_elements = [html.Div([html.A(x_axis_selection, href=column_hyperlinks.get(x_axis_selection, "#"), target="_blank")]) if x_axis_selection in column_hyperlinks else ""]
        return dcc.Graph(figure=fig), html.Div(hyperlink_elements), {'display': 'block'}

    else:
        return html.Div('Invalid graph type selected.'), html.Div(hyperlink_elements), {'display': 'none'}

    return dcc.Graph(figure=fig)


# Call back to update table

@app.callback(
    [Output('datatable', 'columns'),
     Output('column-references-dropdown', 'options')],
    [Input('group-selector-dropdown', 'value')],
    [State('store-group-to-columns', 'data'),
     State('store-df', 'data'),
     State('store-column-hyperlinks', 'data')]
)
def update_table_columns(selected_group, store_group_to_columns, store_df, store_column_hyperlinks):

    # Retrieve Data from Dcc.Store: 
    group_to_columns_dict = json.loads(store_group_to_columns)
    group_to_columns = defaultdict(list, group_to_columns_dict)
    store_df_json = StringIO(store_df)
    df = pd.read_json(store_df_json, orient='split')
    column_hyperlinks = json.loads(store_column_hyperlinks)

    if selected_group:

        # Filter column hyperlinks based on the selected group
        filtered_hyperlinks = {name: link for name, link in column_hyperlinks.items() if name in group_to_columns[selected_group]}
        
        # Convert filtered hyperlinks to dropdown options
        options = [{'label': f'{name}: {link}', 'value': f'{name}||{link}'} for name, link in filtered_hyperlinks.items()]

        # Get the columns for the selected group
        columns_for_group = group_to_columns[selected_group]
        # Filter and return columns that are in the selected group
        return [{"name": col, "id": col} for col in df.columns if col in columns_for_group or col == 'Country Name' or col == 'Affiliation'], options
    else:
        options=[{'label': f'{name}: {link}', 'value': f'{name}||{link}'} for name, link in column_hyperlinks.items()]
        # If no group is selected, show all columns
        return [{"name": col, "id": col} for col in df.columns], options

# Reset the table back to original data if edited
@app.callback(
    Output('datatable', 'data'),
    [Input('reset-button', 'n_clicks')],
    [State('store-df', 'data')],
    prevent_initial_call=True  # Prevents the callback from firing upon the initial load
)
def reset_table(n_clicks, store_df):
    df = pd.read_json(store_df, orient='split')
    return df.to_dict('records')


# Callback to select or unselect all rows. 

@app.callback(
    Output('datatable', 'selected_rows'),
    [Input('select-all-button', 'n_clicks'),
     Input('deselect-all-button', 'n_clicks'),
     Input('select-first-ten-button', 'n_clicks')],
    [State('datatable', 'derived_virtual_indices')]
)
def update_selected_rows(select_all_clicks, deselect_all_clicks, select_first_ten_clicks, sorted_indices):
    if not callback_context.triggered:
        raise PreventUpdate

    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'select-all-button' and select_all_clicks:
        return sorted_indices  # This will select all currently visible sorted rows
    elif trigger_id == 'deselect-all-button' and deselect_all_clicks:
        return []
    elif trigger_id == 'select-first-ten-button' and select_first_ten_clicks:
        # Select the first 10 indices based on the current sort/filter
        if sorted_indices is None:
            return []
        return sorted_indices[:10]

    return no_update

@app.callback(
    [Output('column-references-link', 'href'),
     Output('column-references-link', 'style')],
    [Input('column-references-dropdown', 'value')]
)
def update_reference_link(value):
    if value:
        name, url = value.split('||')
        return url, {'display': 'inline'}
    return '', {'display': 'none'}


@app.callback(
    [
        Output('webscrape-button-div', 'style'),
        Output('save-custom-table-button-div', 'style'),
        Output('delete-collection-button-div', 'style')
    ],
    Input('collection-selector-dropdown', 'value'),
    allow_duplicate=True
)
def update_button_visibility(value):
    if value is None:
        return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
    elif value in ['2024-All-Data', '2024-Nuclear-Only']:
        return {'display': 'block'}, {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'block'}, {'display': 'block'}, {'display': 'block'}


if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8050)
