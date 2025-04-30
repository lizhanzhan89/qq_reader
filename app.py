from flask import Flask, jsonify, render_template, request
import json
import qq_reader_crawler
from apscheduler.schedulers.background import BackgroundScheduler
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime, timedelta

# 创建 Flask 应用实例
app = Flask(__name__)

JSON_FILE_PATH = 'data/current_books.json'
INFO_FILE = 'data/info.json'
NOTIFICATION_HISTORY_FILE = 'data/notification_history.log'
NEW_BOOK_HISTORY_FILE = 'data/new_book_history.json'

# 确保日志目录存在
os.makedirs('logs', exist_ok=True)

# 配置根日志记录器
class ShangHaiTimeFormatter(logging.Formatter):
    """自定义日志格式化器，使用上海时间"""
    
    def formatTime(self, record, datefmt=None):
        utc_dt = datetime.utcfromtimestamp(record.created)
        shanghai_dt = utc_dt + timedelta(hours=8)
        if datefmt:
            return shanghai_dt.strftime(datefmt)
        return shanghai_dt.strftime('%Y-%m-%d %H:%M:%S')

# 创建一个按天轮转的文件处理器
file_handler = TimedRotatingFileHandler(
    filename='logs/app.log',
    when='midnight',
    interval=1,
    backupCount=30,  # 保留30天的日志
    encoding='utf-8'
)
file_handler.suffix = "%Y-%m-%d.log"

# 设置日志格式
formatter = ShangHaiTimeFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# 配置根日志记录器
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

def my_scheduled_job():
    qq_reader_crawler.main()
    logger.info(f"定时任务执行: {qq_reader_crawler.get_shanghai_time()}")

scheduler = BackgroundScheduler()
scheduler.add_job(my_scheduled_job, 'interval', hours=1)
scheduler.start()


@app.route('/')
def index():
    return render_template('index.html')


# 重新加载数据
@app.route('/api/load', methods=['GET'])
def load_data():
    logger.info("手动触发数据加载")
    qq_reader_crawler.main()
    return jsonify("{'msg': 'success'}"), 200


# 定义 API 路由，处理 GET 请求
@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        # 读取 JSON 文件
        data = qq_reader_crawler.load_file_data(JSON_FILE_PATH)
        info = qq_reader_crawler.load_file_data(INFO_FILE)
        new_book_history = qq_reader_crawler.load_file_data(NEW_BOOK_HISTORY_FILE)
        notification_history = []
        with open(NOTIFICATION_HISTORY_FILE, 'r', encoding='utf-8') as file:
            notification_history = [line.strip() for line in file.readlines()]
        # 返回 JSON 数据，状态码 200 表示成功
        return jsonify({
            'data': data,
            'info': info,
            'new_book_history': new_book_history,
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
    logger.info(f"删除作者: {will_delete_author}")

    info = qq_reader_crawler.load_file_data(INFO_FILE)
    follow_authors = set(info.get('follow_authors', []))
    info['follow_authors'] = [follow_author for follow_author in follow_authors if follow_author != will_delete_author]
    qq_reader_crawler.save_data(info, INFO_FILE)
    qq_reader_crawler.update_follows()

    return jsonify("{'msg': 'success'}"), 200


@app.route('/api/author', methods=['POST'])
def add_authro():
    will_add_author = request.get_json().get('author')
    logger.info(f"添加作者: {will_add_author}")

    info = qq_reader_crawler.load_file_data(INFO_FILE)
    follow_authors = set(info.get('follow_authors', []))
    if will_add_author not in follow_authors:
        follow_authors.add(will_add_author)
    info['follow_authors'] = list(follow_authors)
    qq_reader_crawler.save_data(info, INFO_FILE)
    qq_reader_crawler.update_follows()

    return jsonify("{'msg': 'success'}"), 200

@app.route('/api/book', methods=['POST'])
def add_book():
    book_id = request.get_json().get('book_id')
    will_add_book_url = f'//book.qq.com/book-detail/{book_id}'
    logger.info(f"添加书籍: {book_id}")

    info = qq_reader_crawler.load_file_data(INFO_FILE)
    follow_books = info.get('follow_books', [])
    if will_add_book_url not in [fb['url'] for fb in follow_books]:
        follow_books.append({
            'url': will_add_book_url,
            'status': 'new'
        })
    info['follow_books'] = follow_books

    books = qq_reader_crawler.load_file_data(JSON_FILE_PATH)
    books = [book for book in books if book['url'] != will_add_book_url]
    will_add_book = qq_reader_crawler.crawl_detail_page(will_add_book_url)
    will_add_book['is_follow'] = True
    books.append(will_add_book)

    qq_reader_crawler.save_data(info, INFO_FILE)
    qq_reader_crawler.save_data(books, JSON_FILE_PATH)

    return jsonify("{'msg': 'success'}"), 200

@app.route('/api/follow_book', methods=['POST'])
def follow_book():
    book_url = request.get_json().get('url')
    is_follow = request.get_json().get('is_follow')
    logger.info(f"更新书籍关注状态: {book_url}, is_follow={is_follow}")

    if book_url is not None and is_follow is not None:
        info = qq_reader_crawler.load_file_data(INFO_FILE)
        follow_books = info.get('follow_books', [])
        follow_book_urls = {book['url'] for book in follow_books}
        if is_follow and book_url not in follow_book_urls:
            follow_books.append({
                'url': book_url,
                'status': 'new'
            })
        elif not is_follow and book_url in follow_book_urls:
            follow_books = [book for book in follow_books if book['url'] != book_url]
        info['follow_books'] = follow_books
        qq_reader_crawler.save_data(info, INFO_FILE)

    return jsonify("{'msg': 'success'}"), 200

@app.route('/api/important_book', methods=['POST'])
def important_book():
    book_url = request.get_json().get('url')
    is_important = request.get_json().get('is_important')
    logger.info(f"更新书籍重要状态: {book_url}, is_important={is_important}")

    if book_url is not None and is_important is not None:
        info = qq_reader_crawler.load_file_data(INFO_FILE)
        follow_books = info.get('follow_books', [])
        
        # 更新书籍的重点关注状态
        for book in follow_books:
            if book['url'] == book_url:
                book['is_important'] = is_important
                break
                
        info['follow_books'] = follow_books
        qq_reader_crawler.save_data(info, INFO_FILE)

    return jsonify({'msg': 'success'}), 200


@app.route('/api/book_status', methods=['POST'])
def update_book_status():
    book_url = request.get_json().get('url')
    status = request.get_json().get('status')
    logger.info(f"更新书籍状态: {book_url}, status={status}")

    if book_url is not None and status is not None:
        info = qq_reader_crawler.load_file_data(INFO_FILE)
        follow_books = info.get('follow_books', [])
        
        # 更新书籍的状态
        for book in follow_books:
            if book['url'] == book_url:
                book['status'] = status
                break
                
        info['follow_books'] = follow_books
        qq_reader_crawler.save_data(info, INFO_FILE)

    return jsonify({'msg': 'success'}), 200


# 运行 Flask 应用
if __name__ == '__main__':
    logger.info("Flask应用启动")
    app.run(host='0.0.0.0', debug=False, port=5001)