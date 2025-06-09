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
import re
from selenium.webdriver.common.keys import Keys

class SimgokLibraryCrawler:
    def get_book_status(self, book_title: str) -> List[Dict]:
        options = Options()
        options.add_argument("--headless=new")  # headless 모드 활성화
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            # 1. 새로운 검색 페이지 접속
            driver.get("https://www.issl.go.kr/sch/bsch/view.do?mnidx=1597")
            
            # 초기 페이지 로드 완료 대기
            WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            time.sleep(2) # 페이지 로드 후 추가 대기

            # 2. 검색 입력 필드와 검색 버튼 찾기 및 검색 수행
            search_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "searchKeyword")) # 검색 필드 ID
            )
            search_input.clear()
            search_input.send_keys(book_title)

            # 검색 버튼 클릭 대신 fn_bookSearch() JavaScript 함수 직접 호출
            driver.execute_script("fn_bookSearch();")
            time.sleep(3) # 검색 결과 로딩 대기

            # 3. 결과 로딩 대기: bookSearchList 내부에 첫 번째 li 요소가 나타날 때까지 대기
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#bookSearchList li"))
            )
            time.sleep(3) # 결과 내용이 완전히 로드될 수 있도록 추가 대기 시간 증가

            # 4. 결과 파싱
            soup = BeautifulSoup(driver.page_source, "html.parser")
            book_items = soup.select("#bookSearchList li")

            results = []
            for item in book_items:
                try:
                    title = item.select_one(".title").text.strip()
                    info_tags = item.select(".libinfo i")
                    
                    # 1. full_status_text, loan, return_date, reservation 추출
                    # 대출 상태를 포함하는 span.red에서 대출 상태 추출
                    loan_element = item.select_one("span.red")
                    loan = loan_element.text.strip() if loan_element else "정보 없음"

                    # span.red의 부모 태그에서 전체 상태 텍스트 추출
                    full_status_text = loan_element.find_parent().text.strip() if loan_element and loan_element.find_parent() else ""

                    # 도서관 이름 추출
                    library = "정보 없음"
                    for tag in info_tags:
                        if "도서관:" in tag.text:
                            library = tag.text.replace("도서관:", "").strip()
                            break

                    # 심곡도서관 책만 처리
                    if library == "심곡":
                        author = info_tags[0].text.replace("저자:", "").strip() if len(info_tags) > 0 else ""
                        publisher = info_tags[1].text.replace("출판사:", "").strip() if len(info_tags) > 1 else ""
                        year = info_tags[2].text.replace("발행연도:", "").strip() if len(info_tags) > 2 else ""
                        shelf_loc = info_tags[4].text.replace("자료실:", "").strip() if len(info_tags) > 4 else ""
                        call_number = info_tags[5].text.replace("청구기호:", "").strip() if len(info_tags) > 5 else ""
                        
                        # 이미지 URL 추출
                        img_tag = item.select_one("img")
                        image_url = None
                        if img_tag and img_tag.get("src"):
                            relative_image_url = img_tag.get("src")
                            if relative_image_url.startswith("//"):
                                image_url = "https:" + relative_image_url
                            elif relative_image_url.startswith("/"):
                                image_url = "https://www.issl.go.kr" + relative_image_url
                            else:
                                image_url = relative_image_url # 이미 절대경로인 경우

                        # 반납예정일 추출
                        return_date = None
                        return_date_match = re.search(r"반납예정일 (\d{4}-\d{2}-\d{2})", full_status_text)
                        if return_date_match:
                            return_date = return_date_match.group(1)

                        # 예약 여부 추출 및 형식 맞춤
                        reservation = "정보 없음"
                        
                        # "예약하기" 버튼의 활성화 상태 확인 (더 견고한 방법 사용)
                        reserve_button = None
                        librobtn_div = item.select_one("div.librobtn")
                        if librobtn_div:
                            for a_tag in librobtn_div.find_all('a'):
                                if '예약하기' in a_tag.get_text():
                                    reserve_button = a_tag
                                    break

                        is_reserve_button_active = False
                        if reserve_button and "librobtnno" not in reserve_button.get("class", []):
                            is_reserve_button_active = True

                        # full_status_text에서 총 예약 가능 인원수 추출 (예: '예약 3명'에서 3)
                        total_capacity = None
                        reservation_match = re.search(r"예약 (\d+)명", full_status_text)
                        if reservation_match:
                            total_capacity = int(reservation_match.group(1))
                        
                        if total_capacity is not None:
                            if is_reserve_button_active:
                                # 예약하기 버튼이 활성화되어 있으면, 1개 자리가 비어있다고 가정
                                current_reserved = total_capacity - 1
                                if current_reserved < 0: # 음수가 되지 않도록 최소 0명으로 설정
                                    current_reserved = 0
                                reservation = f"예약가능({current_reserved}/{total_capacity})"
                            else: # 버튼이 비활성화됨
                                # 예약하기 버튼이 비활성화되어 있으면, 모든 자리가 찼다고 가정
                                reservation = f"예약불가({total_capacity}/{total_capacity})"
                        else: # '예약 N명' 정보가 없는 경우
                            if is_reserve_button_active:
                                reservation = "예약가능"
                            else:
                                reservation = "예약불가"

                        # 2. 상호대차 여부 추출 (div.librobtn 내의 링크 활성화 여부로 판단)
                        interlibrary = "정보 없음"
                        librobtn_div = item.select_one("div.librobtn")
                        if librobtn_div:
                            interlibrary_link = None
                            for a_tag in librobtn_div.find_all('a'):
                                if '상호대차' in a_tag.get_text():
                                    interlibrary_link = a_tag
                                    break

                            if interlibrary_link:
                                if "librobtnno" in interlibrary_link.get("class", []):
                                    interlibrary = "불가능"
                                else:
                                    interlibrary = "가능"

                        results.append({
                            "title": title,
                            "author": author,
                            "publisher": publisher,
                            "year": year,
                            "loan": loan,
                            "return_date": return_date,
                            "reservation": reservation,
                            "library": library,
                            "shelf_loc": shelf_loc,
                            "call_number": call_number,
                            "interlibrary": interlibrary,
                            "image_url": image_url
                        })
                except Exception as e:
                    print(f"[파싱 오류] {e}")
                    continue

            return results

        except Exception as e:
            print("[심곡 크롤링 오류]", e)
            driver.save_screenshot("simgok_error.png")
            return []
        finally:
            driver.quit()
