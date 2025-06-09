import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class CheongnaLakeLibraryCrawler:
    def __init__(self):
        self.URL = "https://www.michuhollib.go.kr/cnl/sch/bsch/list.do?mnidx=414"

    def get_book_status(self, book_title: str):
        # WebDriver 설정 (헤드리스 모드)
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        # Service 객체를 사용하여 WebDriver 초기화
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            print(f"'{book_title}' 책을 위해 청라호수도서관 크롤링 시작...")
            driver.get(self.URL)

            # 페이지가 완전히 로드될 때까지 대기
            WebDriverWait(driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3) # 페이지 로드 후 추가 대기 시간 증가

            # 검색어 입력 필드에 책 제목 입력 (id="searchKeyword")
            search_input = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "searchKeyword"))
            )
            search_input.clear()
            search_input.send_keys(book_title)
            print(f"검색어 '{book_title}' 입력 완료.")

            # 검색 버튼 클릭 (class="libro_search")
            search_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.libro_search"))
            )
            search_button.click()
            print("검색 버튼 클릭 완료.")

            # 검색 결과가 로드될 때까지 대기 (결과 페이지의 #bookSearchList 사용)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "bookSearchList"))
            )
            time.sleep(3) # 결과 로딩 후 추가 대기

            # 검색 결과 파싱
            book_elements = driver.find_elements(By.CSS_SELECTOR, "#bookSearchList > div > ul.prglist > li")
            books_data = []

            if not book_elements:
                print("검색 결과가 없습니다.")
                return []

            for book_element in book_elements:
                title = ""
                author = ""
                publisher = ""
                publication_year = ""
                library = ""
                shelf_location = ""
                registration_number = ""
                isbn = ""
                call_number = ""
                is_available = False
                return_date = None
                is_interlibrary_available = False

                try:
                    title = book_element.find_element(By.CSS_SELECTOR, "p.textOF2.title a").text.strip()
                except:
                    pass

                try:
                    pub_info_text = book_element.find_element(By.CSS_SELECTOR, "span.name").text.strip()
                    parts = pub_info_text.split(' / ')
                    if len(parts) > 0 and "발행연도 -" in parts[0]:
                        publication_year = parts[0].replace("발행연도 - ", "").strip()
                    if len(parts) > 1 and "지음:" in parts[1]:
                        author = parts[1].replace("지음: ", "").strip()
                    if len(parts) > 2:
                        publisher = parts[2].replace(" :", "").strip()

                except:
                    pass

                try:
                    pginfo_elements = book_element.find_elements(By.CSS_SELECTOR, "ul.pginfo li")
                    for info_li in pginfo_elements:
                        if "도서관" in info_li.text:
                            library = info_li.text.replace("도서관", "").strip()
                        elif "자료실" in info_li.text:
                            shelf_location = info_li.text.replace("자료실", "").strip()
                        elif "등록번호" in info_li.text:
                            registration_number = info_li.text.replace("등록번호", "").strip()
                        elif "ISBN" in info_li.text:
                            isbn = info_li.text.replace("ISBN", "").strip()
                        elif "청구기호" in info_li.text:
                            call_number = info_li.text.replace("청구기호", "").strip()
                except:
                    pass

                # '청라호수' 도서관의 책만 필터링
                if library != "청라호수":
                    continue

                try:
                    availability_div = book_element.find_element(By.CSS_SELECTOR, "div.libro_alquilar")
                    availability_text = availability_div.text.strip()
                    
                    # 대출 상태 확인
                    loan = "대출가능" if "대출가능" in availability_text else "대출불가"
                    
                    # 예약 정보 확인
                    reservation_count = "0"
                    reservation_match = re.search(r'예약 (\d+)명', availability_text)
                    if reservation_match:
                        reservation_count = reservation_match.group(1)

                    reservation_status_text = ""
                    try:
                        reser_element = book_element.find_element(By.CSS_SELECTOR, "a.reser")
                        if "no" in reser_element.get_attribute("class"):
                            reservation_status_text = f"예약불가능 예약 {reservation_count}명"
                        else:
                            reservation_status_text = "예약가능"
                    except:
                        # 자료예약 버튼이 없는 경우 (예: 로그인 후 이용 가능한 서비스) 기본값 설정
                        reservation_status_text = f"예약불가능 예약 {reservation_count}명"

                    # 반납예정일 확인
                    return_date = None
                    return_date_match = re.search(r'반납예정일 (\d{4}-\d{2}-\d{2})', availability_text)
                    if return_date_match:
                        return_date = return_date_match.group(1)

                    # 이미지 URL 가져오기
                    image_url = ""
                    try:
                        img_element = book_element.find_element(By.CSS_SELECTOR, "li.centerimg img")
                        image_url = img_element.get_attribute("src")
                    except:
                        pass

                    # 상호대차 가능 여부 확인
                    interlibrary = "불가능"
                    try:
                        interlibrary_element = book_element.find_element(By.CSS_SELECTOR, "a.cambiar")
                        if "no" not in interlibrary_element.get_attribute("class"):
                            interlibrary = "가능"
                    except:
                        pass

                    books_data.append({
                        "title": title,
                        "author": author,
                        "publisher": publisher,
                        "year": publication_year,
                        "loan": loan,
                        "return_date": return_date,
                        "reservation": reservation_status_text,
                        "library": library,
                        "shelf_loc": shelf_location,
                        "call_number": call_number,
                        "interlibrary": interlibrary,
                        "image_url": image_url
                    })

                except Exception as e:
                    print(f"대출 정보 파싱 중 오류: {e}")
                    continue

            return books_data

        except Exception as e:
            print(f"크롤링 중 오류 발생: {e}")
            return []
        finally:
            driver.quit()

