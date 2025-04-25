import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import datetime

# 文件路径
INFO_FILE = 'data/info.json'
CURRENT_FILE = 'data/current_books.json'
PREVIOUS_FILE = 'data/previous_books.json'


# 解析字数字符串
def parse_word_count(word_count_str):
    """将字数字符串转换为整数，例如 '12.3万字' -> 123000"""
    word_count_str = word_count_str.replace('·', '')
    if '万字' in word_count_str:
        return int(float(word_count_str.replace('万字', '')) * 10000)
    else:
        return int(word_count_str.replace('字', ''))


# 爬取单页书籍信息
def crawl_page(follow_books_urls, page):
    """爬取指定页的书籍信息"""
    url = f"https://book.qq.com/book-rank/female-new/cycle-1-{page}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html5lib')
        book_list = soup.find('div', class_='tabs-content')
        books = []
        for book_item in book_list.find_all('div', class_='book-large rank-book'):
            book_url = book_item.find('a', class_='wrap')['href']
            if book_url in follow_books_urls:
                continue
            title = book_item.find('h4', class_='title ypc-link').text.strip()
            book_item_objects = book_item.find('object').find_all('a')
            author = book_item_objects[0].text.strip()
            book_type = book_item_objects[1].text.strip().replace('·', '')
            word_count_str = book_item.find('p', class_='other').find_all('span')[1].text.strip()
            word_count = parse_word_count(word_count_str)
            books.append({
                'title': title,
                'author': author,
                'type': book_type,
                'word_count': word_count,
                'url': book_url
            })
        return books
    except Exception as e:
        print(f"爬取第 {page} 页失败: {e}")
        return []


def crawl_detail_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    new_url = f"https://ubook.reader.qq.com/book-detail/{url.split('/')[-1]}"
    response = requests.get(new_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html5lib')
    book_detail = soup.find('section', class_='detail-x__header-detail')

    title = book_detail.find('h2', class_='detail-x__header-detail__title').text.strip()
    author = book_detail.find_all(class_='detail-x__header-detail__author')[0].text.strip()
    categories = book_detail.find_all('a', class_='detail-x__header-detail__category')
    book_type = '/'.join([item.text.strip() for item in categories])
    word_count_str = book_detail.find('p', class_='detail-x__header-detail__line').find_all('span')[1].text.strip()
    word_count = parse_word_count(word_count_str)
    last_update_date = book_detail.find('span', class_='detail-x__header-detail__time').text.strip().split('：')[-1]
    book = {
        'title': title,
        'author': author,
        'type': book_type,
        'word_count': word_count,
        'url': url,
        'last_update_date': last_update_date
    }
    return book


# 加载文件数据
def load_file_data(filename):
    if Path(filename).exists():
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# 保存数据
def save_data(json_data, filename):
    """保存当前书籍数据"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)


# 发送微信通知
def send_notification(message):
    try:
        # TODO 通过微信发送通知
        print(message)
        # 保存到日志文件
        with open('data/notification_history.log', 'a', encoding='utf-8') as log_file:
            log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"{log_time} {message}\n")
    except Exception as e:
        print(f"发送通知失败: {e}")


# 检查新书和重点书籍
def check_updates(current_books, previous_books, info):
    previous_urls = {book['url'] for book in previous_books}
    previous_dict = {book['url']: book for book in previous_books}
    follow_dict = {book['url']: book for book in info['follow_books']}
    for book in current_books:
        # 新上榜书籍
        if book['url'] not in previous_urls:
            message = f"新书上榜: {book['title']} - {book['author']} - {book['word_count']} 字"
            send_notification(message)
            book['is_new'] = True

        # set update date
        prev_book = previous_dict.get(book['url'], {})
        prev_word_count = prev_book.get('word_count', 0)
        current_word_count = book['word_count']
        book['last_update_date'] = prev_book.get('last_update_date')
        if current_word_count > prev_word_count or book.get('last_update_date') is None:
            book['last_update_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 检查关注书籍
        follow_book = follow_dict.get(book['url'])
        if follow_book is not None:
            # 重点关注7万字提醒一次
            if current_word_count >= 70000 and follow_book.get('is_important', False) and follow_book.get('alert_for_7') is None:
                message = f"重点关注书籍达到 7 万字: {book['title']} - {book['author']} - {current_word_count} 字"
                send_notification(message)
            # 已完成的10万字提醒
            if current_word_count >= 100000 and follow_book['status'] == 'done' and follow_book.get('alert_for_10') is None:
                message = f"已完成书籍达到 10 万字: {book['title']} - {book['author']} - {current_word_count} 字"
                send_notification(message)


# 主爬取逻辑
def main_crawl():
    info = load_file_data(INFO_FILE)

    follow_books = []
    for fb in info.get('follow_books'):
        book = crawl_detail_page(fb['url'])
        book['is_follow'] = True
        follow_books.append(book)

    """爬取 1-9 页并处理数据"""
    all_books = []
    follow_book_urls = [book['url'] for book in follow_books]
    for page in range(1, 9):
        page_books = crawl_page(follow_book_urls, page)
        all_books.extend(page_books)

    # 加载关注列表
    mix_follow_by_author(info, all_books)

    # 默认按字数排序
    all_books.extend(follow_books)
    sorted_books = sorted(all_books, key=lambda x: x['word_count'], reverse=True)

    # 检查更新并发送通知
    previous_books = load_file_data(CURRENT_FILE)
    check_updates(all_books, previous_books, info)

    # 保存当前数据
    save_data(previous_books, PREVIOUS_FILE)
    save_data(sorted_books, CURRENT_FILE)

    info['last_fetch_data_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(info, INFO_FILE)

    return sorted_books


def update_follows():
    current_books = load_file_data(CURRENT_FILE)
    info = load_file_data(INFO_FILE)
    mix_follow_by_author(info, current_books)
    save_data(current_books, CURRENT_FILE)


# 标记关注
def mix_follow_by_author(info, books):
    for book in books:
        is_follow = False
        for follow_author in info['follow_authors']:
            if book['author'] == follow_author:
                is_follow = True
                break
        book['is_follow'] = is_follow
    return books


def main():
    books = main_crawl()
