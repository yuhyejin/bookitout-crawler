from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import List, Dict
import time

class SimgokLibraryCrawler:
    def get_book_status(self, book_title: str) -> List[Dict]:
        options = Options()
        # options.add_argument("--headless=new")  # 디버깅 중엔 주석
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            driver.get("https://www.issl.go.kr/sch/bsch/list.do?mnidx=1597")
            
            time.sleep(0.3)

            # 1. 심곡도서관 체크박스 클릭
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "shLibCk_1_4"))
            )
            if not checkbox.is_selected():
                checkbox.click()
                time.sleep(0.5)
                
            driver.execute_script("window.scrollBy(0, 100)")
            time.sleep(0.3)
            
            
            print("111111")
            driver.refresh()
            
            # 2. 검색어 입력
            search_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "searchReKeyword"))
            )
            print("22222")
            driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
            time.sleep(0.3)
            print("333333")
            search_input.clear()
            search_input.send_keys(book_title)
            
            print("dsfssf")

            # 3. 검색 버튼 클릭 (함수 호출을 트리거하는 버튼)
            search_button = driver.find_element(By.XPATH, "//button[contains(text(), '검색')]")
            search_button.click()

            # 4. 결과 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "bookSearchList"))
            )
            time.sleep(1)

            # 5. 결과 파싱
            soup = BeautifulSoup(driver.page_source, "html.parser")
            book_items = soup.select("#bookSearchList li")

            results = []
            for item in book_items:
                try:
                    title = item.select_one(".title").text.strip()
                    info_tags = item.select(".libinfo i")
                    status = item.select_one("span.red")

                    results.append({
                        "title": title,
                        "author": info_tags[0].text.replace("저자:", "").strip() if len(info_tags) > 0 else "",
                        "publisher": info_tags[1].text.replace("출판사:", "").strip() if len(info_tags) > 1 else "",
                        "year": info_tags[2].text.replace("발행연도:", "").strip() if len(info_tags) > 2 else "",
                        "library": info_tags[3].text.replace("도서관:", "").strip() if len(info_tags) > 3 else "",
                        "shelf_loc": info_tags[4].text.replace("자료실:", "").strip() if len(info_tags) > 4 else "",
                        "call_number": info_tags[5].text.replace("청구기호:", "").strip() if len(info_tags) > 5 else "",
                        "loan": status.text.strip() if status else "정보 없음"
                    })
                except Exception as e:
                    print("[파싱 오류]", e)
                    continue

            return results

        except Exception as e:
            print("[심곡 크롤링 오류]", e)
            driver.save_screenshot("simgok_error.png")
            return []
        finally:
            driver.quit()
