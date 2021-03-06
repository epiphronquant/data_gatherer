# -*- coding: utf-8 -*-
"""
Created on Mon Oct 18 12:28:47 2021

@author: angus
"""
import streamlit as st
import pandas as pd
import scraper_formulas as xf
from time import sleep
### configure page
st.set_page_config(layout="wide")
st.title('Data Downloader')

column_1, column_2 = st.beta_columns(2) ### Divides page into 2 columns
with column_1:### ### Download Statements chart
    st.header ('Download XueQiu Statements')
    tickers = st.text_input("Type in ticker/tickers in the format 01234, SH123456, SZ123456, ABCD for HKEX, SHSE, SZSE and American stocks respectively. Shareholder information only exists for stocks listed in Mainland China.")
    tickers = tickers.split(',')
    tickers = map(str.strip, tickers)
    tickers = list(tickers)
    statement = st.selectbox(
              'What would you like to download?',
              ('Income Statement','Balance Sheet', 'Cash Flow', 'Top 10 Shareholders', 'Top 10 Traded Shareholders'))
    st.write('You selected:', statement)
    freq = st.selectbox(
      'What frequency would the data be? This is irrelevant for shareholder info',
      ('全部','年报', '中报', '一季报', '三季报'))
    st.write('You selected:', freq)
    @st.cache (ttl=300)
    def download(tickers, statement, freq):
        if tickers == ['']:### Makes function not run if there is no input
            tables = pd.DataFrame()
        elif statement == 'Top 10 Shareholders': ### this is for gathering data on the top 10 largest shareholders            
            tickers =[x for x in tickers if len(x)==8]
            tables = []
            for ticker in tickers:
                xf.infinite_query_threaded_shareholder(ticker, tables, "/detail#/SDGD") ### this downloads the data but completes in different order
            while len(tables) < len(tickers): ### Waits for all the data to be gathered from thread pools before proceeding
                sleep(0.01)
            tables = xf.org_table(tickers, tables, row = 1) ### convert list of tables to dataframe in orderly fashion
            
        elif statement == 'Top 10 Traded Shareholders':
            tickers =[x for x in tickers if len(x)==8]
            tables = []
            for ticker in tickers:
                xf.infinite_query_threaded_shareholder(ticker, tables, "/detail#/LTGD") 
            while len(tables) < len(tickers): 
                sleep(0.01)
            tables = xf.org_table(tickers, tables, row = 1) 
            
        elif statement == 'Income Statement':
            tables = []
            for ticker in tickers:
                xf.infinite_query_threaded_statements(ticker, tables, "/detail#/GSLRB", freq = freq) 
            while len(tables) < len(tickers):
                sleep(0.01)
            tables = xf.org_table(tickers, tables) 
            
        elif statement == 'Balance Sheet':
            tables = []
            for ticker in tickers:
                xf.infinite_query_threaded_statements(ticker, tables, "/detail#/ZCFZB", freq = freq) 
            while len(tables) < len(tickers):
                sleep(0.01)
            tables = xf.org_table(tickers, tables) 
        
        else: ## for cash flow statement
            tables = []
            for ticker in tickers:
                xf.infinite_query_threaded_statements(ticker, tables, "/detail#/XJLLB", freq = freq) 
            while len(tables) < len(tickers):
                sleep(0.01)
            tables = xf.org_table(tickers, tables) 
        return tables
    tables = download(tickers, statement, freq)
    e = tables.astype(str) 
    st.dataframe(e)
    st.markdown(xf.get_table_download_link(tables), unsafe_allow_html=True)

with column_2:##### Download various information chart
    st.header ('Download HKEX Data')
    tickers2 = st.text_input("Type in HKEX ticker/tickers in 1234 or 123 or 12 or 1 format")
    tickers2 = tickers2.split(',') 
    tickers2 = map(str.strip, tickers2)
    tickers2 = list(tickers2)
    @st.cache (ttl=300)
    def hkex(tickers2):
        if tickers2 == ['']:
            tables2 = pd.DataFrame()
        else:
            tables2 = []
            for ticker2 in tickers2:
                xf.threaded_gather_data(ticker2, tables2) 
            while len(tables2) < len(tickers2): 
                sleep(0.01)
            tables2 = xf.org_table(tickers2, tables2, row = 0) 
        return tables2
    tables2 = hkex(tickers2)
    ### filter the data using a list generated by input
    filterer = st.text_input("Type in the things your are interested to gather, leave this blank for all info. e.g (mktcap, pe, shr_out)")
    filterer = 'name,' + filterer ## attach short name on top for clarity
    
    if filterer == 'name,':
        tables2 = tables2
    else:
        filterer = filterer.split (',')
        filterer = map(str.strip, filterer)
        tables2 = tables2.loc[filterer]  
    tables2
    st.markdown(xf.get_table_download_link(tables2), unsafe_allow_html=True)
    
st.header ('Download Various Other XueQiu Information')
tickers3 = st.text_input("Type in ticker/tickers")
tickers3 = tickers3.split(',') 
tickers3 = map(str.strip, tickers3)
tickers3 = list(tickers3)
statement3 = st.selectbox(
         'What would you like to download?',
         ('Stock Data', 'Company Data'))
st.write('You selected:', statement3)
@st.cache (ttl=300)
def download_various (tickers3, statement3):
    if tickers3 == ['']:### makes sure the function doesn't run if there is no data inputted
        tables3 = pd.DataFrame()
    elif statement3 == 'Stock Data':
        tables3 = []
        for ticker3 in tickers3:
            xf.infinite_query_threaded_stockdata(ticker3, tables3) 
        while len(tables3) < len(tickers3):
            sleep(0.01)
        tables3 = xf.org_table(tickers3, tables3) 
    else:  ### this is for gathering company introduction
        tables3 = []
        for ticker2 in tickers3:
            xf.infinite_query_threaded_compintro(ticker2, tables3) 
        while len(tables3) < len(tickers3):
            sleep(0.01)
        tables3 = xf.org_table(tickers3, tables3) 
    return tables3
tables3 = download_various(tickers3, statement3) 
tables3
st.markdown(xf.get_table_download_link(tables3), unsafe_allow_html=True)



