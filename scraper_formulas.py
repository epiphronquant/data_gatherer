# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 14:53:06 2021

@author: angus
"""
from numpy import nan
from time import sleep
import base64
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import multitasking
from bs4 import BeautifulSoup


### Options that allow chrome to run in streamlit
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
def infinite_query(ticker, xq_exten, sleep_time,  freq = "全部",  stock_data = False, statement = False): ### XueQiu God function
    '''A heavily XueQiu customized function that refreshes page until it can gather the needed data
    in: str, str, int, str, bool, bool
    out: dataframe or list of dataframes
    '''
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options) ### use google chrome
    driver.get("https://xueqiu.com/snowman/S/" + ticker + xq_exten) ### go to website
    sleep(1) ### gives time for page to load
    if stock_data == True: ### This is for gathering HKEX stock data
        try:
            int(ticker) ### only HKEX stocks get caught up in this logic
            try:
                button= driver.find_element_by_xpath('/html/body/div/div[2]/div[2]/div[5]/a')### selects button to access HKEX data
                button.click()
            except:
                button= driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[1]/div[3]/a')### selects button to close popup
                button.click()
                button= driver.find_element_by_xpath('/html/body/div/div[2]/div[2]/div[5]/a')### selects button 
                button.click()
        except ValueError:
            pass
    else:
        pass    
    if freq == '全部': 
        pass
    else: ### clicks the respective frequency button
        path = "//span[contains(@class,'btn') and contains(text(), '"+ freq +"')]"
        button= driver.find_element_by_xpath(path)### selects button 
        button.click()
    sleep(sleep_time) ### gives time for page to load. This is customized below and depends on use case
    html = driver.page_source ## gather and read HTML       
    if statement == True: ### only statements data need to be compared, selected and collected
        ### initialize dataframe
        statements = pd.DataFrame()
        ### gathers first chart
        html = driver.page_source ## gather and read HTML    
        statement1 = None
        while statement1 is None: ### keeps on refreshing page until it can gather statement data
            try: 
                statement1 = pd.read_html(html)
            except ValueError:
                driver.refresh()
                sleep(4)
                html = driver.page_source## gather and read HTML
                try: 
                    statement1 = pd.read_html(html) 
                except ValueError:
                    statement1 = None
        statement1 = statement1 [0]
        statement1 = statement1.set_index(statement1.columns [0]) ### sets an index so that the data is merged rather than directly concated
        statements = pd.concat([statements,statement1], ignore_index=False, axis = 1)
        statements = statements.set_index(statements.columns [0]) ### sets an index so that the data is merged rather than directly concated
        statement1l = statement1.values.tolist()
        
        ### press button to gather next chart
        path = "/html/body/div/div[2]/div[2]/div/div[1]/div[2]/span[2]" ## this presses the 下一页 button. It uses copy x-path from chrome inspect
        button= driver.find_element_by_xpath(path)### selects button 
        button.click() 
        sleep(.5)
        
        html = driver.page_source ## gather and read HTML    
        statement2 = pd.read_html(html)
        statement2 = statement2 [0]
        statement2 = statement2.set_index(statement2.columns [0]) ### sets an index so that the data is merged rather than directly concated        
        statement2l = statement2.values.tolist()
        
        ### compare first chart with second chart
        comparison = statement1l == statement2l
        while comparison is False: ### keeps on gathering new charts until the next chart is same as the previous one
            statement2_edit = statement2.iloc [:,2:]
            statements = pd.concat([statements,statement2_edit], ignore_index=False, axis = 1) ### appends to initialized dataframe
            ### gathers first chart
            statement1 = statement2
            statement1l = statement1.values.tolist()        
            ### press button to gather next chart
            path = "/html/body/div/div[2]/div[2]/div/div[1]/div[2]/span[2]" ## this presses the 下一页 button. It uses copy x-path from chrome inspect
            button= driver.find_element_by_xpath(path)### selects button 
            button.click() 
            sleep(1)    
            html = driver.page_source ## gather and read HTML    
            statement2 = pd.read_html(html)
            statement2 = statement2 [0]
            statement2 = statement2.set_index(statement2.columns [0]) ### sets an index so that the data is merged rather than directly concated
            statement2l = statement2.values.tolist()
            comparison = statement1l == statement2l
        statements = statements.reset_index()
        table = statements
    else: ### keeps on refreshing the page until it's possible to gather table data
        table = None
        while table is None:
            try: 
                table = pd.read_html(html)
            except ValueError:
                driver.refresh()
                sleep(4)
                html = driver.page_source## gather and read HTML
                try: 
                    table = pd.read_html(html)
                except ValueError:
                    table = None
    driver.delete_all_cookies()
    driver.quit()
    return table
def convert(chinese): 
    """converts Chinese numbers to int
    in: string
    out: string
    """
    numbers = {'零':0, '一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '壹':1, '贰':2, '叁':3, '肆':4, '伍':5, '陆':6, '柒':7, '捌':8, '玖':9, '两':2, '廿':20, '卅':30, '卌':40, '虚':50, '圆':60, '近':70, '枯':80, '无':90}
    units = {'个':1, '十':10, '百':100, '千':1000, '万':10000, '亿':100000000,'万亿':1000000000000, '拾':10, '佰':100, '仟':1000}
    number, pureNumber = 0, True
    for i in range(len(chinese)):
        if chinese[i] in units or chinese[i] in ['廿', '卅', '卌', '虚', '圆', '近', '枯', '无']:
            pureNumber = False
            break
        if chinese[i] in numbers:
            number = number * 10 + numbers[chinese[i]]
    if pureNumber:
        return number
    number = 0
    for i in range(len(chinese)):
        if chinese[i] in numbers or chinese[i] == '十' and (i == 0 or  chinese[i - 1] not in numbers or chinese[i - 1] == '零'):
            base, currentUnit = 10 if chinese[i] == '十' and (i == 0 or chinese[i] == '十' and chinese[i - 1] not in numbers or chinese[i - 1] == '零') else numbers[chinese[i]], '个'
            for j in range(i + 1, len(chinese)):
                if chinese[j] in units:
                    if units[chinese[j]] >= units[currentUnit]:
                        base, currentUnit = base * units[chinese[j]], chinese[j]
            number = number + base
    return number
def chin_str_split(s):
    tail = s.lstrip('0123456789.')
    head = s[:-len(tail)]
    return head, tail
def convert_table(table):
    """coverts everything beyond the first column with chinese numbers to raw int number
    in: dataframe 
    out: dataframe
    """
    columns = table.columns [1:]
    for column in columns:
        abc = table [column]
        
        abc = abc.astype(str)
        abc3 = pd.DataFrame(chin_str_split(s) for s in abc)
        abc2 = abc3.iloc [:,1]
        abc = abc3.iloc [:,0]

        # abc2 = abc.str[-1]
        # abc = abc.str[:-1]   
        abc2 = '一' + abc2
        abc2 = abc2.astype(str)
        a = []
        for numbers in abc2:
            b = convert (numbers)
            a.append(b)
        a = pd.DataFrame(a, columns = [column])
        abc = pd.DataFrame(abc)
        abc = abc.replace(r'^\s*$', nan, regex=True)
        abc = abc.astype(float)
        df3 = a.mul(abc.values)
        df3 = df3.round(2)
        table [column] = df3
    return table
def to_excel(df):
    """"converts a dataframe to excel
    in: dataframe
    out: processed_data
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index = True, header = False)
    writer.save()
    processed_data = output.getvalue()
    return processed_data
def get_table_download_link(df): ### Hack that allows you to download the dataframe
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download xlsx</a>' # decode b'abc' => abc    
@multitasking.task # Threads the function so it runs (amount of CPU cores)x faster
def infinite_query_threaded_statements(ticker1, tables2, xq_exten, freq):
    """Threads a function where we query, clean and append the data while specifiying which frequency and statement to get.
    in:  str, list, str, str
    out: list of dataframe
    """
    table = infinite_query(ticker1, xq_exten, 1, freq = freq, statement = True)
    table = convert_table(table)
    table = table.T.reset_index(drop=False).T
    table = table.T.reset_index(drop=False).T
    table.iloc[0] = ticker1
    tables2.append (table) ### appends it to the initialized list
@multitasking.task # <== this is all it takes :-)
def infinite_query_threaded_shareholder(ticker1,tables2, xq_exten):
    """Threads a function where we query, clean and append the data for shareholder information.
    in:  str, list, str
    out: list of dataframe
    """
    tables0 = infinite_query(ticker1, xq_exten, 2, freq= '全部')
    tables0 = tables0 [0:2]
    table0 = pd.DataFrame()
    for table in tables0:
        table = table.iloc [:,0:4]
        report = table.columns
        report = report [2]
        report = report [0]
        table.columns = table.columns.droplevel()
        abc = table ['持股数量']
        abc = abc.astype(str)

        abc3 = pd.DataFrame(chin_str_split(s) for s in abc)
        abc2 = abc3.iloc [:,1]
        abc = abc3.iloc [:,0]

        # abc2 = abc.str[-1]
        # abc = abc.str[:-1]   
        
        abc2 = '一' + abc2
        a = []
        for numbers in abc2:
            b = convert (numbers)
            a.append(b)
        a = pd.DataFrame(a, columns = ['持股数量'])
        abc = pd.DataFrame(abc)
        abc = abc.astype(float)
        df3 = a.mul(abc.values)
        df3 = df3.round(0)
        table ['持股数量'] = df3
        table = table.T.reset_index(drop=False).T
        table = table.T.reset_index(drop=False).T
        table.iloc[0] = ticker1
        table = table.reset_index(drop = True)
        table = table.T.reset_index(drop=False).T
        table.iloc[0] = report
        table0 = pd.concat([table0, table])
    table0 = table0.reset_index(drop = True)
    tables2.append(table0)
@multitasking.task 
def infinite_query_threaded_stockdata(ticker2, tables2):
    """Threads a function where we query, clean and append stock data.
    in:  str, list
    out: list of dataframe
    """
    table = infinite_query(ticker2,"", .5, stock_data= True)
    ### clean data
    table = table [0]
    table = table.stack().reset_index()
    table = table.iloc[:,-1]
    table = table.str.split('：', expand = True)
    table = table.set_index(table.columns [0]) ### sets an index so that the data is merged rather than directly concated
    table = table.T.reset_index(drop=False).T
    table.iloc[0] = ticker2
    tables2.append (table) 
@multitasking.task 
def infinite_query_threaded_compintro(ticker2, tables2):
    """Threads a function where we query, clean and append company data.
    in:  str, list
    out: list of dataframe
    """
    table = infinite_query(ticker2,"/detail#/GSJJ", .5)
    table = table [0]
    table = table.iloc [:,0:2]
    table = table.set_index(table.columns [0]) ### sets an index so that the data is merged rather than directly concated
    table = table.T.reset_index(drop=False).T
    table.iloc[0] = ticker2
    tables2.append (table) 
def org_table(tickers, tables, row = 0):
    """Organizes a list of tables into one dataframe in the order of specified tickers.
    Row points to which row to look at in the tables to match with the tickers. Useful for organizing threaded output.
    in:  list of dataframes, list, int
    out: dataframe
    """
    tables8 = pd.DataFrame()
    while len(tickers) > 0:
        y = tickers[0]
        abc = len(tickers)
        abc = list(range(0, abc))
        for number in abc:
            try: 
                tables3 = tables [number]
                x = tables3.iloc[row, 0]
                if x == y:
                    tables8 = pd.concat([tables8,tables3], ignore_index=False, axis = 1)
                    tables = tables[:number]+ tables[number+1:]
                    tickers = tickers[1:]
            except IndexError:
                pass
    return tables8
### formula for HKEX scraping
multipliers = {'K':1000, 'M':1000000, 'B':1000000000}
def string_to_float(string):
    if string[-1].isdigit(): # check if no suffix
        return int(string)
    mult = multipliers[string[-1]] # look up suffix to get multiplier
     # convert number to float, multiply by multiplier, then make int
    return float(string[:-1]) * mult


@multitasking.task
def threaded_gather_data(ticker, output):
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options) ### use google chrome
    url = 'https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=' + str(ticker) +'&sc_lang=en'
    driver.get(url) ### go to website
    sleep(1) ### gives time for page to load. This is a xueqiu specific solution
    html = driver.page_source ## gather and read HTML       
    driver.quit()
    
    soup = BeautifulSoup(html, 'html.parser')   
    summary = soup.find(class_= "company_txt col_summary")
    summary = summary.get_text()
    
    shr_out = soup.find(class_= "col_issued_shares")
    ####!! We assume there will only ever be 2 classes of shares for WVR!!##
    try: 
        shr_out = str(shr_out)
        shr_out = shr_out.split('<br/>')
        shr_out1 = shr_out [0]
        shr_out1 = shr_out1.split('>')
        shr_out1 = shr_out1 [-1]
        shr_out1 = shr_out1.split(' (')
        shr_out1 = shr_out1 [0]
        shr_out1 = shr_out1.replace(',', '')
        shr_out1 = int(shr_out1)
        
        shr_out2 = shr_out [1]
        shr_out2 = shr_out2.split(' (')
        shr_out2 = shr_out2 [0]
        shr_out2 = shr_out2.replace(',', '')
        shr_out2 = int(shr_out2)
        
        shr_out = shr_out1 + shr_out2
    except ValueError:
        shr_out1 = nan
        shr_out2 = nan
        shr_out = shr_out [0]
        shr_out = shr_out.split(' (')
        shr_out = shr_out [0]
        shr_out = shr_out.split('>')    
        shr_out = shr_out [1]
        shr_out = shr_out.replace(',','')
        shr_out = int(shr_out)
    industry = soup.find(class_= "col_industry_hsic")
    industry = industry.get_text()
    industry = industry.split('-')
    industry = [i.strip(' ') for i in industry]
    industry1 = industry [0]
    industry2 = industry [1]
    industry3 = industry [2]
    
    list_date = soup.find(class_= "ico_data col_listing_date")
    list_date = list_date.get_text()
    
    fy_end = soup.find(class_= "ico_data col_financial_year_ends")
    fy_end = fy_end.get_text()
    
    chairman = soup.find(class_= "ico_data ico_f col_chairman")
    chairman = chairman.get_text()
    
    office = soup.find(class_= "ico_data ico_f col_office")
    office = str(office)
    office = office.replace('<br/>', ', ')
    office = office.replace('<span class="ico_data ico_f col_office">', '')
    office = office.replace('</span>', '')
    
    poi = soup.find(class_= "ico_data col_poi")
    poi = poi.get_text()
    
    listing_cat = soup.find(class_= "ico_data ico_f col_listing_cat")
    listing_cat = listing_cat.get_text()
    
    left_list_title = soup.find(class_= "left_list_title")
    
    name = left_list_title.find(class_= "col_name")
    name = name.get_text()
    
    current_price = left_list_title.find(class_= "col_last")
    current_price = current_price.get_text()
    current_price = float(current_price)
    
    prevcls = soup.find(class_= "ico_data col_prevcls")
    prevcls = prevcls.get_text()
    prevcls = prevcls.replace('HK$','')
    prevcls = prevcls.replace('HKD','')
    prevcls = float(prevcls)
    
    open_ = soup.find(class_= "ico_data col_open")
    open_ = open_.get_text()
    open_ = open_.replace('HK$','')
    open_ = float(open_)
    
    turnover = soup.find(class_= "ico_data col_turnover")
    turnover = turnover.get_text()
    turnover = turnover.replace('HK$','')
    turnover = turnover.replace(',','')
    turnover = string_to_float(turnover)
    
    
    volume = soup.find(class_= "ico_data col_volume")
    volume = volume.get_text()
    volume = volume.replace(',','')
    volume = string_to_float(volume)
    
    mktcap = soup.find(class_= "ico_data col_mktcap")
    mktcap = mktcap.get_text()
    mktcap = mktcap.replace('HK$','')
    mktcap = mktcap.replace(',','')
    mktcap = string_to_float(mktcap)
    
    lotsize = soup.find(class_= "ico_data col_lotsize")
    lotsize = lotsize.get_text()
    lotsize = lotsize.replace('HK$','')
    lotsize = lotsize.replace(',','')
    lotsize = int(lotsize)
    
    bid = soup.find(class_= "ico_data col_bid")
    bid = bid.get_text()
    bid = bid.replace('HK$','')
    bid = bid.replace(',','')
    bid = float(bid)
    
    ask = soup.find(class_= "ico_data col_ask")
    ask = ask.get_text()
    ask = ask.replace('HK$','')
    ask = ask.replace(',','')
    ask = float(ask)
    
    eps = soup.find(class_= "ico_data col_eps")
    eps = eps.get_text()
    
    pe = soup.find(class_= "ico_data col_pe")
    pe = pe.get_text()
    pe = pe.replace('x','')
    try:
        pe = float(pe)
    except ValueError:
        pass
    
    divyield = soup.find(class_= "ico_data col_divyield")
    divyield = divyield.get_text()
    
    high52 = soup.find(class_= "col_high52")
    high52 = high52.get_text()
    high52 = high52.replace('HK$','')
    high52 = high52.replace(',','')
    high52 = float(high52)
    
    low52 = soup.find(class_= "col_low52")
    low52 = low52.get_text()
    low52 = low52.replace('HK$','')
    low52 = low52.replace(',','')
    low52 = float(low52)
    
    abc = [["ticker", ticker],["name",name],["class_a_shr", shr_out1],["class_b_shr",shr_out2], ["ask", ask],["bid", bid],["chairman", chairman],["current_price", current_price],["divyield", divyield],["eps", eps],["fy_end", fy_end],["high52", high52],["industry1", industry1], ["industry2", industry2], ["industry3", industry3],["list_date", list_date],["listing_cat", listing_cat],["lotsize", lotsize],["low52", low52],["mktcap", mktcap],["office", office],["open_", open_],["pe", pe],["poi", poi],["prevcls", prevcls],["shr_out", shr_out],["summary", summary],["turnover", turnover],["volume", volume]]
    abcd = pd.DataFrame(abc)
    abcd = abcd.set_index(abcd.columns[0])
    output.append(abcd)
