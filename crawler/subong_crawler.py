from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from html import unescape
from typing import List, Dict
import time


class SubongLibraryCrawler:
    def get_book_status(self, book_title: str) -> List[Dict]:
        options = Options()
        # options.add_argument("--headless=new")  # 개발 중에는 꺼두기
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            # 1. 메인 페이지 접속
            driver.get("https://www.imla.kr/sb/index.do?curl=/jsp/book_search/best_search.jsp?bbsId=43&menu1=2&menu2=43&scd=2")

            # 2. iframe 전환
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "WrittenPublic"))
            )

            # 3. 책 제목 입력
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "VALUE_1"))
            )
            search_input.clear()
            search_input.send_keys(book_title)

            # 4. 검색 버튼 클릭
            search_button = driver.find_element(By.CLASS_NAME, "search_btn")
            search_button.click()

            # 5. 결과 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "book_data_wrap"))
            )
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()

            book_blocks = soup.find_all("div", class_="book_data_wrap")
            print(f"[수봉 결과 수]: {len(book_blocks)}")

            results = []
            for book in book_blocks:
                try:
                    title = book.find("input", {"name": "pTitle"})["value"].strip()
                    author = book.find("input", {"name": "pAuthor"})["value"].strip()
                    publisher = book.find("input", {"name": "pPublisher"})["value"].strip()
                    library = book.find("input", {"name": "pLibName"})["value"].strip()
                    shelf_loc = book.find("input", {"name": "pShelfLoc"})["value"].strip()

                    raw_loan = book.find("input", {"name": "lonely"})["value"]
                    loan = "대출불가" if "대출중" in unescape(raw_loan) else "대출가능"

                    reserve_button = book.find("input", {"value": "대출중도서예약"})
                    reservation = "예약가능" if reserve_button else "예약불가"

                    results.append({
                        "title": title,
                        "author": author,
                        "publisher": publisher,
                        "loan": loan,
                        "reservation": reservation,
                        "library": library,
                        "shelf_loc": shelf_loc
                    })

                except Exception as e:
                    print(f"[파싱 오류] {e}")
                    continue

            return results

        except Exception as e:
            print("[수봉 크롤링 오류]", e)
            driver.quit()
            return []
