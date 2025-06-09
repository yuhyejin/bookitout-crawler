from juan_crawler import JuanLibraryCrawler
from subong_crawler import SubongLibraryCrawler
from simgok_crawler import SimgokLibraryCrawler
from cheongnalake_crawler import CheongnaLakeLibraryCrawler
from cheongnainternational_crawler import CheongnaInternationalLibraryCrawler

crawler_map = {
    "인천광역시교육청주안도서관": JuanLibraryCrawler(),
    "인천광역시 수봉도서관": SubongLibraryCrawler(),
    "인천 서구 심곡도서관": SimgokLibraryCrawler(),
    "청라호수도서관": CheongnaLakeLibraryCrawler(),
    "청라국제도서관": CheongnaInternationalLibraryCrawler(),
    # 다른 도서관 추가 시 여기에 등록
}

def get_crawler(library_code: str):
    return crawler_map.get(library_code)