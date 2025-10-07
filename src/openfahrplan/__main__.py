from dash import dcc, html
import dash

app = dash.Dash(__name__, use_pages=True, title="OpenFahrplan",external_stylesheets=["https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"])
app._favicon = "favicon3.png"
app.layout = html.Div([
    # html.H1(id="heading", children='OpenFahrplan', style={'textAlign': 'center'}),
    html.Nav(className="m-4",children=[
        html.Ul(className="flex flex-row gap-4", children=[
            html.Li([dcc.Link("Übersicht", href="/")]),
            html.Li([dcc.Link("Alle Störungen", href="/disruptions")]),
        ])
    ]),
    html.Hr(),
    dash.page_container,
])

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
    )
