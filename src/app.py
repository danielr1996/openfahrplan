import dash
from dash import Dash, html, dcc
import init.env
app = Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"],
           use_pages=True)
app.layout = html.Div(className="",
                      children=[
                          html.H1(id="heading", children='OpenFahrplan', style={'textAlign': 'center'}),
                          html.Nav([
                              html.Ul(className="flex flex-row gap-4",children=[
                                  html.Li([dcc.Link("Home",href="/")]),
                                  html.Li([dcc.Link("Explore",href="/explore")]),
                                  html.Li([dcc.Link("Map",href="/map")]),
                              ])
                          ]),
                          html.Br(),
                          dash.page_container,
                      ])

app.title = "VAG Explorer"
app._favicon = "favicon3.png"
if __name__ == '__main__':
    app.run(debug=True)
