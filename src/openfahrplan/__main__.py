from dash import dcc, html
import dash

app = dash.Dash(__name__, suppress_callback_exceptions=True, use_pages=True, title="OpenFahrplan",
                external_stylesheets=["https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"])
app._favicon = "favicon3.png"
app.layout = html.Div(
    id="openfahrplan-root",
    className="flex flex-col flex h-screen",
    children=[
        html.Nav(className="m-4", children=[
            html.Ul(className="flex gap-4", children=[
                html.Li([dcc.Link("Linien", href="/lines")]),
                html.Li([dcc.Link("Haltestellen", href="/stations")]),
                html.Li([dcc.Link("Verbindungen", href="/connection")]),
                html.Li([dcc.Link("Störungen", href="/disruptions")]),
            ])
        ]),
        html.Hr(),
        html.Div(id="openfahrplan-content",style={"flex-grow":"1"},className="grow overflow-y-auto",    children=dash.page_container)
    ])

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
    )
