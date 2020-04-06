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
storage_client = storage.Client().from_service_account_json(os.getcwd()+"/"+"storage_cred.json")
bucket_name = 'covid19mstcphs'
bucket = storage_client.get_bucket(bucket_name)


#import report generation and classificaton classes
from psi_and_curb_65_score.FinalResults import FinalResults

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],external_stylesheets=[dbc.themes.BOOTSTRAP]
)
server = app.server

# Plotly mapbox public token
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNqdnBvNDMyaTAxYzkzeW5ubWdpZ2VjbmMifQ.TXcBE-xg9BFdV2ocecc_7g"

#initialize dataframe
today = dt.today()
file_name = ''
Confirmed_total,Recovered,Deaths,Active = 0,0,0,0
# Dictionary of locations
list_of_locations = {}
confirmed_cases = {}
deaths_cases = {}
recovered_cases = {}
list_of_countries = {}
country_mapping = {'US':'United States','Brunei':'Brunei Darussalam','Congo (Brazzaville)':'Congo','Congo (Kinshasa)':'Congo, The Democratic Republic of the','Czechia':'Czech Republic','Holy See':'Holy See (Vatican City State)','Iran':'Iran,Islamic Republic of','South':'Korea, Republic of','Laos':'Lao People\'s Democratic Republic','Libya':'Libyan Arab Jamahiriya','Moldova':'Moldova, Republic of','North Macedonia':'Macedonia','Russia':'Russian Federation','Syria':'Syrian Arab Republic','Taiwan*':'Taiwan','Tanzania':'Tanzania, United Republic of'}
testing_methodologies = ['X-Ray Classification','CT-Scan Classification','PSI/CURB-65 Score']

def initialize():
    df_country_codes = pd.read_csv('https://raw.githubusercontent.com/albertyw/avenews/master/old/data/average-latitude-longitude-countries.csv')
    global list_of_locations,list_of_countries,confirmed_cases,deaths_cases,recovered_cases
    global  Confirmed_total,Recovered,Deaths,Active
    flag = False
    today = dt.today()
    while(not flag):
        try:
            file_name = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/"+today.__format__('%m-%d-%Y')+".csv"
            df = pd.read_csv(file_name)
            flag = True
        except:
            today = today - dtd.timedelta(days=1)
    for index, row in df.iterrows():
        list_of_locations[row['Combined_Key']] = {'lat':row['Lat'],'lon':row['Long_']}
        confirmed_cases[row['Combined_Key']] = str(row['Confirmed'])
        deaths_cases[row['Combined_Key']] = str(row['Deaths'])
        recovered_cases[row['Combined_Key']] = str(row['Recovered'])

        country = row['Combined_Key'].split(",")[-1].strip()
        
        
        country = country_mapping[country] if country in country_mapping.keys() else country

        country_lat_long = df_country_codes[df_country_codes['Country'] == country]
        # print(country_lat_long)
        if not country_lat_long.empty:
            list_of_countries[country] = {'lat':float(country_lat_long['Latitude']),'lon':float(country_lat_long['Longitude'])}
        else:
            list_of_countries[country] = {'lat':row['Lat'],'lon':row['Long_']}

    #remove garbage entries
    keys = list(list_of_locations.keys())
    keys = keys[:]
    for i in keys:
        # print('hello',i)
        if confirmed_cases[i] == '0' and deaths_cases[i] == '0' and recovered_cases[i] == '0':
            del confirmed_cases[i]
            del recovered_cases[i]
            del deaths_cases[i]
            del list_of_locations[i]

    #Set Confirmed and active deceased and recovered count for whole world
    Confirmed_total = df['Confirmed'].sum()
    Deaths = df['Deaths'].sum()
    Active = df['Active'].sum()
    Recovered = df['Recovered'].sum()
    # print("changed")

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
                        style={'width':'150px','background-color':'#a3afa6','border':'#a3afa6','color':'#000000','font-weight':'bold'}
                    )
                )
            ),
            dbc.Collapse(
                dbc.CardBody(
                    formGenerator(f"{i}")
                ),style={'background-color':'#262625'},
                id=f"collapse-{i}",
            ),
        ],style={'background-color':'#1e1e1e'}
    )

def generateDownloadSSLink(i):
    if i == '3':
        return html.A(children='Download template Spreadsheet',href='/template-spreadsheet-download',id='template_ss_download',style={'font-size':'10px','font-color':'light-blue','text-decoration':'underline','font-family':'cambria'})
    else:
        return 

#add
def formGenerator(i):
    text = 'Upload file'
    if i=='3':
        buttonName = 'PSI/CURB-65 Score'
        text = 'Upload Sheet(*.xls)'
    else:
        buttonName = 'Run Classifier'
        text = 'Upload Image(*.png)'
    button_id = "run-"+i

    return dbc.Row([
        dbc.Col([ 
            generateDownloadSSLink(i),     
            dbc.Row([
                    dbc.Col([html.Span(text)]),
                    dbc.Col([
                        dcc.Upload(id=f'upload-{i}',children=
                            html.Div(['Drag&Drop or ',html.A('Select')]),
                            style={'width':'100%','height':'30px','lineheight':'20px','borderWidth':'1px','borderStyle':'dashed','color':'light-blue','borderRadius':'5px','text-align':'center','font-size':'10px'},
                        )
                    ])
                ]
            ),
            dbc.Row([
                    dbc.Col([html.Span('E-mail: ')]),
                    dbc.Col([dbc.Input(id=f'email-{i}',bs_size = 'md',className = 'mb-3')])
                ],style={'padding-top':'5px'}
            ),

            dbc.Row([
                    dbc.Col([dbc.Button(buttonName,id=button_id,style={'background-color':'#6b8e23'})])
            ],style={'padding-top':'5px'}),

            dbc.Row([html.Div(id=f'result-{i}')],style={'color':'light-blue','padding-left':'5px','font-family':'cambria','font-size':'10px'})
        ])
    ])

app.layout = html.Div([
    dbc.Row([
        html.Span("COVID-19 Dashboard - Research at CPHS Laboratory")
    ],style={'background-color':'#262625','box-shadow':'0px 2px 3px #3b3b3b','font-family':'cambria','font-size':'30px'},align='center',justify='center'),

    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                        dbc.Row(dbc.Col(
                            dcc.Dropdown(
                                    id="location-dropdown",
                                    options=[
                                        {"label": i, "value": i}
                                        for i in list_of_countries
                                    ],
                                    placeholder="Select a location",
                                    style={'height':'33px'}
                                )
                            ),style={'padding-bottom':'1px','padding-top':'1px'}
                        ),
                        dbc.Row(
                            dbc.Col([
                                dcc.Graph(id="map-graph",style={'height':'300px','margin-bottom':'10px'}),
                                dcc.Interval(
                                    id = 'map-interval',
                                    interval = 1800*1000,
                                    n_intervals=0
                                )
                            ])
                        )
                    ]
                    ,style={'box-shadow':'8px 0px 3px #3b3b3b'}#,width = 5
                ),
                dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col(html.H6(id='Country'))
                                ]),
                                dbc.Row([
                                    dbc.Col(html.Span('CONFIRMED',style={'color':'#f5b041'})),
                                    dbc.Col(html.Span('DEATHS',style={'color':'#cb4335'})),
                                    dbc.Col(html.Span('RECOVERED',style={'color':'#58d68d'}))#18a141
                                ]),
                                dbc.Row([
                                    dbc.Col(html.H6(id='Confirmed',style={'color':'#f5b041'})),
                                    dbc.Col(html.H6(id='Deaths',style={'color':'#cb4335'})),
                                    dbc.Col(html.H6(id='Recovered',style={'color':'#58d68d'}))
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
                    dbc.Row(dbc.Col([html.H5('Spread Modeling and Intervention Recommendations(*)')])),
                    # dbc.Row(dbc.Col(html.Span("This part is under constructruction*",style={'color':'red','font-size':'15px','font-family':'arial'}))),
                    dbc.Row(dbc.Col(
                        html.Span(['This secton includes : 1. Identify the best-fit spread model, and estimate the corresponding model parameters using the spread data for different regions',html.Br(),'2. Recommend data-driven and strategic interventions during COVID-19 as a function of time'],style={'font-size':'12px','text-align':'center','color':'grey'})
                    ))
                ])
            ],style={'box-shadow':'0px -8px 3px #3b3b3b'}),
            dbc.Row(html.Footer(html.Div(className='container-fluid text-center',children=[html.Span(['This Dashboard updates for every 30 minutes. Data for this Visual Dashboard has been taken from publicly available dataset maintained by ',html.A('John Hopkins',target='_blank',href='https://github.com/CSSEGISandData/COVID-19',style={'color':'light-blue','font-family':'cambria','font-size':'10px'})],style={'float':'left','color':'grey','font-family':'arial','font-size':'10px'}),
                                                                                            html.Span(['* represents the corresponding section is incomplete and will be updated periodically.'],style={'float':'left','color':'grey','font-family':'arial','font-size':'10px'})
             ])),style={'padding-top':'20px'})
        ],width=9,style={'box-shadow':'8px -8px 3px #3b3b3b'}),
        dbc.Col([
            dbc.Row(
                dbc.Col([
                    dbc.Row(dbc.Col([html.H5('COVID-19 Testing(*)')])),
                    dbc.Row(dbc.Col([make_item(1), make_item(2), make_item(3)], className="accordion"))                    
                ],style={'height':'100%'})
            )#,
            # dbc.Row(dbc.Col(html.H6('Scoring Mechanism - Under Construction')),style={'box-shadow':'0px 0px 0px 0px #000000'})
        ],style={'box-shadow':'8px -8px 3px #3b3b3b','height':'100%'})
    ],style={'margin-top':'0px','height':'100%'}),
],style={"height": "100%",'width':'100%','marginLeft':'10px','text-align':'center'})

#Callback to set country/world tag
@app.callback(Output("Country", "children"),[Input("location-dropdown","value")])
def update_country_cases(selectedLocation):
    if selectedLocation:
        return selectedLocation
    else:
        return 'World'

#Callback for Confirmed count
@app.callback(Output("Confirmed", "children"),[Input("location-dropdown","value")])
def update_confirmed_cases(selectedLocation):
    # print(selectedLocation)
    #initialize()
    # print("confir"+str(Confirmed_total))
    if selectedLocation:
        if selectedLocation in country_mapping.values():
            selectedLocation = list(country_mapping.keys())[list(country_mapping.values()).index(selectedLocation)]
        country_wise_count = []
        for key in list(confirmed_cases.keys()):
            if key.split(",")[-1].strip() == selectedLocation:
                country_wise_count.append(int(confirmed_cases[key]))
        return "{:,d}".format(sum(country_wise_count))
    else:
        return "{:,d}".format(Confirmed_total)

#Callback for Recovered count
@app.callback(Output("Recovered", "children"),[Input("location-dropdown","value")])
def update_recovered_cases(selectedLocation):
    if selectedLocation:
        if selectedLocation in country_mapping.values():
            selectedLocation = list(country_mapping.keys())[list(country_mapping.values()).index(selectedLocation)]
        
        country_wise_count = []
        for key in list(recovered_cases.keys()):
            if key.split(",")[-1].strip() == selectedLocation:
                country_wise_count.append(int(recovered_cases[key]))
        return "{:,d}".format(sum(country_wise_count))
    else:
        return "{:,d}".format(Recovered)

#Callback for Death count
@app.callback(Output("Deaths", "children"),[Input("location-dropdown","value")])
def update_death_cases(selectedLocation):
    if selectedLocation:
        if selectedLocation in country_mapping.values():
            selectedLocation = list(country_mapping.keys())[list(country_mapping.values()).index(selectedLocation)]
        country_wise_count = []
        for key in list(deaths_cases.keys()):
            if key.split(",")[-1].strip() == selectedLocation:
                country_wise_count.append(int(deaths_cases[key]))
        return "{:,d}".format(sum(country_wise_count))
    else:
        return "{:,d}".format(Deaths)

def plotMap(selectedLocation,flag):
    
    # print(selectedLocation)
    zoom = 0.0
    latInitial = 0.0
    lonInitial = 0.0
    bearing = 0

    if selectedLocation and flag:
        zoom = 2.0
        bearing = 3
        latInitial = list_of_countries[selectedLocation]["lat"]
        lonInitial = list_of_countries[selectedLocation]["lon"]
    # print(type(latInitial),lonInitial)
    
    return go.Figure(
        data=[
                Scattermapbox(
                    lat=[list_of_locations[i]["lat"] for i in list_of_locations],
                    lon=[list_of_locations[i]["lon"] for i in list_of_locations],
                    # mode="markers",
                    hoverinfo="text",
                    text= [i+": "+"C: "+confirmed_cases[i]+","+"D: "+ deaths_cases[i]+","+"R: "+recovered_cases[i] for i in list_of_locations.keys()],
                    marker=dict(size=8,showscale=False,color=[int(x) for x in confirmed_cases.values()],colorscale='reds',opacity=.8)#,color_selected='blue'
                ),
            ],
            layout=Layout(
                autosize=True,
                hovermode='closest',
                margin=go.layout.Margin(l=0, r=10, t=0, b=0),
                showlegend=False,
                mapbox=dict(
                    accesstoken=mapbox_access_token,
                    center=dict(lat=latInitial, lon=lonInitial),  # 40.7272  # -73.991251
                    style="dark",
                    bearing=bearing,
                    zoom=zoom
                ),
                updatemenus=[
                dict(
                    buttons=(
                        [
                            dict(
                                args=[
                                    {
                                        "mapbox.zoom": 2,
                                        "mapbox.center.lon": "0.0",
                                        "mapbox.center.lat": "0.0",
                                        "mapbox.bearing": 0,
                                        "mapbox.style": "dark",
                                    }
                                ],
                                label="Reset Zoom",
                                method="relayout",
                            )
                        ]
                     ),
                    direction="left",
                    pad={"r": 0, "t": 0, "b": 0, "l": 0},
                    showactive=False,
                    type="buttons",
                    x=0.45,
                    y=0.02,
                    xanchor="left",
                    yanchor="bottom",
                    bgcolor="#323130",
                    borderwidth=1,
                    bordercolor="#6d6d6d",
                    font=dict(color="#FFFFFF"),
                )
            ],
        ),
    )

#Update Map graph based on the location selected
@app.callback(Output("map-graph", "figure"),[Input('map-interval','n_intervals'),Input("location-dropdown", "value")])
def update_graph(n,selectedLocation):
    if n and not selectedLocation:
        flag = 0
    else:
        flag = 1
    return plotMap(selectedLocation,flag)

@app.callback(Output("histogram", "figure"),[Input('graph-interval','n_intervals'),Input("location-dropdown","value")])
def update_histogram(n,selectedLocation):
    df_confirmed = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
    df_deaths = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')
    df_recovered = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')

    if selectedLocation:
        # split_location = selectedLocation.split(",")
        # country = split_location[-1].strip()
        # print(country)
        country = selectedLocation
        if selectedLocation in country_mapping.values():
            country = list(country_mapping.keys())[list(country_mapping.values()).index(selectedLocation)]
        df_confirmed = df_confirmed[df_confirmed['Country/Region'] == country]
        df_deaths = df_deaths[df_deaths['Country/Region'] == country]
        df_recovered = df_recovered[df_recovered['Country/Region'] == country]

    list_confirmed_columns = list(df_confirmed.columns)
    list_deaths_columns = list(df_deaths.columns)
    list_recovered_columns = list(df_recovered.columns)

    index = 4
    confirmed_time_line = {}
    deaths_time_line = {}
    recovered_time_line = {}
    xticks_list = list_confirmed_columns[index:]
    xticks_list = [xticks_list[0],xticks_list[int(len(xticks_list)/2)],xticks_list[-1]]

    for col in list_confirmed_columns[index:]:
        confirmed_time_line[col] = df_confirmed[col].sum()
        deaths_time_line[col] = df_deaths[col].sum()
        recovered_time_line[col] = df_recovered[col].sum()

    Layout = go.Layout(
            legend = dict(x=0,y=1),
            margin=go.layout.Margin(l=2, r=5, t=2, b=2),
            showlegend=True,
            plot_bgcolor="#1E1E1E",
            paper_bgcolor="#1E1E1E",
            dragmode="select",
            font=dict(color="white"),
            xaxis = dict(showgrid=False,nticks=2),
            yaxis = dict(showline=True,showgrid=False,nticks=5))
    fig = go.Figure(
        data=[
            go.Scatter(x=list(confirmed_time_line.keys()), y=list(confirmed_time_line.values()),mode='lines+markers',name='Confirmed',marker=dict(color='#f5b041')),
            go.Scatter(x=list(deaths_time_line.keys()),y=list(deaths_time_line.values()),mode='lines+markers',name='Deaths',marker=dict(color='#cb4335')),
            go.Scatter(x=list(recovered_time_line.keys()),y=list(recovered_time_line.values()),mode='lines+markers',name='Recovered',marker=dict(color='#58d68d'))
        ],
        layout = Layout,
        )
    fig.update_xaxes(tickvals=xticks_list)
    return fig

#add
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
            blob = bucket.blob(str(testId)+"_report.csv")
            blob.upload_from_string(report_df.to_csv(),'text/csv')

            #send mail attaching the report file
            # sendMail(inputFileName,testId,report_filename,email)
            sendMail(testId,email)

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
        return html.Span('')
             
def sendMail(testId,email):
    # print(report_filename)
    fromaddr = "mstcphs@gmail.com"
    toaddr = email
    msg = MIMEMultipart() 
    msg['From'] = fromaddr 
    msg['To'] = toaddr 
    msg['Subject'] = "PSI_and_CURB-65_Report Test Id: " +str(testId)
    body = "Test ID: "+str(testId)+"\n"+"Please find PSI/CURB-65 Score report attached. We have included your input file as well for your reference."+"\n\n"
    body += "Please report to \'mstcphs@gmail.com\' in case of any questions or issues."
    

    blob = bucket.blob(str(testId)+"_report.csv")
    report_content = blob.download_as_string().decode()
    
    body += "\n"+report_content

    msg.attach(MIMEText(body, 'plain')) 

    # attachment1 = open(str(testId)+"_report.csv", "rb") 
    # p1 = MIMEBase('application', 'octet-stream') 
    # p1.set_payload((attachment1).read()) 
    # encoders.encode_base64(p1) 
    # p1.add_header('Content-Disposition', "attachment; filename= %s" % 'report') 
    # msg.attach(p1) 

    # attachment = open(fileName, "rb") 
    # p = MIMEBase('application', 'octet-stream') 
    # p.set_payload((attachment).read()) 
    # encoders.encode_base64(p) 
    # p.add_header('Content-Disposition', "attachment; filename= %s" % 'input') 
    # msg.attach(p) 

    s = smtplib.SMTP('smtp.gmail.com', 587) 
    s.starttls() 
    s.login(fromaddr,"MSTcphsLab") 
    text = msg.as_string() 
    s.sendmail(fromaddr, toaddr, text) 
    s.quit() 

if __name__ =='__main__':
    app.run_server(host='0.0.0.0',port=8080,debug=True)
