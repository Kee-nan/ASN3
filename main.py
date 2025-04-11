import re
import pandas as pd
import plotly.express as px
from packaging import version as packaging_version

# Dash components for interactivity
from dash import dcc, html, dash_table, Dash
from dash.dependencies import Input, Output

from config import RELEASE_FILES, PATCH_COLUMNS

def clean_version(v):
    """
    Drops all the unneeded version info.
    Example: "verrsion 51.01 (4306)" -> "51.01"
    """
    s = str(v).lower().strip()
    pattern = re.search(r'(\d+\.\d+(?:\.\d+)?)', s)
    if pattern:
        return pattern.group(1)
    return s

def make_plot(file_key):
    """
    Reads CSV data and groups it by release version (for Zoom/Webex) or release date (for Firefox).
    Returns the Plotly figure and the DataFrame.
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
        # Group by trimmed release version
        grouped = df.groupby(version_col).size().reset_index(name='count')
        grouped["clean_version"] = grouped[version_col].apply(clean_version)
        grouped["sort_key"] = grouped["clean_version"].apply(lambda x: packaging_version.parse(x))
        grouped = grouped.sort_values("sort_key")
        grouped[version_col] = grouped["clean_version"]
        grouped = grouped.drop(columns=["clean_version", "sort_key"])
        x_col = version_col
    else:
        # Group by release date (Firefox or other)
        grouped = df.groupby(release_date_col).size().reset_index(name='count')
        grouped = grouped.sort_values(release_date_col)
        x_col = release_date_col

    # Create a y value. We'll keep most points aligned on zero.
    grouped['y_value'] = 0.0  # Base level for timeline.
    # Optionally add a small jitter if overlapping is a concern:
    if len(grouped) > 1:
        grouped['y_value'] = [0.05 * i for i in range(len(grouped))]

    # Create the scatter plot
    # Map both 'size' and 'color' to the count so users have a visual legend (with colorbar)
    fig = px.scatter(
        grouped,
        x=x_col,
        y='y_value',
        size='count',
        color='count',
        color_continuous_scale='Blues',
        title=f"Interactive Timeline of Releases ({file_key.replace('_releases', '').capitalize()})",
        labels={'count': 'Number of Features', 'y_value': ''},
    )
    
    # Add a timeline baseline
    fig.add_shape(
        type="line",
        x0=grouped[x_col].min(),
        x1=grouped[x_col].max(),
        y0=0,
        y1=0,
        line=dict(color="gray", width=2, dash="dash")
    )
    
    # Add an on-chart annotation to explain the markers
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0, y=1.05,
        text="Dot size & color represent # of features",
        showarrow=False,
        font=dict(family="Arial", size=12, color="#555")
    )
    
    fig.update_layout(
        xaxis_title="Release Version" if x_col == version_col else "Release Date",
        yaxis=dict(showgrid=False, visible=False, zeroline=False),
        plot_bgcolor="white",
        title_x=0.5,  # Center the title
        margin=dict(t=70, l=50, r=50, b=70),
        font=dict(family="Arial", size=12, color="#333")
    )
    
    # Adjust x-axis tick formatting for clarity
    fig.update_xaxes(tickangle=45, gridcolor='lightgray', tickfont=dict(size=10))
    # Enhance markers with a clear outline
    fig.update_traces(
        customdata=grouped[x_col],
        marker=dict(line=dict(width=1.5, color='darkgray'))
    )
    
    # Enhanced hover template with consistent styling
    if file_key in ["webex_releases", "zoom_releases"]:
        hover_template = (
            "<b style='font-size: 14px'>Version: %{x}</b><br>"
            "<b>Features:</b> %{marker.size}<br>"
            "<i>Click for details</i><extra></extra>"
        )
    else:
        hover_template = (
            "<b style='font-size: 14px'>Date: %{x}</b><br>"
            "<b>Features:</b> %{marker.size}<br>"
            "<i>Click for details</i><extra></extra>"
        )
    fig.update_traces(hovertemplate=hover_template)
    
    return fig, df

# Create the Dash app instance
app = Dash(__name__)

# Set file_key here: "firefox_releases", "zoom_releases", or "webex_releases"
file_key = "webex_releases"
fig, df = make_plot(file_key)

app.layout = html.Div([
    # Header
    html.H1("Release Timeline", style={
        'textAlign': 'center',
        'color': '#2c3e50',
        'marginBottom': '20px',
        'fontFamily': 'Arial'
    }),
    # Instructional text for the user
    html.Div("This interactive timeline displays release versions (or dates) on the x-axis. The dot's size and color indicate the number of features included in that release. Click a dot to see detailed information.",
             style={'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial', 'color': '#555'}),
    # Chart
    dcc.Graph(
        id='timeline-chart',
        figure=fig,
        style={'height': '600px', 'width': '90%', 'margin': '0 auto'}
    ),
    html.Hr(style={'margin': '30px 0'}),
    # Details container: displays a table when a dot is clicked
    html.Div(
        id='details-container',
        children="Click on a dot to view individual features here.",
        style={
            'padding': '20px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '5px',
            'marginTop': '20px',
            'fontFamily': 'Arial'
        }
    )
])

@app.callback(
    Output('details-container', 'children'),
    [Input('timeline-chart', 'clickData')]
)
def display_feature_details(clickData):
    if clickData is None:
        return "Click on a dot to view individual features here."
    
    # Determine the selected x value (release version or date)
    point = clickData['points'][0]
    x_value = point['customdata']
    
    version = PATCH_COLUMNS.get("Version")
    release_date = PATCH_COLUMNS["Date"]
    
    # Filter the original DataFrame based on the selected point
    if version and (version in df.columns):
        mask = df[version].apply(lambda v: clean_version(v)) == x_value
        filtered = df[mask]
    else:
        filtered = df[df[release_date] == x_value]
    
    if filtered.empty:
        return "No features found for the selected dot."
    
    # Reset the index and insert a new "ID" column for clarity
    filtered = filtered.reset_index(drop=True)
    filtered.insert(0, "ID", filtered.index + 1)
    
    # Display the details in a styled DataTable
    return dash_table.DataTable(
        data=filtered.to_dict('records'),
        columns=[{"name": col, "id": col} for col in filtered.columns],
        page_size=10,
        style_table={
            'overflowX': 'auto',
            'border': '1px solid #ddd'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #ddd'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial'
        },
        style_data_conditional=[{
            'if': {'row_index': 'odd'},
            'backgroundColor': '#f1f1f1'
        }]
    )

if __name__ == '__main__':
    app.run(debug=True)
