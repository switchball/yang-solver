# log_config.py

import logging
import os

def setup_logging(log_file='app.log'):
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s',
    #     datefmt='%Y-%m-%d %H:%M:%S',
    #     filename=log_file,
    #     filemode='a'
    # )

    # 创建日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 设置日志级别

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # 设置文件处理器的日志级别

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 设置控制台处理器的日志级别

    # 定义日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d - %(levelname)s - %(filename)s - %(lineno)d - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 将格式应用到处理器
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)