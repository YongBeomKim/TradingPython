from urllib import parse
from datetime import date
from tqdm import tqdm
import pandas as pd
import requests
import olefile
import json


class G2bStore:
    
    def __init__(self):
        self.url_head = "http://apis.data.go.kr/1230000/BidPublicInfoService02/getBidPblancListInfo"
        self.key_user = "JDTOZUQU3PvzXciumqS%2BATOZY8ycaRUyAgIw5%2FdVybBB1niud03Rgh%2FBHSIJQnm8iCwyr45j2zYU7tGbtxLFCQ%3D%3D"
        self.key_user2 = "JDTOZUQU3PvzXciumqS+ATOZY8ycaRUyAgIw5/dVybBB1niud03Rgh/BHSIJQnm8iCwyr45j2zYU7tGbtxLFCQ=="
        self.url_tail = "&ServiceKey=" + self.key_user # Adding the User Key
        self.parts = ["Servc?", "Thng?", "Frgcpt?", "Cnstwk?"] # 용역, 물품, 외자(국내에서 생산되지 않는 상품/ 용역), 공사 
        
    # API Key 값들의 정보 출력하기
    def get_api_info(self, full_data=False):
        r"""Api 의 Column 내용 테이블 출력하기
        'https://data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15000802'
        """
        url = 'https://data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15000802'
        result_pd = pd.read_html(url)
        result_pd = result_pd[-1]
        if full_data:
            return result_pd
        else:
            key_info = result_pd.iloc[:, :2]
            key_info = key_info.set_index('항목명(영문)')
            return key_info['항목명(국문)'].to_dict()


    # API 데이터 다운로드 함수
    def get_download(self, part=0, date_start=None, date_end=None, page_no=1, 
        num_of_row=5, file_type='json', query_div=1, display_count=False, display_url=False):
        
        r"""나라장터 API 를 활용한 데이터 수집함수
        ::param : part::       수집 대상 (0:용역, 1:물품, 2:외자, 3:공사)
        ::param : date_start:: 수집 시작일
        ::param : date_end::   수집 종료일
        ::param : page_no::    수집 페이지
        ::param : num_of_row:: 1번에 수집 가능한 갯수 (Max:999)
        ::param : file_type::       Json, Xml 선택가능
        ::param : query_div::  (조회구분) 1:등록일시, 2:입찰공고번호, 3:변경일시
        ::param : display_count:: 전체 조회가능 갯수 출력 Mode
        ::return : json, String Total Count Number::"""

        # 1 Params Interpolation : 결측값 보완하기 & 반복횟수 계산 모드시 입력값 보정
        if type(part) != int:
            print("0:용역, 1:물품, 2:외자, 3:공사 필수입력 필요")
            return None
        
        part = self.parts[part] # 목록 수집범위 (0, 1, 2, 3)
        if date_start == None: date_start = date.today().strftime("%Y%m%d")
        if date_end == None: date_end = date.today().strftime("%Y%m%d")
        if display_count: num_of_row = 5
        
        url_query = {
            "inqryBgnDt":date_start + "0000",
            "inqryEndDt":date_end + "2359",
            "numOfRows":num_of_row, # (1회 조회갯수) Max 999
            "inqryDiv":query_div,   # (조회구분) 1:등록일시, 2:입찰공고번호, 3:변경일시
            "pageNo":part,
            'type':file_type,  
        }
        
        # 2 Main Process : Get Download the JSON API DataSet
        url = self.url_head + part + parse.urlencode(url_query, encoding='utf-8', doseq=True) + self.url_tail        
        response = requests.get(url).content.decode('utf-8')
        response_json = json.loads(response)
        
        # 3 Post Process
        # url 을 출력하는 조건
        if display_url: 
            print(url)
        # Return : 조건에 따라 Return 값 다르게 적용하기
        if display_count:
            try:    return response_json['response']['body']['totalCount']
            except: return response_json
        else:
            return response_json


    # API 전체 데이터 반복문 활용 다운로드 함수
    def get_full_download(self, part=0, date_start=None, date_end=None, data_frame=True):
        r""">>> 해당 범위의 모든 나라장터 공고자료 수집기
        date_start 만 "20210101" 과 같은 문자/ 숫자로 입력하면
        현재까지 공고된 데이터 모두 수집 및 출력 한다
        :: return ::  List()"""

        # Pre Process : 반복횟수 계산
        total_counts = self.get_download(part=part, date_start=date_start, date_end=date_end, display_count=True)
        category_name = ["용역","물품","외자","공사"]

        # Main Process : 필요한 갯수만큼 반복해서 전체 결과값 생성
        result_list = []
        for page_no in tqdm(range(1, (total_counts // 900)+2)):
            result_items = self.get_download(part=part, date_start=date_start, date_end=date_end, 
                                             page_no=page_no, num_of_row=900)
            result_list += result_items['response']['body']['items']
        
        # Post Process : to DataFrame and Fltering And Change Kor of Columns 
        if data_frame:
            # 데이터를 DataFrame 으로 변환
            result_df = pd.DataFrame(result_list)

            # 참고 문서 Url 과 문서이름 List(Array) 정리 및 변환하기 (PostgreSQL)
            doc_url = [f"ntceSpecDocUrl{number}"  for number in range(1,11)]
            doc_name = [f"ntceSpecFileNm{number}"  for number in range(1,11)]
            result_df['doc_url'] = [list(filter(lambda x : len(x)>2, 
                result_df.loc[index, doc_url]))  for index in range(len(result_df))]
            result_df['doc_name'] = [list(filter(lambda x : len(x)>2, 
                result_df.loc[index, doc_name]))  for index in range(len(result_df))]
            
            # 유효값 필터링
            filter_columns = ['bidNtceDt','bidBeginDt','bidClseDt',
                'bidNtceNo','bidNtceNm','bidNtceDtlUrl','ntceInsttNm','bidNtceOrd',
                'reNtceYn','rgstTyNm','ntceKindNm','rbidPermsnYn', 'doc_url', 'doc_name']
            result_df = result_df.loc[:,filter_columns]
            
            # Date Time 데이터의 Type 변환
            for col in result_df.columns[:3]:
                result_df[col] = pd.DatetimeIndex(result_df[col])

            # 나라장터 데이터 컬럼 한글로 변경하기
            key_info_dict = self.get_api_info()
            key_info_dict['doc_url'] = '참고문서_url'
            key_info_dict['doc_name'] = '참고문서_name'
            result_df.columns = [key_info_dict[_] for _ in result_df.columns]
            result_df.insert(0,'구분', category_name[part])
            return result_df

        else:
            return result_list

    
    def read_csv(self, file_name, encoding):
        r"""CSV 파일을 불러온 경우,
        1. Date Time 테이블의 속성을 Pandas 로 반꾸기 (필터링 용이)
        2. List Array 데이터를 Python 의 List() 객체로 변환"""
        df = pd.read_csv(file_name, encoding=encoding)
        
        # Pre Pocessing : Date Time 데이터의 Type 변환
        for col in df.columns[1:4]:
            df[col] = pd.DatetimeIndex(df[col])
        
        # Post Processing : 참고문서 url, 파일이름 List() 로 변환
        # https://somjang.tistory.com/entry/Python-str-%ED%98%95%EC%8B%9D%EC%9D%98-list-%EB%AC%B8%EC%9E%90%EC%97%B4-list-%ED%98%95%EC%8B%9D%EC%9C%BC%EB%A1%9C-%EB%B3%80%ED%99%98%ED%95%98%EB%8A%94-%EB%B0%A9%EB%B2%95-str-list-to-list-python
        import ast
        for name in ['url','name']:
            df[f"참고문서_{name}"] = list(map(
                lambda x : ast.literal_eval(x), df[f"참고문서_{name}"]))
        return df