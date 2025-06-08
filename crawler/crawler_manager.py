from juan_crawler import JuanLibraryCrawler
from subong_crawler import SubongLibraryCrawler
from simgok_crawler import SimgokLibraryCrawler

crawler_map = {
    "주안도서관": JuanLibraryCrawler(),
    "인천광역시 수봉도서관": SubongLibraryCrawler(),
    "인천 서구 심곡도서관": SimgokLibraryCrawler(),
    # 다른 도서관 추가 시 여기에 등록
}

def get_crawler(library_code: str):
    return crawler_map.get(library_code)