from django_plotly_dash import DjangoDash
from dash import dcc, html

# Bar chart
bar_app = DjangoDash("BarChart")

bar_app.layout = html.Div([
    dcc.Graph(
        id="bar-chart",
        figure={
            "data": [
                {"x": ["Device A", "Device B", "Device C"], "y": [30, 25, 40],
                 "type": "bar", "name": "Readings"},
            ],
            "layout": {
                "title": {"text": "Device Comparison", "x": 0.5},
                "plot_bgcolor": "#f8f9fa",
                "paper_bgcolor": "#f8f9fa",
                "font": {"family": "Arial", "size": 14},
            }
        }
    )
])
