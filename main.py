import re
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from packaging import version as packaging_version
import numpy as np

# Dash components for interactivity
from dash import dcc, html, dash_table, Dash
from dash.dependencies import Input, Output
from config import RELEASE_FILES, PATCH_COLUMNS, REVIEW_FILES, REVIEW_COLUMNS, CLUSTER_FILES

class TraceVisualizer:
    def __init__(self, app_name="firefox"):
        self.app_name = app_name
        self.app = Dash(__name__)
        self.fig, self.df_release, self.df_reviews, self.df_cluster = self.make_plot(app_name)
        self.setup_callbacks()
        self.setup_layout()

    @staticmethod
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

    @staticmethod
    def extract_major_minor(version):
        match = re.search(r'(\d+)\.(\d+)', str(version))
        if match:
            major, minor = match.groups()
            return f"{major}.{minor}"
        else:
            return None  # or "0.0" if you prefer

    def make_plot(self, file_key):
        """
        Reads CSV data and groups it by release version (for Zoom/Webex) or release date (for Firefox).
        Returns the Plotly figure and the DataFrame.
        """
        release_file_path = RELEASE_FILES[f"{file_key}_releases"]
        review_file_path = REVIEW_FILES[f"{file_key}_reviews"]
        cluster_summary_path = CLUSTER_FILES[f"{file_key}_summary"]
        cluster_reviews_path = CLUSTER_FILES[f"{file_key}_clustered_reviews"]
        try:
            df_release = pd.read_csv(release_file_path, encoding='cp1252')
        except UnicodeDecodeError:
            df_release = pd.read_csv(release_file_path, encoding='latin1')

        try:
            df_review = pd.read_csv(review_file_path, encoding='cp1252')
        except UnicodeDecodeError:
            df_review = pd.read_csv(review_file_path, encoding='latin1')
        
        # Convert release date column to datetime
        release_date_col = PATCH_COLUMNS["Date"]
        review_date_col = REVIEW_COLUMNS.get("Date")
        df_release[release_date_col] = pd.to_datetime(df_release[release_date_col], errors='coerce')
        df_review[review_date_col] = pd.to_datetime(df_review[review_date_col], errors='coerce')
        
        version_col = PATCH_COLUMNS.get("Version")
        rating_col = REVIEW_COLUMNS.get("Rating")

        
        release_name = f"{file_key}_releases"
        if version_col and (version_col in df_release.columns) and (release_name in ["webex_releases", "zoom_releases"]):
            # Group by trimmed release version (zoom/webex)
            grouped = df_release.groupby(version_col).size().reset_index(name='count')
            grouped["clean_version"] = grouped[version_col].apply(self.clean_version)
            grouped["sort_key"] = grouped["clean_version"].apply(lambda x: packaging_version.parse(x))
            grouped = grouped.sort_values("sort_key")
            grouped[version_col] = grouped["clean_version"]
            x_col = version_col

            # Handle reviews
            # Webex and Zoom's versions are formatted slightly different in reviews, 
            # and thus need different functions
            if file_key == "webex":
                df_review["clean_version"] = df_review[REVIEW_COLUMNS.get("Version")].apply(self.extract_major_minor)
            elif file_key == "zoom":
                df_review["clean_version"] = df_review[REVIEW_COLUMNS.get("Version")].apply(self.clean_version)
            
            avg_ratings = df_review.groupby("clean_version")[rating_col].mean().reset_index()
            avg_ratings.rename(columns={rating_col: "avg_rating"}, inplace=True)
            review_counts = df_review.groupby("clean_version").size().reset_index(name="review_count")

            grouped = grouped.merge(avg_ratings, on="clean_version", how="left")
            grouped = grouped.merge(review_counts, on="clean_version", how="left")
        else:
            # Group by date (Firefox)
            grouped = df_release.groupby(release_date_col).size().reset_index(name='count')
            grouped = grouped.sort_values(release_date_col)
            x_col = release_date_col

            # Handle reviews for y axis (Firefox needs to handle by date, not version)
            df_review[review_date_col] = pd.to_datetime(df_review[review_date_col], errors='coerce')
            grouped = grouped.sort_values(x_col)
            df_review = df_review.sort_values(review_date_col)

            release_dates = grouped[x_col].to_list()
            release_dates.append(pd.Timestamp.max)

            # Each review is binned by its date to the feature release date that happened before it
            df_review['release_bin'] = pd.cut(
                df_review[review_date_col],
                bins=release_dates,
                labels=grouped[x_col],
                right=False # Don't include reviews that happen on the next review day in the previous bin [x, y)
            )

            df_review['release_bin'] = pd.to_datetime(df_review['release_bin'])

            review_counts = df_review.groupby('release_bin').size().reset_index(name='review_count')

            avg_ratings = df_review.groupby('release_bin')[rating_col].mean().reset_index()
            avg_ratings.rename(columns={rating_col: "avg_rating"}, inplace=True)

            grouped = grouped.merge(avg_ratings, left_on=x_col, right_on='release_bin', how='left')
            grouped = grouped.merge(review_counts, left_on=x_col, right_on='release_bin', how='left')

        grouped['y_value'] = grouped['avg_rating'].fillna(3)
        
        fig = px.scatter(
            grouped,
            x=x_col,
            y='y_value',
            size='count',
            color='review_count',
            color_continuous_scale='Blues',
            symbol_sequence=["diamond"],
            title=f"Interactive Timeline of Releases ({file_key.replace('_releases', '').capitalize()})",
            labels={'count': 'Number of Features', 'review_count': 'Number of Reviews', 'y_value': ''},
        )

        df_cluster = pd.read_csv(cluster_reviews_path)
        df_summary = pd.read_csv(cluster_summary_path)
        df_summary = df_summary.sort_values('version')

        if file_key in ["webex", "zoom"]:
            hover_template = (
                "<b style='font-size: 14px'>Version: %{x}</b><br>"
                "<b>Features:</b> %{marker.size}<br>"
                "<b># Reviews:</b> %{marker.color:.0f}<br>"
                "<b>Avg Rating:</b> %{y:.2f}<br>"
                "<i>Click for details</i><extra></extra>"
            )
        else:
            hover_template = (
                "<b style='font-size: 14px'>Date: %{x}</b><br>"
                "<b>Features:</b> %{marker.size}<br>"
                "<b># Reviews:</b> %{marker.color:.0f}<br>"
                "<b>Avg Rating:</b> %{y:.2f}<br>"
                "<i>Click for details</i><extra></extra>"
            )

        # These update traces NEED to happen BEFORE adding our review cluster plot.
        # Add hover template for features
        fig.update_traces(hovertemplate=hover_template)
        # Enhance markers with a clear outline
        fig.update_traces(
            customdata=grouped[x_col],
            marker=dict(line=dict(width=1.5, color='darkgray'))
        )

        # Make sure cluster_label is clean
        df_summary['cluster_label'] = df_summary['cluster_label'].fillna('Unknown').astype(str)

        min_size = 10
        max_size = 50

        num_reviews = df_summary["num_reviews"]
        size = ((num_reviews - num_reviews.min()) / (num_reviews.max() - num_reviews.min())) * (max_size - min_size) + min_size

        fig.add_trace(go.Scatter(
            x=df_summary["version"],
            y=df_summary["avg_score"],
            mode='markers',
            marker=dict(
                size=size,
                color=df_summary["num_reviews"],
                colorscale='Turbo',
            ),
            name="Cluster Summary",
            showlegend=False,
            customdata=np.stack([df_summary['cluster_label'], df_summary['num_reviews']], axis=-1),
            hovertemplate=(
                "<b>Review Cluster:</b> %{customdata[0]}<br>" +
                "<b>Version:</b> %{x}<br>" +
                "<b>Avg Score:</b> %{y:.2f}<br>" +
                "<b># Reviews:</b> %{customdata[1]:,}<extra></extra>"
            )
        ))  

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
            text="Dot size = # Features, Color = # of reviews",
            showarrow=False,
            font=dict(family="Arial", size=12, color="#555")
        )
        
        fig.update_layout(
            xaxis_title="Release Version" if x_col == version_col else "Release Date",
            yaxis_title="Average Rating (1-5)",
            yaxis=dict(
                showgrid=True,
                range=[1,5],
                dtick=1,
                title="Average Rating",
                showline=True,
                mirror=True
            ),
            plot_bgcolor="white",
            title_x=0.5, # Center the title
            margin=dict(t=70, l=50, r=50, b=70),
            font=dict(family="Arial", size=12, color="#333"),
        )

        # Adjust x-axis tick formatting for clarity
        fig.update_xaxes(tickangle=45, gridcolor='lightgray', tickfont=dict(size=10))
            
        return fig, df_release, df_review, df_cluster

    def setup_callbacks(self):
        @self.app.callback(
            Output('details-container', 'children'),
            [Input('timeline-chart', 'clickData')]
        )
        def display_details(clickData):
            if clickData is None:
                return "Click on a dot to view individual features here."
            
            # Determine the selected x value (release version or date)
            point = clickData['points'][0]
            trace_index = point.get('curveNumber')
            if trace_index == 0:
                # When feature clicked...
                x_value = point['customdata']
                
                version = PATCH_COLUMNS.get("Version")
                release_date = PATCH_COLUMNS["Date"]
                
                # Find all the individual features within a grouping so we can grrab they data
                if version and (version in self.df_release.columns):
                    mask = self.df_release[version].apply(lambda v: self.clean_version(v)) == x_value
                    filtered = self.df_release[mask]
                else:
                    filtered = self.df_release[self.df_release[release_date] == x_value]
                
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
            elif trace_index == 1:
                # When review cluster clicked...
                cluster_label = point['customdata'][0]
                
                filtered_reviews = self.df_cluster[self.df_cluster['cluster_label'] == cluster_label]
                filtered_reviews = filtered_reviews.reset_index(drop=True)
                filtered_reviews.insert(0, "ID", filtered_reviews.index + 1)

                filtered_reviews = filtered_reviews[['ID', 'score', 'content']]
            
                return dash_table.DataTable(
                    data=filtered_reviews.to_dict('records'),
                    columns=[{"name": col, "id": col} for col in filtered_reviews.columns],
                    page_size=10,
                    style_table={'overflowX': 'auto', 'border': '1px solid #ddd'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold', 'border': '1px solid #ddd'},
                    style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Arial'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f1f1f1'}]
                )

    def setup_layout(self):
        self.app.layout = html.Div([
            html.H1("Release Timeline", style={
                'textAlign': 'center',
                'color': '#2c3e50',
                'marginBottom': '20px',
                'fontFamily': 'Arial'
            }),
            html.Div("This interactive timeline displays release versions (or dates) on the x-axis. The dot's size and color indicate the number of features included in that release. Click a dot to see detailed information.",
                    style={'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial', 'color': '#555'}),
            dcc.Graph(
                id='timeline-chart',
                figure=self.fig,
                style={'height': '600px', 'width': '90%', 'margin': '0 auto'}
            ),
            html.Hr(style={'margin': '30px 0'}),
            html.Div(
                id='details-container',
                children="Click on a dot to view individual features/reviews here.",
                style={
                    'padding': '20px',
                    'backgroundColor': '#f8f9fa',
                    'borderRadius': '5px',
                    'marginTop': '20px',
                    'fontFamily': 'Arial'
                }
            )
        ])

    def run(self, debug=True):
        self.app.run(debug=debug)

def main():
    visualizer = TraceVisualizer(app_name="firefox")
    visualizer.run(debug=True)

if __name__ == '__main__':
    main()
