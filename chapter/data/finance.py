import pandas as pd
import json, requests, datetime


def bok_eos_api(code='', counts=10000, date_gap='MM', date_start='20011201', date_end=None, code2="?", code3="?"):

    r"""한국은행 OPENAPI 수집기"""
    if date_end == None: date_end = datetime.date.today().strftime("%Y%m%d") # 오늘날짜
    # Process 1 : api key 값 추출
    # with open('./_keys.json', 'r') as f:
    #     apiKey = json.loads(f.read())['bokey']
    apiKey = "YOWLAS8MI7X427J1231C"

    # API link 주소 생성기
    url = f'http://ecos.bok.or.kr/api/StatisticSearch/{apiKey}/json/kr/1/{counts}/{code}/{date_gap}/{date_start}/{date_end}/{code2}/{code3}'
    response = requests.get(url).content.decode('utf-8')
    response_dict = json.loads(response)
    response_key  = list(response_dict.keys())[0]
    
    # 유효값을 호출한 경우
    if response_key == 'StatisticSearch':
        response_data = response_dict[response_key]['row'] # 유효값 Data 추출하기
        response_dataframe = pd.DataFrame(response_data) 
        response_dataframe['DATA_VALUE'] = list(  # DATA_VALUE 텍스트를 숫자로 변환
            map(lambda x : float(x),  response_dataframe['DATA_VALUE'])) 
       
        # 월간 정보인 경우, 날짜값 추가
        # https://stackoverflow.com/questions/37354105/find-the-end-of-the-month-of-a-pandas-dataframe-series
        if date_gap == 'MM':
            response_dataframe['TIME'] = pd.to_datetime(
                response_dataframe['TIME'], format='%Y%m')
        
        # 내부에 여러개 테이블이 추가되어 있는 경우, 내용 출력하기
        if len(set(response_dataframe['ITEM_CODE1'])) > 1:
            print(f"Code2 items : {sorted(set(response_dataframe['ITEM_CODE1']))}")
        if len(set(response_dataframe['ITEM_CODE2'])) > 1:
            print(f"Code3 items : {sorted(set(response_dataframe['ITEM_CODE2']))}")
        return response_dataframe

    # 오류값이 호출된 경우
    else:
        print(response_dict)
        return None
    
    
import os
import pandas as pd
from datetime import date


class StockCSV:

    def __init__(self):
        self.code = '005930'
        self.date_start = '2010-01-01'
        self.date_end = str(date.today())


    def finance(self, code=None, date_start=None, date_end=None, file_name=None, force_update=False):

        r'''Finance Data Reacer : CSV file save & loader
        :param code: Stock Code
        :param date_start, date_end: "2020-02-02"
        :param file_name: Saved file name
        :param force_update: Over write even if exist file
        https://github.com/FinanceData/FinanceDataReader/blob/master/README.md'''
        
        # Iterpolated Params
        if code == None: code = self.code
        if date_start == None: date_start = self.date_start
        if date_end == None: date_end = datetime.date.today().strftime("%Y%m%d")
        if file_name == None: file_name = f"{code}.csv"
        
        # case 1 : 파일을 지정한 경우
        if file_name:

            ## 01 Loading from CSV
            if os.path.isfile(file_name):     # Checking the File exist
                data = pd.read_csv(file_name)
                data['Date'] = pd.to_datetime(data['Date']) # datetime 포맷
                data = data.set_index('Date') # 변경된 컬럼을 Index 로 설정
            ## 02 Loading from Py Module API
            else:                             # if not, download the data
                from FinanceDataReader import DataReader as fdr
                data = fdr(code, date_start, date_end).reset_index()
                data.to_csv(file_name, index=None)
                data = data.set_index('Date')

        # case 2 : 강제 업데이트 및 파일을 저장하지 않은경우
        elif force_update:
            from FinanceDataReader import DataReader as fdr
            data = fdr(code, date_start, date_end)            
        else:
            from FinanceDataReader import DataReader as fdr
            data = fdr(code, date_start, date_end)            
        return data
    
    
    def yahoo(self, code=None, 
              date_start=None, date_end=None, 
              file_name=None, force_update=False):
        r'''Yahoo Finance : CSV file save & loader
        :param code: Stock Code
        :param date_start, date_end: "2020-02-02"
        :param file_name: Saved file name
        :param force_update: Over write even if exist file
        '''

        # Iterpolated Params
        if code == None: code = self.code
        if date_start == None: date_start = self.date_start
        if date_end == None: date_end = datetime.date.today().strftime("%Y%m%d")
        if file_name == None: file_name = f"{code}.csv"

        
        # case 1 : 파일을 지정한 경우
        if file_name:
            ## 01 Loading from CSV
            if os.path.isfile(file_name):  # Checking the File exist
                data = pd.read_csv(file_name)
                data['Date'] = pd.to_datetime(data['Date']) # datetime 포맷 변경
                data = data.set_index('Date')               # 변경된 컬럼을 Index 로 설정
            ## 02 Loading from Py Module API
            else:  # if not, download the data
                import yfinance as yf
                data = yf.download(code, start=date_start, end=date_end,
                    progress=False, auto_adjust=True).reset_index()
                data.to_csv(file_name, index=None)
                data = data.set_index('Date')

        # case 2 : 강제 업데이트 및 파일을 저장하지 않은경우
        elif force_update:
            import yfinance as yf
            data = yf.download(code, start=date_start, end=date_end,
                progress=False, auto_adjust=True) #.reset_index()
        else:
            import yfinance as yf
            data = yf.download(code, start=date_start, end=date_end,
                progress=False, auto_adjust=True) #.reset_index()
        return data