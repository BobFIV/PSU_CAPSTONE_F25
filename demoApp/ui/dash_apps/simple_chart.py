from django_plotly_dash import DjangoDash
from dash import dcc, html

# Line chart
app = DjangoDash("SimpleChart")

app.layout = html.Div([
    dcc.Graph(
        id="line-chart",
        figure={
            "data": [
                {"x": [1, 2, 3, 4, 5], "y": [10, 20, 15, 25, 30],
                 "type": "scatter", "mode": "lines+markers", "name": "Device A"},
            ],
            "layout": {
                "title": {"text": "Live Sensor Data", "x": 0.5},
                "plot_bgcolor": "#f8f9fa",
                "paper_bgcolor": "#f8f9fa",
                "font": {"family": "Arial", "size": 14},
            }
        }
    )
])
