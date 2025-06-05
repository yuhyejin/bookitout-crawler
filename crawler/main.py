from flask import Flask, request, jsonify
from crawler_manager import get_crawler
import traceback

app = Flask(__name__)

@app.route('/crawl', methods=['GET'])
def crawl():
    library = request.args.get('library')
    title = request.args.get('title')

    if not library or not title:
        return jsonify({"error": "Missing 'library' or 'title' parameter"}), 400

    crawler = get_crawler(library)
    if crawler is None:
        return jsonify({"error": f"Unsupported library code: {library}"}), 404

    try:
        result = crawler.get_book_status(title)
        return jsonify(result)
    except Exception as e:
        print("[에러 발생]", e)
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8000)
