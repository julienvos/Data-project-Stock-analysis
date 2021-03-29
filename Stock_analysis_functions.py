import yfinance as yf
import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



# The Functions

## Yahoo stock data

def data_yahoo(tickers, period= "5y"):
  data = yf.download(  # or pdr.get_data_yahoo(...
          # tickers list or string as well
          tickers = tickers,

          # use "period" instead of start/end
          # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
          # (optional, default is '1mo')
          period = period,

          # fetch data by interval (including intraday if period < 60 days)
          # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
          # (optional, default is '1d')
          interval = "1d",

          # group by ticker (to access via data['SPY'])
          # (optional, default is 'column')
          group_by = 'ticker',

          # adjust all OHLC automatically
          # (optional, default is False)
          auto_adjust = True,

          # download pre/post regular market hours data
          # (optional, default is False)
          prepost = True,

          # use threads for mass downloading? (True/False/Integer)
          # (optional, default is True)
          threads = True,

          # proxy URL scheme use use when downloading?
          # (optional, default is None)
          proxy = None
      )
  return data

### RSI function

def get_RSI(close_price, window_length=14):

  # Get the % difference in price from previous step (or the diff())
  delta = close_price.pct_change()

  # Get rid of the first row, which is NaN since it did not have a previous 
  # row to calculate the differences
  delta = delta.iloc[1:]

  # Make the positive gains (up) and negative gains (down) Series
  up, down = delta.copy(), delta.copy()
  up[up < 0] = 0
  down[down > 0] = 0

  # Calculate the EWMA
  roll_up1 = up.ewm(span=window_length).mean()
  smooth_roll_up1 = roll_up1.shift(1) * (window_length - 1) + roll_up1 #added to smooth the result
  roll_down1 = down.abs().ewm(span=window_length).mean()
  smooth_roll_down1 = roll_down1.shift(1) * (window_length - 1) + roll_down1 # added to smooth the result

  # Calculate the RSI based on EWMA
  RS1 = smooth_roll_up1 / smooth_roll_down1
  RSI1 = 100.0 - (100.0 / (1.0 + RS1))


  # Calculate the SMA
  roll_up2 = up.rolling(window_length).mean()
  smooth_roll_up2 = roll_up2.shift(1) * (window_length - 1) + roll_up2 #added to smooth the result
  roll_down2 = down.abs().rolling(window_length).mean()
  smooth_roll_down2 = roll_down2.shift(1) * (window_length - 1) + roll_down2 #added to smooth the result

  # Calculate the RSI based on SMA
  RS2 = smooth_roll_up2 / smooth_roll_down2
  RSI2 = 100.0 - (100.0 / (1.0 + RS2))

  return pd.Series(RSI1, name='RSI_EMA')


### MACD function

def get_MACD(close_price, short_window=12, long_window=26):
  short_ema = 0.15 * close_price + 0.85 * close_price.ewm(span=short_window).mean().shift(1)
  long_ema = 0.075 * close_price + 0.925 * close_price.ewm(span=long_window).mean().shift(1)

  MACD = short_ema - long_ema

  return pd.Series(MACD, name='MACD')

## General functions

###log returns

def avg_log_returns(close_price, avg_period=[10]):

  """
  returns log returns
  """
  daily_log_returns_shift = pd.DataFrame(np.log(close_price / close_price.shift(1)))

  log_return = pd.DataFrame(index=close_price.index)

  for x in avg_period:
    log_return["log_return_{}_days".format(x)] = daily_log_returns_shift.rolling(x).sum()

  return log_return.fillna(0)

###Ratio close price

def ratio_avg_close_price(close_price, past_days=[10]):

  ratio = pd.DataFrame(index=close_price.index)
  for x in past_days:
    ratio['ratio_close_price_{}_days'.format(x)] = close_price / close_price.rolling(x).mean()
  return ratio.fillna(1) # fill the first rows with 1 as a ratio

###Target Data

def create_target_data(close_price, period=10, percent=5):

  """
  Calculates the moments in time where the stock goes  x % up or down after y days in the future

  periods: These are the y days in the future

  percents: These are the %'s up or down after period y

  """

  #close price x days ago
  future_close_price = close_price.shift(period * -1)

  #Did the close price went ..  % up in the past x days?
  percentage = percent/100 + 1

  #df with booleans
  target = future_close_price >= (percentage * close_price) # target is raw since it has a lot of sequences of ones

  #ones and zeros
  target = target.fillna(0) * 1 #fillna to fill the Nan's

  #signal
  target = target.diff() # mention only the moments when the price STARTS to go up or down after y days

  return pd.Series(data=target, name='target', dtype='int')


def total_stock(stock_names, period='1y', target_period=10, target_percent=5):

  assert type(stock_names) == list, "stock_names should be a list"
  
  ordered_df = pd.DataFrame() #empty dataframe
  data = data_yahoo(stock_names, period=period)

  for stock in stock_names:

    if len(stock_names) > 1:
      stock_data = data[stock].copy() # data from 1 stock
    else:
      stock_data = data.copy()

    #label of the stock
    label = pd.Series(index=stock_data.index, name='stock_name', dtype='object').fillna(stock)

    #close price
    stock_close = stock_data['Close']

    #RSI
    RSI = get_RSI(stock_close, window_length=14)

    #MACD
    MACD = get_MACD(stock_close, short_window=12, long_window=26)

    #ratio close prices
    ratio_close_price = ratio_avg_close_price(stock_close, past_days=[5,10,20])

    #log_returns
    log_returns = avg_log_returns(stock_close, avg_period=[10,30,60])

    #target data
    target_data = create_target_data(stock_close, period=target_period, percent=target_percent)

    full_df = pd.concat([label, stock_data, ratio_close_price, log_returns,RSI, MACD, target_data], axis=1) #concat all together
    ordered_df = ordered_df.append(full_df)


  return ordered_df.iloc[2:,:] #to avoid nan's in the RSI, MACD and target column

