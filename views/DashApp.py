import abc
import traceback
from typing import Any

import dash
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output
from flask import Flask


class DashApp(metaclass=abc.ABCMeta):
    def __init__(self, url_base: str, title: str = "NGTT Dashboard") -> None:
        self.url_base = url_base
        self.title = title

    def initialize(self, server: Flask) -> None:
        external_stylesheets = [
            "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
            dbc.themes.BOOTSTRAP,
            "https://eds-static.equinor.com/font/equinor-font.css",
        ]
        self.app = dash.Dash(
            server=server,
            url_base_pathname=self.url_base,
            suppress_callback_exceptions=True,
            external_stylesheets=external_stylesheets,
            title=self.title,
        )

        self.app.layout = self.onload

        @self.app.callback(Output("content", "children"), Input("_ignore", "value"))
        def data_loader_callback(layout: Any) -> Any:
            try:
                self.load_data()
                return self.get_html()
            except Exception:
                return html.Pre(traceback.format_exc())

    def onload(self) -> Any:
        return html.Div(
            [html.Div(id="content", children="Loading data..."), html.Div(id="_ignore")]
        )

    @abc.abstractmethod
    def load_data(self) -> None:
        pass

    @abc.abstractmethod
    def get_html(self) -> Any:
        pass
