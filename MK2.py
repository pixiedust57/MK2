import ccxt
import pandas as pd
import numpy as np
import dontshare_config as ds
from datetime import date, datetime, timezone, tzinfo
import time
import schedule
from pprint import pprint
import dontshare_config as dns

binance = ccxt.binanceusdm({
    'enableRateLimit': True,
    # mine
    'apiKey': 'K8F8mq7WTwtj2gNwn4azTWUEHWxlFNFHOqsr3aHCgp8SFoBNbfnUqn5zZ38vIB38',
    'secret': 'GYTEMlojfJYnjAzuo5yOdIDItV92AIM97Mn2pbUm2GjbUtHQWquITPTKwjPsViQa',
    # 'apiKey': dns.an_KEY,
    # 'secret': dns.an_SECRET,
    'testnet': False,
    'timeInForce': 'GTX',
    'options': {
        'defaultType': 'future',
    },

})
# binance.set_sandbox_mode(True)
# binance.FUTURES_TESTNET_URL = 'https://testnet.binancefuture.com/fapi'

symbol = 'BTCUSDT'

pos_size = 0.0025  # contracts //50

target = 18  # exit

stoploss = -7

params = {'timeInForce': 'GTX', "quantity": "0.001",
          }
binance.set_leverage(leverage=10, symbol='BTCUSDT')


# FIND DAILY SMA 20

# What is ask and bid ?

# ask_bid() [0] = ask,[1] = bid

# def my_bal():
#     bal = binance.fetch_balance()
#     print("This is your balance : ", bal)


# print(my_bal())


def ask_bid():
    ob = binance.fetch_order_book(symbol)
    # print(ob)

    bid = ob['bids'][0][0]
    ask = ob['asks'][0][0]

    return ask, bid


print(ask_bid())

# useless function


def fetch_candles():
    timeframe = '15m'
    num_bars = 250
    candles = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=num_bars)
    df = pd.DataFrame(candles, columns=[
                      'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['sma20_d'] = df.close.rolling(20).mean()
    df['body_length'] = (df['close'] - df['open']) / df['open']
    filtered_df = df[(df['body_length'] >= 0.004) &
                     (df['body_length'] <= 0.01)]
    df.loc[(df['body_length'] >= 0.004) & (
        df['body_length'] <= 0.01), 'check1'] = 'YES'
    # print(filtered_df)
# return df
# fetch_candles()
# df_d = daily_sma()
# df_f = f15_sma()
# ask = ask_bid()[0]
# bid = ask_bid()[1]
# combine this 2 df

# print(df_d)
# print(df_f)


def fetch_cross():
    timeframe = '4h'
    num_bars = 100
    current_price = ask_bid()[1]
    candles = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=num_bars)
    df = pd.DataFrame(candles, columns=[
                      'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['sma20_d'] = df.close.rolling(20).mean()
    df['body_length'] = (df['close'] - df['open']) / df['open']
    # filtered_df = df[(df['body_length'] >= 0.004) &
    #                  (df['body_length'] <= 0.01)]
    df.loc[((df['body_length'] >= 0.004) & (df['body_length'] <= 0.0125)) |
           ((df['body_length'] <= -0.004) & (df['body_length'] >= -0.0125)), 'check1'] = 'YES'
    df['check1'].fillna('NO', inplace=True)

    df.loc[df['sma20_d'] < current_price, 'sig'] = 'BUY'
    # df.loc[(df['open'] < df['sma20_d']), 'sig'] = 'SELL'
    df.loc[df['sma20_d'] > current_price, 'sig'] = 'SELL'
    # df.loc[(df['open'] > df['sma20_d']), 'sig'] = 'BUY'

    df.loc[~df['sig'].isin(['SELL', 'BUY']), 'sig'] = 'HOLD'

    fil_df = df.loc[(df['sig'].isin(['SELL']))]

    # print(fil_df)
    return df


# fetch_cross()


def read_chart():
    timeframe = '15m'
    num_bars = 200
    candles = binance.fetch_ohlcv(symbol, timeframe=timeframe, limit=num_bars)
    df = pd.DataFrame(candles, columns=[
                      'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['sma20_d'] = df.close.rolling(20).mean()
    df['body_length'] = (df['close'] - df['open']) / df['open']
    # filtered_df = df[(df['body_length'] >= 0.004) &
    #                  (df['body_length'] <= 0.01)]
    df.loc[((df['body_length'] >= 0.004) & (df['body_length'] <= 0.0125)) |
           ((df['body_length'] <= -0.004) & (df['body_length'] >= -0.0125)), 'check1'] = 'YES'
    df['check1'].fillna('NO', inplace=True)
    # Retracing avoidance
    df['bp_1'] = df['sma20_d'] * .997
    df['sp_1'] = df['sma20_d'] * 1.003

    df.loc[(df['open'] < df['sma20_d']) & (
        df['close'] > df['sma20_d']), 'sig'] = 'BUY'

    df.loc[(df['open'] > df['sma20_d']) & (
        df['close'] < df['sma20_d']), 'sig'] = 'SELL'

    df.loc[~df['sig'].isin(['SELL', 'BUY']), 'sig'] = 'HOLD'
    # print(df)
    fil_df = df.loc[(df['sig'].isin(['SELL', 'BUY']))
                    & (df['check1'] == 'YES')]

    # print(fil_df)

    return df


def open_positions():
    # 'type': 'swap',

    open_positions = binance.fetch_positions(symbols=[symbol])
    for position in open_positions:
        print(f'Side: {position["side"]}')
        # print(f'Size: {position["positionAmt"]}')

    # print(open_positions)

    # bin_bal = binance.fetch_balance()
    # open_positions = open_positions[0]
    # pprint(open_positions)
    # pprint(open_positions)
    openpos_side = position['side']
    print("confirmed side :", openpos_side)

    openpos_size = open_positions[0]['info']['positionAmt']
    print("confirmed size :", openpos_size)
    # print(openpos_side)
    # print(openpos_size)

    if openpos_side == ('long'):
        openpos_bool = True
        long = True
    elif openpos_side == ('short'):
        openpos_bool = True
        long = False
    else:
        openpos_bool = False
        long = None

    return open_positions, openpos_bool, openpos_size, long


def kill_switch():

    # gracefully limit close us
    print('starting the kill switch')
    openposi = open_positions()[1]
    long = open_positions()[3]
    kill_size = open_positions()[2]
    print(f'* * * * *openposi {openposi}, long {long}, size {kill_size}')

    while openposi == True:

        print("Starting kill switch loop till limit fill")
        temp_df = pd.DataFrame()
        print('just made a temp df')

        binance.cancel_all_orders(symbol)
        openposi = open_positions()[1]
        long = open_positions()[3]
        long = open_positions()[3]
        kill_size = open_positions()[2]
        kill_size = int(kill_size.replace(".", ""))
        print(kill_size)

        ask = ask_bid()[0]
        bid = ask_bid()[1]

        if long == False:
            binance.create_limit_buy_order(symbol, kill_size, bid, params)
            print(
                f'just made a BUY to CLOSE order of {kill_size} {symbol} at ${bid}')
            print('sleeping for 30 seconds to see if it fills. . . !')
            time.sleep(30)
        elif long == True:
            binance.create_limit_sell_order(symbol, kill_size, ask, params)
            print(
                f'just made a SELL to CLOSE order of {kill_size} {symbol} at ${ask}')
            time.sleep(30)
        else:
            print(' + + +  ERROR  + + +')

        openposi = open_positions()[1]


def pnl_close():

    print('Checking to see if its time to exit...')

    params = {"code": "USDT"}
    pos_dict = binance.fetch_positions(
        symbols=["BTC/USDT"], params=params)
    # print(pos_dict)
    pos_dict = pos_dict[0]
    side = pos_dict['side']
    # print(side)
    size = pos_dict['contracts']
    entry_price = float(pos_dict['entryPrice'])
    leverage = float(pos_dict['leverage'])
    current_price = ask_bid()[1]
    print(
        f'side: {side} | entry_price: {entry_price} | lev: {leverage} | current_price: {current_price}')
    # short or long
    if side == 'long':
        diff = current_price - entry_price
        long = True
    else:
        diff = entry_price - current_price
        long = False
    try:
        perc = round(((diff/entry_price) * leverage), 10)
    except:
        perc = 0

    print(f'diff {diff} | perc {perc}')
    perc = 100*perc
    print(f'this is our PNL percentage%: {(perc)}%')

    pnlclose = False
    in_pos = False

    if perc > 0:
        in_pos = True
        print('We are in winning Position')
        if perc > target:
            print(
                f':) :) :) starting the kill switch because we hit our target of {target} %')
            pnlclose = True
            kill_switch()
        else:
            print("TARGET NOT HIT YET")
            in_pos = True

    elif perc < 0 and perc > stoploss:
        print('We are in losing position, but holding on!')
        in_pos = True

    elif perc <= stoploss:
        print("Triggering StopLoss :( ")
        pnlclose = True
        kill_switch()

    elif side != None and perc == 0:
        print("Entry Price same as Current Price, so lets wait maybe. . . ")

    else:
        print('NOT IN POSITION!')
        in_pos = False
    print('just finished checking PNL close...')

    return pnlclose, in_pos, size, long
    # if hit target then close
    # GET IN POSITION OR NA

    # return in_pos


def bot():
    # pnl_close()
    df_h = read_chart()  # 15m
    df_f = fetch_cross()  # 1d
    ask = ask_bid()[0]
    bid = ask_bid()[1]

    signal_ht = df_f.iloc[-1]['sig']
    signal_15 = df_h.iloc[-4]['sig']
    # MAKE OPEN ORDER
    # LONG OR SHORT?
    if df_f.iloc[-1]['sig'] == 'BUY' and df_h.iloc[-2]['sig'] == 'BUY':
        sig = 'BUY'
    elif df_f.iloc[-1]['sig'] == 'SELL' and df_h.iloc[-2]['sig'] == 'SELL':
        sig = 'SELL'
    else:
        sig = 'ON HOLD'

    print(f'The Signal from larger timeframe is : {signal_ht}')
    print(f'The Signal from 15m timeframe is : {signal_15}')

    height = df_h.iloc[-2]['check1']
    print(f'is this the right candle ? : {height}')

    open_size = pos_size / 2

# # only run if not in position
    in_pos = pnl_close()[1]
    print(f'Are we in Position ? : {in_pos}')
    if in_pos == False:

        if height == 'YES' and sig == 'BUY':
            print('making an opening order as BUY...')
            bp_1 = bid
            print(f'this is bp_1 : {bp_1}')
            binance.cancel_all_orders(symbol)
            binance.create_limit_buy_order(symbol, open_size, bp_1, params)
            print('just made opening order, so gonna sleep for 2mins....brb ;)')
            time.sleep(120)
        elif height == 'YES' and sig == 'SELL':
            print('making an opening order as SELL')
            sp_1 = ask
            print(f'this is sp_1 : {sp_1} ')
            binance.cancel_all_orders(symbol)
            binance.create_limit_sell_order(symbol, open_size, sp_1, params)
            print('just made opening order, so gonna sleep for 2mins....brb ;)')
            time.sleep(120)
        else:
            print("No, cant enter anywhere now")

    else:
        print('We are in Position already, so not making new orders')


schedule.every(30).seconds.do(bot)  # 900 = 15min

while True:
    try:
        schedule.run_pending()
    except:
        print("Internet error!")
        time.sleep(30)
