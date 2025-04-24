from flask import Flask, jsonify, send_from_directory, request
import json
import qq_reader_crawler

# 创建 Flask 应用实例
app = Flask(__name__)

JSON_FILE_PATH = 'current_books.json'
INFO_FILE = 'info.json'
NOTIFICATION_HISTORY_FILE = 'notification_history.log'


@app.route('/')
def serve_html():
    return send_from_directory('static', 'index.html')


# 重新加载数据
@app.route('/api/load', methods=['GET'])
def load_data():
    qq_reader_crawler.main()
    return jsonify("{'msg': 'success'}"), 200


# 定义 API 路由，处理 GET 请求
@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        # 读取 JSON 文件
        data = qq_reader_crawler.load_file_data(JSON_FILE_PATH)
        info = qq_reader_crawler.load_file_data(INFO_FILE)
        notification_history = []
        with open(NOTIFICATION_HISTORY_FILE, 'r', encoding='utf-8') as file:
            notification_history = [line.strip() for line in file.readlines()]
        # 返回 JSON 数据，状态码 200 表示成功
        return jsonify({
            'data': data,
            'info': info,
            'notification_history': notification_history[::-1]
        }), 200
    except FileNotFoundError:
        # 如果文件不存在，返回错误信息，状态码 404
        return jsonify({"error": "JSON file not found"}), 404
    except json.JSONDecodeError:
        # 如果 JSON 格式错误，返回错误信息，状态码 400
        return jsonify({"error": "Invalid JSON format"}), 400

@app.route('/api/author', methods=['DELETE'])
def delete_authro():
    will_delete_author = request.args.get('author')

    info = qq_reader_crawler.load_file_data(INFO_FILE)
    follow_authors = set(info.get('follow_authors', []))
    info['follow_authors'] = [follow_author for follow_author in follow_authors if follow_author != will_delete_author]
    qq_reader_crawler.save_data(info, INFO_FILE)
    qq_reader_crawler.update_follows()

    return jsonify("{'msg': 'success'}"), 200


@app.route('/api/author', methods=['POST'])
def add_authro():
    will_add_author = request.get_json().get('author')

    info = qq_reader_crawler.load_file_data(INFO_FILE)
    follow_authors = set(info.get('follow_authors', []))
    if will_add_author not in follow_authors:
        follow_authors.add(will_add_author)
    info['follow_authors'] = list(follow_authors)
    qq_reader_crawler.save_data(info, INFO_FILE)
    qq_reader_crawler.update_follows()

    return jsonify("{'msg': 'success'}"), 200


@app.route('/api/sub', methods=['POST'])
def sub_book():
    book_url = request.get_json().get('url')
    is_sub = request.get_json().get('is_sub')

    if book_url is not None and is_sub is not None:
        info = qq_reader_crawler.load_file_data(INFO_FILE)
        follow_books = set(info.get('follow_books', []))
        if is_sub:
            follow_books.add(book_url)
        else:
            follow_books.discard(book_url)
        info['follow_books'] = list(follow_books)
        qq_reader_crawler.save_data(info, INFO_FILE)
        qq_reader_crawler.update_follows()

    return jsonify("{'msg': 'success'}"), 200


# 运行 Flask 应用
if __name__ == '__main__':
    app.run(debug=True, port=5001)