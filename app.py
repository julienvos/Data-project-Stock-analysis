from Stock_analysis_functions import *

import yfinance as yf
import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

percentages = [5,10,15,20]
periods = [5,10,15,20,30,60]
years = ['1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','max']

technical_indicators = ['RSI_EMA', 'MACD']

other_graphs = ['ratio_close_price_5_days',
                'ratio_close_price_10_days',    
                'ratio_close_price_20_days',
                'log_return_10_days',
                'log_return_30_days', 
                'log_return_60_days']

app.layout = html.Div([
                       
                        html.Div([
                                  html.H5('Select the stock', style={'color': 'black'}),

                                  html.Label(children=[
                                                        dcc.Input(id='text_stock', type='text', value='AAPL'),
                                                        html.Button(id='submit_stock', n_clicks=0, children= 'Show', style={'color':'black'})]),
                                                       
                                  
                                  html.Label(dcc.Dropdown(
                                                           id='year_dropdown',
                                                           options=
                                                           [{'label':year, 'value':year} for year in years],
                                                           value="1y",
                                                           multi=False),
                                             
                                                      style={"width" : '60%'}),
                                  
                                  html.Br(),

                                  html.Label(children=[html.Font("Percentage up", style={'color':'black'}),
                                                       dcc.Slider(id='percent_slider',
                                                          min=min(percentages),
                                                          max=(max(percentages)),
                                                          step=None,
                                                          marks={percent : {'label': str(percent) + '%', 'style':{'fontSize': 14}} for percent in percentages},
                                                          dots=True,
                                                          value=5,
                                                          tooltip={'placement':'top'}
                                                                  )
                                                        ],
                                             style={
                                                 'width':'25%'
                                                  }
                                             ),
                                  
                                  html.Br(),

                                          html.Label(children=[html.Font("Days in future", style={'color':'black'}),
                                          dcc.Slider(id='period_slider',
                                          min=min(periods),
                                          max=max(periods),
                                          step=None,
                                          marks={period : {'label': str(period) + ' days', 'style':{'fontSize': 14}} for period in periods},
                                          dots=True,
                                          value=5,
                                          tooltip={'placement':'top'}
                                                  )
                                        ],
                              style={
                                  'width':'50%'
                                  }
                              ),
                                  ]),
                       

                        html.Div(
                        dcc.Graph(id='stock_prices'),
                        # style={
                        #     'float': 'right',
                        #     'width':'70%',
                        #     'margin': '0 1.5%'
                        # }
                        ),
                       
                       #the tech indicator graph
                       html.Br(),

                       html.Label(children=[
                                            html.Font("Technical Indicator", style={'color':'black'}),
                                            dcc.Dropdown(id='indicator_dropdown',
                                                         options=[{'label': "MACD", 'value':"MACD"},
                                                                  {'label': "RSI", 'value':"RSI_EMA"}],
                                                         value="MACD",
                                                          multi=False,
                                                          style={"width" : '60%'})]
                           ),

                       html.Br(),


                       html.Div(dcc.Graph(id='tech_indicator')),
                                
                      #other graphs   
                      html.Br(),      
                      html.Label(children=[
                                            html.Font("Other graphs", style={'color':'black'}),
                                            dcc.Dropdown(id='dropdown_other_graphs',
                                                         options=[{'label': x, 'value': x} for x in other_graphs],
                                                         value=other_graphs[0],
                                                          multi=False,
                                                          style={"width" : '60%'})]
                                ),

                      html.Br(),

                      html.Div(dcc.Graph(id='other_graphs'))

])

@app.callback(
    Output(component_id='stock_prices', component_property='figure'),
    Input(component_id='submit_stock', component_property='n_clicks'),
    Input(component_id='percent_slider', component_property='value'),
    Input(component_id='period_slider', component_property='value'),
    Input(component_id='year_dropdown', component_property='value'),
    State(component_id='text_stock', component_property='value'))

def update_graph(n_clicks, percent, period, year, stock):

  df = total_stock(stock_names=stock.split(" "), period=year, target_percent=percent, target_period=period) 
  #stock.split(" ") means split every stock symbol (based on space) and make a list of the stock symbols

  fig = px.line(data_frame=df,
                x=df.index,
                y='Close',
                line_group='stock_name',
                hover_name='stock_name',
                title='Stock Closing prices',
                color='stock_name',
                labels={'stock_name': 'Stock', 'x': 'Date'}
                )
  
  fig.add_trace(go.Scatter(x=df.loc[df['target'] == 1].index,
                           y=df['Close'].loc[df['target'] == 1],
                           mode='markers',
                           name=str(percent) +  '% up in ' + str(period) + ' days',
                           marker_color='green',
                           marker_symbol='triangle-up',
                           marker_size=15

                           ))

  #fig.update_layout(transition_duration=500)

  return fig


#RSI and MACD indicator  

@app.callback(
    Output(component_id='tech_indicator', component_property='figure'),
    Input(component_id='submit_stock', component_property='n_clicks'),
    Input(component_id='indicator_dropdown', component_property='value'),
    Input(component_id='year_dropdown', component_property='value'),
    State(component_id='text_stock', component_property='value'))

def update_technical_indicator(n_clicks, indicator,year,stock):

  df = total_stock(stock_names=stock.split(" "), period=year)

  fig = px.line(data_frame=df,
              x=df.index,
              y= indicator,
              line_group='stock_name',
              hover_name='stock_name',
              title= indicator,
              color='stock_name',
              labels={'stock_name': 'Stock', 'x': 'Date'})

  # fig.update_layout(transition_duration=700)

  return fig

#other graphs

@app.callback(
    Output(component_id='other_graphs', component_property='figure'),
    Input(component_id='submit_stock', component_property='n_clicks'),
    Input(component_id='dropdown_other_graphs', component_property='value'),
    Input(component_id='year_dropdown', component_property='value'),
    State(component_id='text_stock', component_property='value'))

def update_other_graphs(n_clicks, column,year,stock):

  df = total_stock(stock_names=stock.split(" "), period=year)

  fig = px.line(data_frame=df,
              x=df.index,
              y= column,
              line_group='stock_name',
              hover_name='stock_name',
              title= column,
              color='stock_name',
              labels={'stock_name': 'Stock', 'x': 'Date'})

  # fig.update_layout(transition_duration=700)

  return fig


if __name__ == '__main__':
  app.run_server()