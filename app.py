import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask import Flask, send_from_directory
from hana_ml import dataframe
import configparser
import pandas as pd
import base64
from pathlib import Path

def make_conn ():
    config = configparser.ConfigParser()
    config.read('mdd_hbp.ini')
    connection_context = dataframe.ConnectionContext(
    config['MDD_HBP']['url'],
    int(config['MDD_HBP']['port']),
    config['MDD_HBP']['user'],
    config['MDD_HBP']['pwd'])
    return connection_context

def run_sql (sql_script):
    connection_context = make_conn()
    if connection_context:
        sqldataset = (connection_context.sql(sql_script)) ##SQL Query for dataframe 
        df = sqldataset.collect()
        connection_context.close()
        return df
    else:
        print("Conn_error")

UPLOAD_DIRECTORY = Path("sql_scripts/")

server = Flask(__name__)
app = dash.Dash(external_stylesheets=[dbc.themes.LUX])

app.layout = dbc.Container(fluid=True, children=[
    html.Div(
    [
        html.H1("HANA SQL Browser - Note 1969700"),
        html.Div(
            [
            dbc.Row(
            [
                dbc.Col(html.Div(dcc.Upload(
                                                            id="upload-data",
                                                            children=html.Div(["Click to select a file to upload."] ),
                                                            style={
                                                                "width": "100%",
                                                                "height": "30px",
                                                                "lineHeight": "30px",
                                                                "borderWidth": "1px",
                                                                "borderStyle": "solid",
                                                                "borderRadius": "5px",
                                                                "textAlign": "center",
                                                                "margin": "10px",
                                                            },
                                                            multiple=False,
                                                        ), 
                                            ),  width={"size": 4}, ),
                dbc.Col(html.Div(dbc.Button("Run SQL", id='run_sql',  color="success",  className="mr-1"), 
                                            ), width={"size": 2}, ),
                dbc.Col(html.Div( [
                                                dbc.Button("Toggle Notes", color="info", id="notes", className="mr-1"),
                                                dbc.Button("Toggle Script", color="info", id="script", className="mr-1"),
                                                dbc.Button("Toggle Output", color="info", id="output", className="mr-1"),
                                            ] 
                                            ),  width={"size": 6}, ),
            ], ), 
            ],), 
       
        dbc.Collapse( 
            [
                html.H3("SQL Notes"),
                dcc.Textarea(
                    id='textarea-sqlnotes',
                    value='<the sql notes section of the selected file will appear here>',
                    style={"margin": "10px", 'width': '80%', 'height': 150,  'font-size': '10px'},
                    ),  
            ],  id="notes-collapse"), 
        
        dbc.Collapse(
            [
                html.H3("SQL Script"),
                dcc.Textarea(
                    id='textarea-sqlscript',
                    value='<the sql notes section of the selected file will appear here>',
                    style={"margin": "10px", 'width': '80%', 'height': 150,  'font-size': '10px'},
                    ), 
            ],  id="script-collapse"),
            
        dbc.Collapse(
            [
                html.H3("SQL output"),
                dash_table.DataTable(
                    id = 'table',  
                    style_as_list_view=True,  
                    style_header={'backgroundColor': 'white','fontWeight': 'bold'}, 
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    page_current= 0,
                    page_size= 10,
                    export_format='xlsx',
                    export_headers='display'
                    ),
            ], id="output-collapse",  style={"margin": "10px", 'width': '80%'}, ),     
    ],
)])

@app.callback(
    Output("notes-collapse", "is_open"),
    Input("notes", "n_clicks"),
    [State("notes-collapse", "is_open")],
)
def toggle_notes(n_notes, is_open):
    if n_notes:
        return not is_open
    return is_open

@app.callback(
    Output("script-collapse", "is_open"),
    Input("script", "n_clicks"),
    [State("script-collapse", "is_open")],
)
def toggle_script(n_script, is_open):
    if n_script:
        return not is_open
    return is_open

@app.callback(
    Output("output-collapse", "is_open"),
    Input("output", "n_clicks"),
    [State("output-collapse", "is_open")],
)
def toggle_ouput(n_output, is_open):
    if n_output:
        return not is_open
    return is_open


@app.callback(
    Output('textarea-sqlnotes', 'value'), 
    [Input("upload-data", "filename"),  Input("upload-data", "contents")],
)
def update_output(uploaded_filename, uploaded_file_contents):
    """Set TextArea valuefrom SQL Notes"""
    if  uploaded_filename is not None and uploaded_file_contents is not None:
        path_file = UPLOAD_DIRECTORY / uploaded_filename
        file = open(path_file)
        file_contents = file.read().replace(']\n\n', ']')
        start = file_contents.find('/*') + 5
        end = file_contents.find('*/', start)
        value = file_contents[start:end]
        value = 'File Name: ' + uploaded_filename + '\n\n' + value
    else:
        value = "< no file selected >"
    return value

@app.callback(
    Output('textarea-sqlscript', 'value'), 
    [Input("upload-data", "filename"),  Input("upload-data", "contents")],
)
def update_output(uploaded_filename, uploaded_file_contents):
    """Set TextArea valuefrom SQL Notes"""
    if  uploaded_filename is not None and uploaded_file_contents is not None:
        path_file = UPLOAD_DIRECTORY / uploaded_filename
        file = open(path_file)
        file_contents = file.read()
        start = file_contents.find('/*')
        end = file_contents.find('*/', start) + 2
        value = file_contents[end:]
        value = 'SELECT' + value
    else:
        value = "< no file selected >"
    return value
            
@app.callback(
    [Output(component_id='table', component_property='data'), 
      Output(component_id='table', component_property='columns')], 
    [Input("run_sql", "n_clicks"),  
      Input("textarea-sqlscript",  "value")]
)
def on_button_click(n,  sql_txt):
    if n is not None:
        df = run_sql(sql_txt)
        if not df.empty:
            columns = [{'name': col, 'id': col} for col in df.columns]
            data = df.to_dict(orient='records')
            return data, columns
        else:
         return [{}], []
    else:
         return [{}], []
            
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
