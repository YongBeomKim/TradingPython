import re
from tqdm import tqdm
from urllib import parse, request
from lxml.html import fromstring, tostring
from collections import OrderedDict

# Django Aladin
class aladin:

    def __init__(self):
        self.browser = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.5 Safari/534.55.3"
        self.url_head = "https://www.aladin.co.kr/m/msearch.aspx?"

    def resp_url(self, token:str, encoding='utf-8', page='1'):
        r"""알라딘 중고책 검색결과 크롤링 (모바일은 25개만 출력)
        :param token: 검색어(한글)
        :param encoding: utf-8, euc-kr 택일
        :return: response text"""
        query = {'SearchWord':token, 'SearchTarget':'UsedStore',
                 'SortOrder':'5', 'ViewRowCount':'50', 'page':page}
        head  = "https://www.aladin.co.kr/m/msearch.aspx?"
        query = parse.urlencode(query, encoding=encoding, doseq=True)
        return request.urlopen(request.Request(
            self.url_head+query,
            headers = {'User-Agent':self.browser})).read().decode(encoding)

    def lxml_items(self, html_resp):
        """크롤링 html 에서 itme 내용을 lxml 로 추출하기"""
        html_lxml   = fromstring(html_resp)
        result_list = []
        books = html_lxml.xpath('.//div[@id="Search3_Result"]/div[@class="browse_list_box "]/table')
        for book in books:
            texts = [_.text_content().strip()  for _ in book.xpath('.//ul[@class="b_list2"]/li')[:2]]
            title = texts[0].replace('[중고]','')
            for _ in book.xpath('.//li[@class="pb_title_b"]/div/a'):
                result = OrderedDict()
                result['title'] = title
                result['image'] = book.xpath('.//img[@class="i_cover"]')[0].get('src')
                result['publish'] = texts[1].split('|')[1].strip()
                result['publish_date'] = texts[1].split('|')[-1].strip()
                result['market'] = '알라딘'
                result['area'] = _.text_content()
                # href url link ...
                href = 'https://www.aladin.co.kr'+(_.get('href'))
                result['area_info'] = href
                result['area_price'] = href
                result_list.append(result)
        return result_list

    def page_count(self, html_resp):
        """total_page number Counting"""
        # Table 의 Header 에 표시된 검색갯수
        html_lxml  = fromstring(html_resp)
        html_head  = html_lxml.xpath('//div[@id="scrollTarget"]')[0]  # 결과 Table 선택
        html_head  = "".join(html_head.xpath('.//ul[@class="new2017_nav_u"]/li//text()'))
        item_count = "".join(re.findall(r"중고매장\([\d]+\)", html_head))
        print(item_count)
        item_count = int("".join(re.findall(r"[\d]+", item_count)))
        item_count = item_count - 2 # 전체 Item 갯수
        if item_count % 25 == 0: return item_count // 25 #, item_count % 25
        else: return (item_count // 25) + 1 #, item_count % 25
        
    def get_items(self, token):
        """크롤링 대상 페이지를 반복하며 작업 함수를 실행"""
        resp     = self.resp_url(token)
        page_num = self.page_count(resp)
        print(f"Crawling : {page_num} pages")
        if page_num == 1: # 결과값 1페이지에 모두 있을 때
            result = self.lxml_items(resp)
        else:             # 다른 페이지에도 있을 때
            result = self.lxml_items(resp)
            for i in tqdm(range(2, page_num+1)):
                try:
                    resp    = self.resp_url(token, page=str(i))
                    result += self.lxml_items(resp)
                except: pass
        return result
    

class yes24:
    
    def __init__(self):
        self.browser = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
        self.area_code = {
            "1":"강남점", "2":"목동점", "6":"홍대점", "8":"기흥점", "11":"강서NC"
        }

    def get_items(self, token:str):
        result = []
        for k, v in self.area_code.items():
            try:
                result += self.used_yes(token, code=int(k))
            except: pass
        return result
        
    def used_yes(self, token:str, code:str, encoding='euc-kr', page='1'):
        r"""yes24 중고책 검색결과 크롤링
        :param token: 검색어(한글)
        :param encoding: utf-8, euc-kr 택일
        :return: response text"""
        # Web Resp
        query = {"searchText" : token}
        query = parse.urlencode(query, encoding = encoding)
        url = f"http://www.yes24.com/Mall/UsedStore/Search?STORE_CODE={code:03d}&"
        url = url + f"{query}&sortBy=RECENT_DATE&pageNumber={page}&pageSize=200&"
        html_resp = request.urlopen(request.Request(
            url, headers={'User-Agent':self.browser})).read().decode(encoding)
        # Resp Html 에서 lxml 추출 (ul id="ulResult")
        html_lxmls = fromstring(html_resp)
        html_lxmls = html_lxmls.xpath('.//ul[@id="ulResult"]/li')
        # print(html_lxmls)
        result_list = []
        for html_lxml in html_lxmls:
            try:
                html_lxml_temp = html_lxml.xpath('.//div[@class="storeG_info"]')[0]
                title  = html_lxml_temp.xpath('.//strong[@class="name"]')[0].text_content().strip()
                result = OrderedDict()  # 책정보 Area
                result['title'] = title
                result['image'] = html_lxml.xpath('.//div[@class="storeG_img"]//img')[0].get('src')
                info = [_.strip() for _ in html_lxml_temp.xpath('.//p[@class="storeG_pubGrp"]')[0].text_content().split('|')]
                result['publish']      = info[1]
                result['publish_date'] = info[-1]
                result['market'] = 'yes24'
                result['area']  = self.area_code[str(code)]
                result['area_info']  = html_lxml_temp.xpath('.//div[@class="storeG_loca"]//dd')[0].text_content().strip()
                result['area_price'] = html_lxml_temp.xpath('.//p[@class="storeG_price"]')[0].text_content()
                result_list.append(result)
            except: pass
        return result_list