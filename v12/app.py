import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table, Input, Output, State, callback_context, no_update
from collections import defaultdict
from dash.dependencies import Input, Output, ClientsideFunction
import data_processing as dp



# ----------------------------------- DASH ---------------------------------------------------

result = dp.createTable() 
df = result[0]
category_filter = result[1]
column_hyperlinks = result[2]


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
    html.Button('Select All', id='select-all-button', n_clicks=0, style={'margin': '10px'}),
    html.Button('Deselect All', id='deselect-all-button', n_clicks=0, style={'margin': '10px'}),
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

    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'select-all-button' and select_all_clicks:
        return list(range(len(rows)))
    elif trigger_id == 'deselect-all-button' and deselect_all_clicks:
        return []

    return no_update


if __name__ == '__main__':
    app.run_server(debug=True)

