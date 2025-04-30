import requests
from bs4 import BeautifulSoup
import logging
from utils import (
    parse_word_count, 
    get_shanghai_time, 
    load_file_data, 
    save_data, 
    send_notification
)

# 文件路径
INFO_FILE = 'data/info.json'
CURRENT_FILE = 'data/current_books.json'
PREVIOUS_FILE = 'data/previous_books.json'
NEW_BOOK_HISTORY_FILE = 'data/new_book_history.json'

# 获取日志记录器
logger = logging.getLogger(__name__)


# 爬取单页书籍信息
def crawl_page(follow_books_urls, page):
    """爬取指定页的书籍信息"""
    url = f"https://book.qq.com/book-rank/female-new/cycle-1-{page}"
    logger.info(f"开始爬取第 {page} 页: {url}")
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
        logger.error(f"爬取第 {page} 页失败: {e}")
        return []


def crawl_detail_page(url):
    logger.info(f"开始爬取书籍详情页: {url}")
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


# 检查新书和重点书籍
def check_updates(current_books, previous_books, info):
    previous_urls = {book['url'] for book in previous_books}
    previous_dict = {book['url']: book for book in previous_books}
    follow_dict = {book['url']: book for book in info['follow_books']}
    
    new_books = []
    for book in current_books:
        # 新上榜书籍
        if book['url'] not in previous_urls:
            book_record = book.copy()
            new_books.append(book_record)

        # set update date
        prev_book = previous_dict.get(book['url'], {})
        prev_word_count = prev_book.get('word_count', 0)
        current_word_count = book['word_count']
        book['last_update_date'] = prev_book.get('last_update_date')
        if current_word_count > prev_word_count or book.get('last_update_date') is None:
            book['last_update_date'] = get_shanghai_time()

        # 检查关注书籍
        follow_book = follow_dict.get(book['url'])
        if follow_book is not None:
            # 重点关注的7万字提醒一次
            if current_word_count >= 70000 and follow_book.get('is_important', False) and follow_book.get('alert_for_7') is None:
                message = f"重点关注书籍达到 7 万字: 《{book['title']}》 - {book['author']} - {current_word_count} 字"
                send_notification(message)
                follow_book['alert_for_7'] = True
            # 未开始的5万字提醒一次
            if current_word_count >= 50000 and follow_book['status'] == 'new' and follow_book.get('alert_for_5') is None:
                message = f"关注书籍达到 5 万字: 《{book['title']}》 - {book['author']} - {current_word_count} 字"
                send_notification(message)
                follow_book['alert_for_5'] = True
            # 正在做的9万字提醒一次
            if current_word_count >= 90000 and follow_book['status'] == 'wip' and follow_book.get('alert_for_9') is None:
                message = f"正在做的书籍达到 9 万字: 《{book['title']}》 - {book['author']} - {current_word_count} 字"
                send_notification(message)
                follow_book['alert_for_9'] = True
            # 已完成的9万7字提醒一次
            if current_word_count >= 97000 and follow_book['status'] == 'done' and follow_book.get('alert_for_97') is None:
                message = f"已完成书籍达到 97000 字: 《{book['title']}》 - {book['author']} - {current_word_count} 字"
                send_notification(message)
                follow_book['alert_for_97'] = True

    if new_books.__len__() > 0:
        # 加载历史新书记录
        new_book_history = load_file_data(NEW_BOOK_HISTORY_FILE)
        if not isinstance(new_book_history, list):
            new_book_history = []
        
        # 创建URL到记录的映射，用于快速查找
        existing_books = {book['url']: book for book in new_book_history}
        
        for book in new_books:
            # 如果书已存在，只更新日期
            if book['url'] in existing_books:
                existing_books[book['url']]['up_date'] = get_shanghai_time().split()[0]
            else:
                # 新书则添加完整记录
                book['up_date'] = get_shanghai_time().split()[0]
                new_book_history.append(book)
                
        # 保存更新后的历史记录
        save_data(new_book_history, NEW_BOOK_HISTORY_FILE)
        # 发送新书通知
        message = f"新书上榜: {', '.join('《' + book['title'] + '》' for book in new_books)}"
        send_notification(message)


# 主爬取逻辑
def main_crawl():
    logger.info("开始主爬取任务")
    info = load_file_data(INFO_FILE)
    
    follow_books = []
    for fb in info.get('follow_books'):
        logger.info(f"爬取关注书籍: {fb['url']}")
        book = crawl_detail_page(fb['url'])
        book['is_follow'] = True
        follow_books.append(book)
    logger.info(f"已爬取关注书籍: {len(follow_books)} 本")

    """爬取 1-9 页并处理数据"""
    all_books = []
    follow_book_urls = [book['url'] for book in follow_books]
    for page in range(1, 10):
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

    info['last_fetch_data_date'] = get_shanghai_time()
    save_data(info, INFO_FILE)

    logger.info(f"本次爬取完成，共获取 {len(sorted_books)} 本书籍")
    return sorted_books


def update_follows():
    logger.info("开始更新关注状态")
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
