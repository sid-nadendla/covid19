import dash
import os
from flask import send_file
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output,State
from plotly import graph_objs as go
from plotly.graph_objs import *
import plotly.express as px
from datetime import datetime as dt
import datetime as dtd
import base64
from io import BytesIO as _BytesIO
from PIL import Image
import io
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders

from google.cloud import storage
storage_client = storage.Client().from_service_account_json(os.getcwd()+"/storage_cred.json")
bucket_name = 'covid19mstcphs'
bucket = storage_client.get_bucket(bucket_name)


#import report generation and classificaton classes
from psi_and_curb_65_score.FinalResults import FinalResults
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

TAB_STYLE = {
    'borderRight':'none',
    'borderBottom':'none',
    'borderTop':'none',
    'boxShadow': 'none',
    'background-color': '#d2e3f3',
    'paddingTop': 0,
    'paddingBottom': 0,
    'height': '42px',
    'color':'#1e1e1e',
    'display':'table',
    'text-align':'middle',
}

SELECTED_STYLE = {
    # 'boxShadow': 'inset 0px 2px 2px 2px #11111',
    'boxShadow': '0px -2px 3px #3b3b3b',
    'borderBottom':'none',
    'background-color': '#ffffff',
    'paddingTop': 0,
    'paddingBottom': 0,
    'height': '42px',
    'color':'#1e1e1e',
    'vertical-align':'middle'
}

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],external_stylesheets=[dbc.themes.BOOTSTRAP]
)
server = app.server

# Plotly mapbox public token
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNqdnBvNDMyaTAxYzkzeW5ubWdpZ2VjbmMifQ.TXcBE-xg9BFdV2ocecc_7g"

#initialize dataframe
today = dt.today()
file_name = ''
# Dictionary of locations
state_wise_cumulative_df = pd.DataFrame()
usa_timeline_df = pd.DataFrame()

list_of_states = {}

testing_methodologies = ['X-Ray Classification','CT-Scan Classification','PSI/CURB-65 Score']

def initialize():
    global state_wise_cumulative_df,usa_timeline_df,list_of_states     
    filename = "gs://covid19mstcphs/cases.csv"
    # filename = "https://storage.cloud.google.com/covid19mstcphs/cases.csv"
    df = pd.read_csv(filename)
    flag = False
    state_wise_cumulative_df = df.groupby(['state_name'],as_index=False)['recovered_count','confirmed_count','death_count'].sum()

    df = df.groupby(['confirmed_date','state_name'],as_index=False)['confirmed_count','death_count','recovered_count'].sum()
    states = pd.unique(df['state_name'])
    list_of_states = states
    usa_timeline_df = pd.DataFrame()

    for state in states:
        df_new = df[df['state_name']==state]
        sum=[0,0,0]
        state_df = pd.DataFrame()
        for index,row in df_new.iterrows():
            sum[0]+= row['confirmed_count']
            sum[1]+= row['death_count']
            sum[2]+= row['recovered_count']
            state_df = state_df.append({'confirmed_date':row['confirmed_date'], 'state_name':row['state_name'],'confirmed_count':sum[0],'death_count':sum[1],'recovered_count':sum[2]   },ignore_index=True)
        usa_timeline_df = usa_timeline_df.append(state_df)

initialize()

#add
def make_item(i):
    # we use this function to make the example items to avoid code duplication
    # print(i)
    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span(
                    dbc.Button(
                        testing_methodologies[i-1],
                        color="primary",
                        id=f"group-{i}-toggle",
                        style={'width':'150px','background-color':'rgb(77, 154, 202)','border':'rgb(77, 154, 202)','color':'white','font-weight':'bold'}
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(
                    formGenerator(f"{i}")
                ),style={'background-color':'#FFFFFF'},
                id=f"collapse-{i}",
            ),
        ],style={'background-color':'#ffffff','border':'none'}
    )

def generateDownloadSSLink(i):
    if i == '3':
        return html.A(children='Download template Spreadsheet',href='/template-spreadsheet-download',id='template_ss_download',style={'font-size':'10px','font-color':'blue','text-decoration':'underline','font-family':'cambria'})
    else:
        return 

#add
def formGenerator(i):
    text = 'Upload file'
    if i=='3':
        buttonName = 'PSI/CURB-65 Score'
        text = 'Upload Sheet(*.xlsx)'
    else:
        buttonName = 'Run Classifier'
        text = 'Upload Image(*.png,*.jpg)'
    button_id = "run-"+i

    return dbc.Row([
        dbc.Col([ 
            generateDownloadSSLink(i),     
            dbc.Row([
                    dbc.Col([html.Span(text,style={'font-size':'15px'})]),
                    dbc.Col([
                        dcc.Upload(id=f'upload-{i}',children=
                            html.Div(['Drag&Drop or ',html.A('Select')]),
                            style={'width':'100%','height':'30px','lineheight':'20px','borderWidth':'1px','borderStyle':'dashed','color':'light-blue','borderRadius':'5px','text-align':'center','font-size':'10px'},
                        )
                    ])
                ]
            ),
            dbc.Row([
                    dbc.Col([html.Span('E-mail: ',style={'font-size':'15px'})]),
                    dbc.Col([dbc.Input(id=f'email-{i}',bs_size = 'md',className = 'mb-3')])
                ],style={'padding-top':'5px'}
            ),

            dbc.Row([
                    dbc.Col([dbc.Button(buttonName,id=button_id,style={'background-color':'rgb(20, 97, 168)','border':'rgb(20, 97, 168)','color':'white'})])
            ],style={'padding-top':'5px'}),

            dbc.Row([html.Div(id=f'result-{i}')],style={'color':'light-blue','padding-left':'5px','font-family':'cambria','font-size':'10px'})
        ])
    ])


app.layout = html.Div([
    dbc.Row([
        html.Span("COVID-19 Dashboard - Research at CPHS Laboratory")
    ],style={'background-color':'rgb(77, 154, 202)','box-shadow':'0px 2px 3px #3b3b3b','font-family':'cambria','font-size':'30px','color':'white'},align='center',justify='center'),

    dbc.Row([
        dbc.Col([
            dcc.Tabs([
                dcc.Tab(label='Home', selected_style=SELECTED_STYLE, style=TAB_STYLE, children=[
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                        dbc.Row(dbc.Col(
                            dcc.Dropdown(
                                    id="location-dropdown",
                                    options=[
                                        {"label": i, "value": i}
                                                        for i in list_of_states
                                    ],
                                                    placeholder="Select State",
                                    style={'height':'33px'}
                                )
                            ),style={'padding-bottom':'1px','padding-top':'1px'}
                        ),
                        dbc.Row(
                            dbc.Col([
                                                dcc.Graph(id="map-graph",style={'background-color':'black','display':'inherit','height':'300px','margin-bottom':'10px'}),
                                dcc.Interval(
                                    id = 'map-interval',
                                    interval = 1800*1000,
                                    n_intervals=0
                                )
                            ])
                        )
                    ]
                                    ,style={'box-shadow':'2px 0px 3px #3b3b3b'}#,width = 5
                ),
                dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col(html.H6(id='Country'))
                                ]),
                                dbc.Row([
                                                    dbc.Col(html.Span('CONFIRMED',style={'color':'rgb(7, 139, 189)','font-weight':'bold'})),
                                                    dbc.Col(html.Span('DEATHS',style={'color':'#cb4335','font-weight':'bold'})),
                                                    dbc.Col(html.Span('RECOVERED',style={'color':'rgb(4, 119, 53)','font-weight':'bold'}))#18a141
                                ]),
                                dbc.Row([
                                                    dbc.Col(html.H6(id='Confirmed',style={'color':'rgb(7, 139, 189)','font-weight':'bold'})),
                                                    dbc.Col(html.H6(id='Deaths',style={'color':'#cb4335','font-weight':'bold'})),
                                                    dbc.Col(html.H6(id='Recovered',style={'color':'rgb(4, 119, 53)','font-weight':'bold'}))
                                ])
                            ],style={'height':'100px'})
                        ]),
                        dbc.Row(
                            dbc.Col([
                                dcc.Graph(id="histogram",style={'height':'230px','padding-bottom':'3px'}),
                                dcc.Interval(
                                    id = 'graph-interval',
                                    interval = 1800*1000,
                                    n_intervals=0
                                )
                            ])
                        )
                    ]#width commented
                ),
            ],style={'column-gap':'3px'}),
            dbc.Row([
                dbc.Col([
                                    dbc.Row(dbc.Col([html.H5('Spread Modeling and Intervention Recommendations')])),
                    # dbc.Row(dbc.Col(html.Span("This part is under constructruction*",style={'color':'red','font-size':'15px','font-family':'arial'}))),
                    dbc.Row(dbc.Col(
                        html.Span(['This secton includes : 1. Identify the best-fit spread model, and estimate the corresponding model parameters using the spread data for different regions',html.Br(),'2. Recommend data-driven and strategic interventions during COVID-19 as a function of time'],style={'font-size':'12px','text-align':'center','color':'grey'})
                    ))
                ])
                            ],style={'box-shadow':'0px -2px 3px #3b3b3b'}),
                        ],width=9,style={'box-shadow':'2px -2px 3px #3b3b3b'}),
        dbc.Col([
            dbc.Row(
                dbc.Col([
                                    dbc.Row(dbc.Col([html.H5('COVID-19 Testing')])),
                    dbc.Row(dbc.Col([make_item(1), make_item(2), make_item(3)], className="accordion"))                    
                ],style={'height':'100%'})
            )#,
            # dbc.Row(dbc.Col(html.H6('Scoring Mechanism - Under Construction')),style={'box-shadow':'0px 0px 0px 0px #000000'})
                        ],style={'box-shadow':'2px -2px 3px #3b3b3b','height':'100%'})
                    ])
                ]),
                
                dcc.Tab(label='Resources', selected_style=SELECTED_STYLE,style=TAB_STYLE, children=[
                    dbc.ListGroup([
                        dbc.ListGroupItem(html.Span(['This Dashboard updates for every 30 minutes.'])),
                        dbc.ListGroupItem(html.Span(['Data Source: We collected data using the API provided by ',html.A('1point3acres.com',target='_blank',href='https://coronavirus.1point3acres.com/',style={'color':'blue','font-family':'cambria'})])),
                        dbc.ListGroupItem(children = (['X-Ray Classification: We used CNN to predict COVID-19 using X-RAY images',
                            dbc.ListGroupItem(html.Span(['X-Ray Image dataset has been taken from: ',html.A('Data Source',target='_blank',href='https://github.com/ieee8023/covid-chestxray-dataset',style={'color':'blue','font-family':'cambria'})])),
                            dbc.ListGroupItem('Observed Accuracy of the prediction model: ~83%'),
                            dbc.ListGroupItem('As the available training data is limited, we have used GRAD-cam to understand the interpretability of the CNN and the heatmap image for the areas of focus is delivered along with prediction result.')
                        ])),
                    ],style={'box-shadow':'2px -2px 3px #3b3b3b','text-align':'left','font-size':'13px'})
                ]),
            ])

        ])
    ])
])

#Callback to set country/world tag
@app.callback(Output("Country", "children"),[Input("location-dropdown","value")])
def update_country_cases(selectedLocation):
    if selectedLocation:
        return selectedLocation
    else:
        return 'USA'

#Callback for Confirmed count
@app.callback(Output("Confirmed", "children"),[Input("location-dropdown","value")])
def update_confirmed_cases(selectedLocation):
    if(not selectedLocation):
        return state_wise_cumulative_df['confirmed_count'].sum()
    else:
        return state_wise_cumulative_df[state_wise_cumulative_df['state_name'] == selectedLocation]['confirmed_count'].sum()

#Callback for Recovered count
@app.callback(Output("Recovered", "children"),[Input("location-dropdown","value")])
def update_recovered_cases(selectedLocation):
    if(not selectedLocation):
        return state_wise_cumulative_df['recovered_count'].sum()
    else:
        return state_wise_cumulative_df[state_wise_cumulative_df['state_name'] == selectedLocation]['recovered_count'].sum()

#Callback for Death count
@app.callback(Output("Deaths", "children"),[Input("location-dropdown","value")])
def update_death_cases(selectedLocation):
    if(not selectedLocation):
        return state_wise_cumulative_df['death_count'].sum()
    else:
        return state_wise_cumulative_df[state_wise_cumulative_df['state_name'] == selectedLocation]['death_count'].sum()


#Callbackfunction to update map
#Update Map graph based on the location selected
@app.callback(Output("map-graph", "figure"),[Input('map-interval','n_intervals'),Input("location-dropdown", "value")])
def update_graph(n,selectedLocation):
    fig = go.Figure(data=go.Choropleth(
        locations=state_wise_cumulative_df['state_name'],
        z=state_wise_cumulative_df['confirmed_count'],
        locationmode='USA-states',
        colorscale='blues',
        autocolorscale=False,
        text='Confirmed', # hover text
        marker_line_color='rgb(77, 154, 202)', # line markers between states
        colorbar_title="Confirmed",
    ))

    fig.update_layout(height=300,geo=dict(scope='usa',showlakes=True,lakecolor='#ffffff'),margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig

@app.callback(Output("histogram", "figure"),[Input('graph-interval','n_intervals'),Input("location-dropdown","value")])
def update_histogram(n,selectedLocation):

    if not selectedLocation:
        timeline_df = usa_timeline_df.groupby(['confirmed_date'],as_index=False)['confirmed_count','recovered_count','death_count'].sum()
    if selectedLocation:
        timeline_df = usa_timeline_df[usa_timeline_df['state_name']==selectedLocation]

    Layout = go.Layout(
            legend = dict(x=0,y=1),
            margin=go.layout.Margin(l=2, r=5, t=2, b=2),
            showlegend=True,
            plot_bgcolor="#ffffff",
            # paper_bgcolor="#FFFFFF",
            dragmode="select",
            font=dict(color="#1e1e1e"),
            xaxis = dict(showline=True,linecolor='#1e1e1e',showgrid=True,gridcolor='lightgrey'),
            yaxis = dict(showline=True,linecolor='#1e1e1e',showgrid=True,gridcolor='lightgrey'))
    fig = go.Figure(
        data=[
            go.Scatter(x=list(timeline_df['confirmed_date']), y=list(timeline_df['confirmed_count']),mode='lines+markers',name='Confirmed',marker=dict(color='rgb(7, 139, 189)')),
            go.Scatter(x=list(timeline_df['confirmed_date']),y=list(timeline_df['death_count']),mode='lines+markers',name='Deaths',marker=dict(color='#cb4335')),
            go.Scatter(x=list(timeline_df['confirmed_date']),y=list(timeline_df['recovered_count']),mode='lines+markers',name='Recovered',marker=dict(color='rgb(4, 119, 53)'))
        ],
        layout = Layout,
        )
    fig.update_xaxes()
    return fig
@app.callback(
    [Output(f"collapse-{i}", "is_open") for i in range(1, 4)],
    [Input(f"group-{i}-toggle", "n_clicks") for i in range(1, 4)],
    [State(f"collapse-{i}", "is_open") for i in range(1, 4)],
)
def toggle_accordion(n1, n2, n3, is_open1, is_open2, is_open3):
    ctx = dash.callback_context

    if not ctx.triggered:
        return ""
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "group-1-toggle" and n1:
        return not is_open1, False, False
    elif button_id == "group-2-toggle" and n2:
        return False, not is_open2, False
    elif button_id == "group-3-toggle" and n3:
        return False, False, not is_open3
    return False, False, False

@server.route('/template-spreadsheet-download') 
def download_csv():
    # print(os.getcwd())    
    return send_file('template-psi-curb65-score.xlsx',
                     mimetype='application/vnd.ms-excel',
                     attachment_filename='template-psi-curb65-score.xlsx',
                     as_attachment=False)

@app.callback(Output('template_ss_download', 'href'), [Input('template_ss_download', 'id')])
def update_link(id):
    return '/template-spreadsheet-download'

#function to generate unique id for test
def generateTestID(filename):
    #dowload csv file from google cloud storage as a file and get the last id information
    # try:
    blob = bucket.get_blob(filename+".csv")
    fileobject = blob.download_as_string()
    decoded_file_content = fileobject.decode()
    split_file_content = decoded_file_content.split("\n")
    if len(split_file_content) == 2:
        return 1
    else:
        return int(split_file_content[-1].split(",")[0]) + 1
    # except:
    #     return np.random(111111,999999)

#callback for run x-ray classifier
@app.callback(Output('result-1','children'),[Input('run-1','n_clicks'),Input('email-1','value'),Input('upload-1','contents'),Input('upload-1','filename')])
def run_X_Ray_Classifier(n_clicks,email,contents,filename):
    # print('in meth')
    # if n_clicks:
    #     unique_id = generateTestID('x-ray-testing')
    #     if contents is not None:
    #         string = contents.split(';base64,')[-1]
    #         decoded = base64.b64decode(string)
    #         buffer = _BytesIO(decoded)
    #         im = Image.open(buffer)
    #         iml = im.save(str(unique_id)+'.png')
        

    #         return html.Div('Testing Completed.Please check you mail for details.',style={'color':'light-blue'})
    # else:
    return html.Div('This functionality is under construction. Will be updated periodically.',style={'font-family':'cambria','font-size':'10px','padding-left':'5px'})

@app.callback(Output('result-2','children'),[Input('run-2','n_clicks'),Input('email-2','value'),Input('upload-2','contents'),Input('upload-2','filename')])
def run_ct_scan_classifier(n_clicks,email,contents,filename):
    return html.Div('This feature is under construction. will be updated periodically.',style={'font-family':'cambria','font-size':'10px','padding-left':'5px'})

@app.callback(Output('result-3','children'),[Input('run-3','n_clicks'),Input('email-3','value'),Input('upload-3','contents'),Input('upload-3','filename')])
def run_psi_curb65_score(n_clicks,email,contents,filename):
    print(contents)
    
    if n_clicks:
        testId = generateTestID('psi_and_curb_65_score')
        fileName = str(testId)+'.csv'
        if contents is not None and email is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                if 'csv' in filename:
                    # Assume that the user uploaded a CSV file
                    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                elif 'xls' in filename:
                    # Assume that the user uploaded an excel file
                    df = pd.read_excel(io.BytesIO(decoded))
                # inputFileName = os.getcwd()+'/psi_and_curb_65_score_testing/'+fileName
                # df.to_csv(inputFileName,index=False)
                blob = bucket.blob(fileName)
                blob.upload_from_string(df.to_csv(),'text/csv')
            except Exception as e:
                return html.Div([
                    'There was an error processing this file.'+e
                ])
            
            #generate report using input excel
            fr = FinalResults()
            # report_filename = fr.generateReport(inputFileName)
            report_df = fr.generateReport(df)

            #save the report csv to google cloud storage
            reportfilename = str(testId)+"_report.csv"
            blob = bucket.blob(reportfilename)
            blob.upload_from_string(report_df.to_csv(),'text/csv')

            #send mail attaching the report file
            # sendMail(inputFileName,testId,report_filename,email)
            sendMail('PSI/CURB-65 Score Report',testId,'',fileName,reportfilename,email)

            #save the entry to csv file
            blob = bucket.blob('psi_and_curb_65_score.csv')
            blobcontent = blob.download_as_string()
            blobdecoded = blobcontent.decode()
            string = str(testId)+","+fileName+","+str(testId)+"_report.csv"+","+email
            blobdecoded+="\n"+string
            blob.upload_from_string(blobdecoded)

            return html.Span('Run Completed. Check your mail.',style={'color':'light-blue','font-size':'10px','text-align':'center'})
        
        else:
            return html.Span('Upload file/email is empty. Please check',style={'color':'light-blue','font-size':'10px','text-align':'center'})
    else:
        return html.Span([])
             
def sendMail(subject,testId,testResult,inputfilename,reportfilename,email):
    fileext = inputfilename.split('.')[-1]
    # print(report_filename)
    fromaddr = "mstcphs@gmail.com"
    toaddr = email
    msg = MIMEMultipart() 
    msg['From'] = fromaddr 
    msg['To'] = toaddr 
    msg['Subject'] = subject+" Test ID: " +str(testId)
    body = "Test ID: "+str(testId)+"\n"+"Please find "+subject+" attached. We have included your input file as well for your reference."+"\n\n"
    if(subject == 'COVID-19 XRAY Classification Test Report'):
        body += "Test Result: " +testResult + "\n"
    body += "Please report to \'mstcphs@gmail.com\' in case of any questions or issues."
    

    blob = bucket.blob(inputfilename)
    input_content = bytearray(blob.download_as_string())
    blob = bucket.blob(reportfilename)
    report_content = bytearray(blob.download_as_string())

    msg.attach(MIMEText(body, 'plain')) 

    p = MIMEBase('application','octet-stream')
    p.set_payload(input_content)
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment", filename= 'input.'+fileext)
    msg.attach(p)
    p = MIMEBase('application','octet-stream')
    p.set_payload(report_content)
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment", filename= 'report.'+fileext)
    msg.attach(p)

    s = smtplib.SMTP('smtp.gmail.com', 587) 
    s.starttls() 
    s.login(fromaddr,"MSTcphsLab") 
    text = msg.as_string() 
    s.sendmail(fromaddr, toaddr, text) 
    s.quit() 

if __name__ =='__main__':
    app.run_server(host='0.0.0.0',port=8080,debug=True)
