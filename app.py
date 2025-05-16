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
from flask import Flask, redirect, session, jsonify
from authlib.integrations.flask_client import OAuth

load_dotenv()

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
        return redirect('/')
    except Exception as e:
        print(f'Auth error: {e}')
        return redirect('/login')


@server.route('/logout')
def logout():
    session.clear()
    return redirect(
        f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?"
        f"returnTo=http://127.0.0.1:8050&"
        f"client_id={os.getenv('AUTH0_CLIENT_ID')}"
    )

@server.route('/is-authenticated')
def is_authenticated():
    if 'user' in session:
        return jsonify({"authenticated": True, "user": session['user']})
    return jsonify({"authenticated": False})

css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css"]
app = Dash(name="Sork Lab Dashboard", server=server, external_stylesheets=css, suppress_callback_exceptions=True)

def serve_layout():
    if 'user' in session: # Authenticated layout
        return html.Div([
            # Main content wrapper with flexible height
            html.Div([
                # Header
                html.Div(
                    html.H1("Sork Lab Dashboard", className="text-center fw-bold"),
                    style={"backgroundColor": 'white', "padding": "15px"}
                ),
                # AUTH0 CHECK -- TEST
                html.Div([
                    html.Div(id='user-info', className="mb-2"),
                    html.A(
                        html.Button("Login", className="btn btn-primary"), 
                        href="/login"),
                    html.A(
                        html.Button("Logout", className="btn btn-outline-secondary btn-sm"), 
                        href="/logout")
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
                    "backgroundColor": "#f5f5f5", 
                    "color": "#e3e3e3", 
                    "padding": "20px", 
                    "width": "100%",
                    "marginTop": "40px"
                }
            )
        ], style={
            "background-color": "#e5ecf6", 
            "minHeight": "100vh",
            "display": "flex",
            "flexDirection": "column"
        }) 
    else: # Not authenticated
        return html.Div([
            # Header
            html.Div(
                html.H1("Sork Lab Dashboard", className="text-center fw-bold"),
                style={"backgroundColor": 'white', "padding": "15px"}
            ),
            # Login content
            html.Div([
                html.Div([
                    html.H2("Welcome to Sork Lab Dashboard", className="text-center"),
                    html.P("Please log in to access the dashboard features.", className="text-center"),
                    html.Div([
                        html.A(
                            html.Button("Login", className="btn btn-primary"),
                            href="/login",
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
                    "backgroundColor": "#f5f5f5", 
                    "color": "#e3e3e3", 
                    "padding": "20px", 
                    "width": "100%",
                    "marginTop": "40px"
                }
            )
        ], style={
            "background-color": "#e5ecf6", 
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

if __name__ == "__main__":
    app.run(debug=True)