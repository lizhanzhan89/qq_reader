import datetime
import json
from pathlib import Path
import logging
from urllib.parse import quote

# 获取日志记录器
logger = logging.getLogger(__name__)

def parse_word_count(word_count_str):
    """将字数字符串转换为整数，例如 '12.3万字' -> 123000"""
    word_count_str = word_count_str.replace('·', '')
    if '万字' in word_count_str:
        return int(float(word_count_str.replace('万字', '')) * 10000)
    else:
        return int(word_count_str.replace('字', ''))

def get_shanghai_time():
    """获取北京时间"""
    utc_time = datetime.datetime.utcnow()
    shanghai_time = utc_time + datetime.timedelta(hours=8)
    return shanghai_time.strftime("%Y-%m-%d %H:%M:%S")

def load_file_data(filename):
    """加载文件数据"""
    if Path(filename).exists():
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(json_data, filename):
    """保存当前书籍数据"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

def send_wechat_notification(message):
    """发送微信通知"""
    try:
        base_url = "https://wxpusher.zjiecode.com/api/send/message/SPT_xiAfRwl3cByBm0BHxFmVoa9Q2M52"
        encoded_message = quote(message)
        response = requests.get(f"{base_url}/{encoded_message}")
        logger.info(f"发送通知: {message}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"发送微信通知失败: {e}")
        return False

def send_notification(message):
    """发送通知并记录日志"""
    try:
        # 通过微信发送通知
        send_wechat_notification(message)
        # 保存到日志文件
        with open('data/notification_history.log', 'a', encoding='utf-8') as log_file:
            log_time = get_shanghai_time()
            log_file.write(f"{log_time} {message}\n")
    except Exception as e:
        print(f"发送通知失败: {e}")