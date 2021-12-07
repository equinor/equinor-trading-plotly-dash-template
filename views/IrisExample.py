import datetime
from typing import Any, Dict, List

from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from flask.app import Flask
from plotly.missing_ipywidgets import FigureWidget
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans

from src.utils.DataLoader import DataLoader
from views.DashApp import DashApp

MIN_HEIGHT = 600
LAYOUT = go.Layout(
    margin=go.layout.Margin(
        l=0,  # left margin
        r=0,  # right margin
        b=0,  # bottom margin
    )
)

class IrisExample(DashApp):
    df = None

    def __init__(
        self, url_base: str, options: Dict, data_loader: DataLoader, data_files: Dict
    ) -> None:
        self.options = options
        self.data_loader = data_loader
        self.data_files = data_files
        super().__init__(url_base, self.options["name"])

    def initialize(self, server: Flask) -> None:
        super().initialize(server)

        @self.app.callback(
            Output("cluster-graph", "figure"),
            [
                Input("x-variable", "value"),
                Input("y-variable", "value"),
                Input("cluster-count", "value"),
            ],
        )
        def make_graph(x, y, n_clusters):
            # minimal input validation, make sure there's at least one cluster
            km = KMeans(n_clusters=max(n_clusters, 1))
            df = self.iris.loc[:, [x, y]]
            km.fit(df.values)
            df["cluster"] = km.labels_

            centers = km.cluster_centers_

            data = [
                go.Scatter(
                    x=df.loc[df.cluster == c, x],
                    y=df.loc[df.cluster == c, y],
                    mode="markers",
                    marker={"size": 8},
                    name="Cluster {}".format(c),
                )
                for c in range(n_clusters)
            ]

            data.append(
                go.Scatter(
                    x=centers[:, 0],
                    y=centers[:, 1],
                    mode="markers",
                    marker={"color": "#000", "size": 12, "symbol": "diamond"},
                    name="Cluster centers",
                )
            )

            layout = {"xaxis": {"title": x}, "yaxis": {"title": y}}

            return go.Figure(data=data, layout=layout)
        # make sure that x and y values can't be the same variable
        def filter_options(v):
            """Disable option v"""
            return [
                {"label": col, "value": col, "disabled": col == v}
                for col in self.iris.columns
            ]


        # functionality is the same for both dropdowns, so we reuse filter_options
        self.app.callback(Output("x-variable", "options"), [Input("y-variable", "value")])(
            filter_options
        )
        self.app.callback(Output("y-variable", "options"), [Input("x-variable", "value")])(
            filter_options
        )

    def load_data(self) -> None:
        self.iris = pd.read_csv(
            self.data_loader.get(**self.data_files["iris"]),
            index_col=0
        )
        print(self.iris)

    def get_html(self) -> Any:
        return dbc.Container(
            [
                html.H1("Iris k-means clustering"),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    html.Div(
                                        [
                                            dbc.Label("X variable"),
                                            dcc.Dropdown(
                                                id="x-variable",
                                                options=[
                                                    {"label": col, "value": col} for col in self.iris.columns
                                                ],
                                                value="sepal length (cm)",
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            dbc.Label("Y variable"),
                                            dcc.Dropdown(
                                                id="y-variable",
                                                options=[
                                                    {"label": col, "value": col} for col in self.iris.columns
                                                ],
                                                value="sepal width (cm)",
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            dbc.Label("Cluster count"),
                                            dbc.Input(id="cluster-count", type="number", value=3),
                                        ]
                                    ),
                                ],
                                body=True,
                            )

                            , md=4),
                        dbc.Col(dcc.Graph(id="cluster-graph"), md=8),
                    ],
                    align="center",
                ),
            ],
            fluid=True,
        )
