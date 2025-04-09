import re
import pandas as pd
import plotly.express as px
from packaging import version as packaging_version

# dash on plotly gives us click ability on plots
from dash import dcc, html, dash_table, Dash
from dash.dependencies import Input, Output
from config import RELEASE_FILES, PATCH_COLUMNS

def clean_version(v):
    """
    Drops all the unneeded version info
    "verrsion 51.01 (4306)" -> "51.01"
    """
    s = str(v).lower().strip()
    pattern = re.search(r'(\d+\.\d+(?:\.\d+)?)', s)
    if pattern:
        return pattern.group(1)
    return s

def make_plot(file_key):
    """
    Does data grouping from the CSV
    - Zoom/Webex: group by release version
    - Firefox: group by release date
    """
    release_file_path = RELEASE_FILES[file_key]
    try:
        df = pd.read_csv(release_file_path, encoding='cp1252')
    except UnicodeDecodeError:
        df = pd.read_csv(release_file_path, encoding='latin1')
    
    # Convert release date column to datetime
    release_date_col = PATCH_COLUMNS["Date"]
    df[release_date_col] = pd.to_datetime(df[release_date_col], errors='coerce')
    
    version_col = PATCH_COLUMNS.get("Version")
    
    if version_col and (version_col in df.columns) and (file_key in ["webex_releases", "zoom_releases"]):
        # Group by trimmed release version (zoom/webex)
        grouped = df.groupby(version_col).size().reset_index(name='count')
        grouped["clean_version"] = grouped[version_col].apply(clean_version)
        grouped["sort_key"] = grouped["clean_version"].apply(lambda x: packaging_version.parse(x))
        grouped = grouped.sort_values("sort_key")
        grouped[version_col] = grouped["clean_version"]
        grouped = grouped.drop(columns=["clean_version", "sort_key"])
        x_col = version_col
    else:
        # Group by date (Firefox)
        grouped = df.groupby(release_date_col).size().reset_index(name='count')
        grouped = grouped.sort_values(release_date_col)
        x_col = release_date_col

    #no vertical change in timeline
    grouped['y_value'] = 0
    
    fig = px.scatter(
        grouped,
        x=x_col,
        y='y_value',
        size='count',
        title=f"Interactive Timeline of Releases ({file_key.replace('_releases', '').capitalize()})"
    )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis=dict(showgrid=False, visible=False, zeroline=False),
        plot_bgcolor="white"
    )
    fig.update_xaxes(tickangle=45)
    fig.update_traces(customdata=grouped[x_col])
    
    # Hide/Show info available on mouse-hover
    if file_key in ["webex_releases", "zoom_releases"]:
        hover_template = "<b>Version: %{x}</b><br>Count: %{marker.size}<extra></extra>"
    else:
        hover_template = "<b>Date: %{x}</b><br>Count: %{marker.size}<extra></extra>"
    fig.update_traces(hovertemplate=hover_template)
    
    return fig, df

# Create Dash app. Dash gives ability to interact with plotly (click, etc)
app = Dash(__name__)

# Change this to firefox_releases, zoom_releases or webex_releases
file_key = "webex_releases"
fig, df = make_plot(file_key)

# Layout stuff
app.layout = html.Div([
    html.H1("Release Timeline"),
    dcc.Graph(id='timeline-chart', figure=fig),
    html.Hr(),
    html.Div(id='details-container', children="Click on a dot to view individual features here.")
])

# Event thats fired on mouse click. Makes details screen show up
@app.callback(
    Output('details-container', 'children'),
    [Input('timeline-chart', 'clickData')]
)
def display_feature_details(clickData):
    if clickData is None:
        return "Click on a dot to view individual features here."
    
    # Get group id (the version or date)
    point = clickData['points'][0]
    x_value = point['customdata']
    
    version = PATCH_COLUMNS.get("Version")
    release_date = PATCH_COLUMNS["Date"]
    
    # Find all the individual features within a grouping so we can grrab they data
    if version and (version in df.columns):
        mask = df[version].apply(lambda v: clean_version(v)) == x_value
        filtered = df[mask]
    else:
        filtered = df[df[release_date] == x_value]
    
    if filtered.empty:
        return "No features found for the selected dot."
    
    # Display the filtered details using Dash DataTable
    return dash_table.DataTable(
        data=filtered.to_dict('records'),
        columns=[{"name": col, "id": col} for col in filtered.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )

if __name__ == '__main__':
    app.run(debug=True)
