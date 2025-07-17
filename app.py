from dash import dcc, html, Dash
from dash.dependencies import Input, Output
from tabs.dataset import dataset_layout
from tabs.stats import stats_layout
from tabs.upload import upload_layout
from tabs.download import download_layout
from tabs.map import map_layout
from tabs.joins import joins_layout
import os
import secrets
from dotenv import load_dotenv
from flask import Flask, redirect, session, jsonify, request
from authlib.integrations.flask_client import OAuth
from urllib.parse import parse_qs
from cache_config import cache

load_dotenv(override=True)

# Initialize OAuth
server = Flask(__name__)
server.secret_key = os.getenv("APP_SECRET_KEY", "default-secret")

oauth = OAuth(server)
auth0 = oauth.register(
    'auth0',
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    api_base_url=f"https://{os.getenv('AUTH0_DOMAIN')}",
    access_token_url=f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token",
    authorize_url=f"https://{os.getenv('AUTH0_DOMAIN')}/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    }, 
    server_metadata_url=f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration"
)

@server.route('/login')
def login():
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce
    return auth0.authorize_redirect(redirect_uri=os.getenv("AUTH0_CALLBACK_URL"), nonce=nonce)

@server.route('/callback')
def callback_handling():
    try:
        token = auth0.authorize_access_token()
        nonce = session.get('nonce')
        userinfo = auth0.parse_id_token(token, nonce=nonce)
        session['user'] = userinfo
        session.pop('nonce', None)
        return redirect('/app/')
    except Exception as e:
        print(f'Auth error: {e}')
        return redirect('/unauthorized')


@server.route('/logout')
def logout():
    session.clear()
    return redirect(
        f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?"
        f"returnTo=https://sorklab2.eeb.ucla.edu/app/&"
        f"client_id={os.getenv('AUTH0_CLIENT_ID')}"
    )

@server.route('/unauthorized')
def unauthorized():
    session.clear()
    return redirect(
        f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?"
        f"returnTo=https://sorklab2.eeb.ucla.edu/app/?error=invalid_credentials&"
        f"client_id={os.getenv('AUTH0_CLIENT_ID')}"
    )

css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css"]
app = Dash(name="Sork Lab Dashboard", server=server, external_stylesheets=css, suppress_callback_exceptions=True, requests_pathname_prefix='/app/')

# Font editting and coloring
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Gowun+Batang&display=swap" rel="stylesheet">
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Gowun Batang', serif;
                color: #133817;
            }

            h1, h2, h3, h4, h5, h6, p, div, span, a, button {
                color: #133817 !important;
            }

            .btn, .btn-primary, .btn-outline-secondary {
                color: #133817 !important;  
            }

            .text-muted {
                color: #133817 !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

cache.init_app(server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '/tmp',
    'CACHE_THRESHOLD': 100
})

def serve_layout():

    dcc.Location(id='url', refresh=False)
    dcc.Store(id='joined-dataset-store'),
    dcc.Store(id="cached-data-key")

    if 'user' in session: # Authenticated layout
        return html.Div([
            # Main content wrapper with flexible height
            html.Div([
                # Header
                html.Div(
                    html.H1("Sork Lab Dashboard", className="text-center fw-bold"),
                    style={"backgroundColor": '#e9ebe8', "padding": "15px"}
                ),
                # AUTH0 CHECK -- TEST
                html.Div([
                    html.Div(id='user-info', className="mb-2"),
                    html.A(
                        html.Button("Login", className="btn btn-primary btn-sm login-button"), 
                        href="/app/login"),
                    html.A(
                        html.Button("Logout", className="btn btn-outline-secondary btn-sm logout-button"), 
                        href="/app/logout")
                ], className="col-3 text-end"),
                # Tab content container
                html.Div([
                    html.Br(),
                    # Give the tabs a unique ID that all components can access
                    dcc.Tabs(id='main-tabs', value='map-tab', children=[
                        map_layout,
                        dataset_layout,
                        stats_layout,
                        joins_layout,
                        upload_layout,
                        download_layout,
                    ], className="mb-4") 
                ], className="col-8 mx-auto", style={"minHeight": "calc(100vh - 200px)"})
            ], style={"flex": "1 0 auto"}),
            
            # Footer that stays at the bottom
            html.Footer(
                html.Div("Sork Lab Dashboard © 2025", className="text-center text-muted py-3"),
                style={
                    "backgroundColor": "#e9ebe8", 
                    "color": "#e3e3e3", 
                    "padding": "20px", 
                    "width": "100%",
                    "marginTop": "40px"
                }
            )
        ], style={
            "backgroundColor": "#e9ebe8", 
            "minHeight": "100vh",
            "display": "flex",
            "flexDirection": "column"
        }) 
    else: # Not authenticated
        return html.Div([
            # Header
            html.Div(
                html.H1("Sork Lab Dashboard", className="text-center fw-bold"),
                style={"backgroundColor": 'e9ebe8', "padding": "15px"}
            ),
            # Errors
            html.Div([
                dcc.Location(id='url', refresh=False),
                html.Div(id='error-message'),
            ]),
            # Login content
            html.Div([
                html.Div([
                    html.H2("Welcome to Sork Lab Dashboard", className="text-center"),
                    html.P("Please log in to access the dashboard features.", className="text-center"),
                    html.Div([
                        html.A(
                            html.Button("Login", className="btn btn-primary"),
                            href="/app/login",
                            className="d-block mx-auto",
                            style={"width": "fit-content"}
                        )
                    ], className="text-center")
                ], className="p-5 bg-white rounded shadow")
            ], className="col-6 mx-auto mt-5"),

            # Maps tab
            html.Div([
                html.Br(), 
                map_layout
            ], className="p-4 bgwhite rounded shadow mt-5", style={
                "width": "90%", 
                "margin": "0 auto"
            }), 

            # Footer that stays at the bottom
            html.Footer(
                html.Div("Sork Lab Dashboard © 2025", className="text-center text-muted py-3"),
                style={
                    "backgroundColor": "#e9ebe8", 
                    "color": "#e3e3e3", 
                    "padding": "20px", 
                    "width": "100%",
                    "marginTop": "40px"
                }
            )
        ], style={
            "backgroundColor": "#e9ebe8", 
            "minHeight": "100vh",
            "display": "flex",
            "flexDirection": "column"
        })
        

app.layout = serve_layout


@app.callback(
    Output('user-info', 'children'),
    Input('main-tabs', 'value')
)
def display_user(tab):
    if 'user' in session:
        return f"Logged in as {session['user']['name']}"
    return "Not logged in"


@app.callback(
    Output('error-message', 'children'),
    Input('url', 'search')
)
def display_error_message(search):
    if search:
        query_params = parse_qs(search.lstrip('?'))
        if 'error' in query_params:
            return html.Div("Login failed: Invalid username or password.", style={'color': 'red', 'textAlign': 'center', 'marginTop': '20px'})
    return ""

if __name__ == "__main__":
    app.run(debug=True)
