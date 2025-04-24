import requests
from bs4 import BeautifulSoup
import json
import itchat
from pathlib import Path
import datetime

# 文件路径
INFO_FILE = 'info.json'
CURRENT_FILE = 'current_books.json'
PREVIOUS_FILE = 'previous_books.json'


# 解析字数字符串
def parse_word_count(word_count_str):
    """将字数字符串转换为整数，例如 '12.3万字' -> 123000"""
    word_count_str = word_count_str.replace('·', '')
    if '万字' in word_count_str:
        return int(float(word_count_str.replace('万字', '')) * 10000)
    else:
        return int(word_count_str.replace('字', ''))


# 爬取单页书籍信息
def crawl_page(page):
    """爬取指定页的书籍信息"""
    url = f"https://book.qq.com/book-rank/female-new/cycle-1-{page}"  # 假设的 URL，需替换为实际地址
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        book_list = soup.find('div', class_='tabs-content')  # 需根据实际 HTML 调整
        books = []
        for book_item in book_list.find_all('div', class_='book-large rank-book'):  # 需根据实际调整
            title = book_item.find('h4', class_='title ypc-link').text.strip()  # 需根据实际调整
            book_item_objects = book_item.find('object').find_all('a')
            author = book_item_objects[0].text.strip()
            book_type = book_item_objects[1].text.strip().replace('·', '')
            word_count_str = book_item.find('p', class_='other').find_all('span')[1].text.strip()  # 需根据实际调整
            word_count = parse_word_count(word_count_str)
            book_url = book_item.find('a', class_='wrap')['href']
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
    """通过微信发送通知，并保存到日志文件"""
    try:
        # itchat.send(message, toUserName='filehelper')
        # TODO
        print(message)
        # 保存到日志文件
        with open('notification_history.log', 'a', encoding='utf-8') as log_file:
            log_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"{log_time} {message}\n")
    except Exception as e:
        print(f"发送通知失败: {e}")


# 检查新书和重点书籍
def check_updates(current_books, previous_books):
    """检查新上榜书籍和重点书籍字数变化"""
    current_urls = {book['url'] for book in current_books}
    previous_urls = {book['url'] for book in previous_books}

    # 新上榜书籍
    new_books = [book for book in current_books if book['url'] not in previous_urls]
    for book in new_books:
        message = f"新书上榜: {book['title']} - {book['author']} - {book['word_count']} 字"
        send_notification(message)

    previous_dict = {book['url']: book for book in previous_books}
    for book in current_books:
        prev_book = previous_dict.get(book['url'], {})
        prev_word_count = prev_book.get('word_count', 0)
        current_word_count = book['word_count']
        # set update date
        book['last_update_date'] = prev_book.get('last_update_date')
        if current_word_count > prev_word_count or book.get('last_update_date') is None:
            book['last_update_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 检查重点书籍
        if book['is_follow']:
            if prev_word_count < 100000 <= current_word_count:
                message = f"重点书籍达到 10 万字: {book['title']} - {book['author']} - {current_word_count} 字"
                send_notification(message)


# 主爬取逻辑
def main_crawl():
    info = load_file_data(INFO_FILE)

    """爬取 1-9 页并处理数据"""
    all_books = []
    for page in range(1, 9):
        page_books = crawl_page(page)
        all_books.extend(page_books)

    # 默认按字数排序
    sorted_books = sorted(all_books, key=lambda x: x['word_count'], reverse=True)
    previous_books = load_file_data(CURRENT_FILE)

    # 加载关注列表
    mix_follow(info, sorted_books)

    # 检查更新并发送通知
    check_updates(sorted_books, previous_books)

    # 保存当前数据
    save_data(previous_books, PREVIOUS_FILE)
    save_data(sorted_books, CURRENT_FILE)

    info['last_fetch_data_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(info, INFO_FILE)

    return sorted_books


def update_follows():
    current_books = load_file_data(CURRENT_FILE)
    info = load_file_data(INFO_FILE)
    mix_follow(info, current_books)
    save_data(current_books, CURRENT_FILE)


# 标记关注
def mix_follow(info, books):
    for book in books:
        is_follow = False
        for follow_book in info['follow_books']:
            if book['url'] == follow_book:
                is_follow = True
                break
        if not is_follow:
            for follow_author in info['follow_authors']:
                if book['author'] == follow_author:
                    is_follow = True
                    break
        book['is_follow'] = is_follow
    return books


def main():
    # itchat.auto_login(hotReload=True)  # 登录微信，支持热重载

    books = main_crawl()

    # itchat.logout()


if __name__ == '__main__':
    itchat.auto_login(hotReload=True)  # 登录微信，支持热重载
    itchat.send("hello", toUserName='filehelper')
    itchat.logout()
