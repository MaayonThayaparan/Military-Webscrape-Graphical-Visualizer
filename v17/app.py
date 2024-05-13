import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context, no_update
from collections import defaultdict
from dash.dependencies import Input, Output, ClientsideFunction
from utils.load_data import createTable, loadDatabase
from pymongo import MongoClient
from dash.exceptions import PreventUpdate
import json
import dash_bootstrap_components as dbc

# Connect to MongoDB Atlas cluster
client = MongoClient("mongodb+srv://readwriteuser:e35BMIMnmYaOOgRG@cluster0.w1obusd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['military_data']


# ----------------------------------- DASH ---------------------------------------------------


# URL for the Bootstrap CSS CDN (using Bootstrap 5 for this example)
bootstrap_cdn_url = "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[bootstrap_cdn_url])

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
        html.Div(className='row justify-content-center', children=[
            html.Div(className='col-md-4', children=[
                html.Label('Select Database Instance:', htmlFor='collection-selector-dropdown'),
                dcc.Dropdown(
                    id='collection-selector-dropdown',
                    options=[{'label': collection, 'value': collection} for collection in db.list_collection_names()],
                    value=None,
                    placeholder="Select a collection",
                    className='mb-2'
                ),
                html.Button('Webscrape New Instance', id='webscrape-button', className='btn btn-primary')
            ]),
        ]),
        html.Div(id='dynamic-content')
    ], className='container py-4'),
    dbc.Modal(
        id='modal-webscrape',
        is_open=False,
        children=[
            dbc.ModalBody([
                dbc.Input(id='instance-name', type='text', placeholder='Name Instance', className='mb-2'),
                dbc.Button('Submit', id='submit-instance', className='btn btn-success'),
                html.Div(id='loading-output')
            ])
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
    Output('modal-webscrape', 'is_open'),
    [Input('webscrape-button', 'n_clicks')],
    [State('modal-webscrape', 'is_open')]
)
def open_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    [Output('loading-output', 'children'),
     Output('collection-selector-dropdown', 'options')],
    [Input('submit-instance', 'n_clicks')],
    [State('instance-name', 'value'),
     State('collection-selector-dropdown', 'options')]
)
def perform_webscrape(n_clicks, instance_name, options):
    if n_clicks is None:
        raise PreventUpdate

    # Simulate a loading message and a long-running process
    nuclear_url = 'https://fas.org/initiative/status-world-nuclear-forces/'
    gfp_url = 'https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america'
    gfp_base_url = 'https://www.globalfirepower.com'
    loadDatabase(db, gfp_url, gfp_base_url, nuclear_url)
    loading_message = html.Div("Webscraping in progress... Please wait.")

    return [html.Div(f"Data for {instance_name} successfully scraped and saved."), instance_name]


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

    df, category_filter, column_hyperlinks = retrieve_data(value)

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
                        html.Div(className='col-md-4', children=[
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
                        html.Div(id='x-axis-selector-dropdown-div', className='col-md-4', children=[
                            html.Label('Country Grouping:', htmlFor='x-axis-selector-dropdown'),
                            dcc.Dropdown(
                                id='x-axis-selector-dropdown',
                                options=[{'label': col, 'value': col} for col in df.columns if col in ['Country Name', 'Affiliation']],
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
                        fixed_columns={'headers': True, 'data': 1},  # Fixing the first two columns
                        style_table={
                            'overflowX': 'auto',
                            'width' : '100%', # Enable horizontal scrolling on the table
                            'minWidth' : '100%'
                        },  
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
    
    return htmlDiv, df_json, category_filter_json, column_hyperlinks_json, columns_json, group_to_columns_json, group_selector_dropdown_json, group_selector_dropdown__multibar_json

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

    if y_axis_selection != 'Affiliation':
        df_filtered[y_axis_selection] = pd.to_numeric(df_filtered[y_axis_selection], errors='coerce').fillna(0)

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
    Output('datatable', 'columns'),
    [Input('group-selector-dropdown', 'value')],
    [State('store-group-to-columns', 'data'),
     State('store-df', 'data')]
)
def update_table_columns(selected_group, store_group_to_columns, store_df):

    # Retrieve Data from Dcc.Store: 
    group_to_columns_dict = json.loads(store_group_to_columns)
    group_to_columns = defaultdict(list, group_to_columns_dict)
    df = pd.read_json(store_df, orient='split')

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


if __name__ == '__main__':
    app.run_server(debug=True)