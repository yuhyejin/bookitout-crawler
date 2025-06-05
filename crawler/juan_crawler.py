from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from base_crawler import LibraryCrawler

class JuanLibraryCrawler(LibraryCrawler):
    def get_book_status(self, book_title: str) -> List[Dict]:
        base_url = "https://lib.ice.go.kr/juan/intro/search/index.do?"
        params = {
            'search_type': 'L_TITLE',
            'search_text': book_title,
            'booktype': 'BOOK',
            'rowCount': '10'
        }

        url = base_url + urlencode(params)
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        results = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            books = soup.find_all('div', class_='row')

            for book in books:
                title_tag = book.find('a', class_='name')
                title = title_tag.text.strip() if title_tag else "제목 없음"

                loan_status = "정보 없음"
                return_date = "정보 없음"
                reservation_status = "정보 없음"

                table = book.find('table')
                if table:
                    td_tags = table.find_all('td')
                    for i, td in enumerate(td_tags):
                        text = td.text.strip()
                        if '대출' in text:
                            loan_status = text
                        elif i == 1:
                            return_date = text
                        elif i == 2: 
                            if td.find('a', href="#sangho"):
                                interlibrary = "상호대차가능"
                            else:
                                interlibrary = "상호대차불가능"
                        elif '예약' in text:
                            reservation_status = text

                results.append({
                    'title': title,
                    'loan': loan_status,
                    'return_date': return_date,
                    'reservation': reservation_status,
                    'interlibrary': interlibrary
                })

        return results