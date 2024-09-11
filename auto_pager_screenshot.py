# -*- coding: utf-8 -*-
import time
import os
import logging
from mss import mss
from PIL import Image
import win32gui
import win32com.client
import configparser
import pyautogui
import img2pdf

# 設置日誌
logging.basicConfig(filename='auto_pager_screenshot.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    encoding='utf-8')

# 自定義日誌函數
def log_message(message, level=logging.INFO):
    logging.log(level, message)
    print(message)

# 讀取配置文件
config = configparser.ConfigParser()
config_file = 'auto_pager_screenshot_config.ini'

try:
    if not config.read(config_file, encoding='utf-8'):
        raise FileNotFoundError(f"找不到配置文件: {config_file}")

    # 從配置文件中讀取設置
    save_directory = config.get('Settings', 'save_directory', fallback=r'R:\output')
    file_prefix = config.get('Settings', 'file_prefix', fallback='page_')
    screenshot_count = config.getint('Settings', 'screenshot_count', fallback=5)
    delay_between_screenshots = config.getfloat('Settings', 'delay_between_screenshots', fallback=1.5)
    print_to_console = config.getboolean('Settings', 'print_to_console', fallback=True)
    next_page_action = config.get('Settings', 'next_page_action', fallback='RIGHT')
    pdf_output = config.get('Settings', 'pdf_output', fallback='')
    screenshot_mode = config.get('Settings', 'screenshot_mode', fallback='full_screen')
    fixed_area = config.get('Settings', 'fixed_area', fallback='0,0,1920,1080')

    # 解析固定範圍的座標和大小
    if screenshot_mode == 'fixed_area':
        fixed_area = tuple(map(int, fixed_area.split(',')))
        if len(fixed_area) != 4:
            raise ValueError("固定範圍格式錯誤，應為 'x,y,width,height'")

except FileNotFoundError as e:
    log_message(f"錯誤: {str(e)}", logging.ERROR)
    log_message("將使用默認設置繼續執行。", logging.WARNING)
    
    # 使用默認設置
    save_directory = r'R:\output'
    file_prefix = 'page_'
    screenshot_count = 5
    delay_between_screenshots = 1.5
    print_to_console = True
    next_page_action = 'RIGHT'
    pdf_output = ''
    screenshot_mode = 'full_screen'
    fixed_area = (0, 0, 1920, 1080)

# 確保儲存目錄存在
os.makedirs(save_directory, exist_ok=True)

def get_active_window():
    return win32gui.GetForegroundWindow()

def switch_to_target_window():
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%{TAB}')  # 模擬 Alt+Tab
    time.sleep(0.5)  # 給窗口切換一些時間
    return get_active_window()

def send_next_page_command(hwnd):
    if hwnd:
        win32gui.SetForegroundWindow(hwnd)
        if next_page_action == 'MOUSE_LEFT':
            pyautogui.click()
        else:
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys(f"{{{next_page_action}}}")
    else:
        log_message("找不到目標窗口，無法發送下一頁命令", logging.ERROR)

def take_screenshot(number, hwnd):
    with mss() as sct:
        if screenshot_mode == 'full_screen':
            monitor = sct.monitors[1]  # 主顯示器
            screenshot = sct.grab(monitor)
        else:  # fixed_area
            screenshot = sct.grab(fixed_area)
        
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        filename = f"{file_prefix}{number:03d}.png"
        full_path = os.path.join(save_directory, filename)
        img.save(full_path)
        log_message(f"截圖已儲存: {full_path}")

    win32gui.SetForegroundWindow(hwnd)  # 確保目標窗口在前台
    send_next_page_command(hwnd)
    time.sleep(delay_between_screenshots)

def merge_images_to_pdf(image_files, pdf_path):
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_files))
    log_message(f"PDF 文件已生成: {pdf_path}")

def main():
    log_message("自動翻頁截圖工具啟動")
    log_message(f"將進行 {screenshot_count} 次截圖，儲存至 {save_directory}")
    log_message(f"翻頁操作: {next_page_action}")
    log_message(f"截圖模式: {'全螢幕' if screenshot_mode == 'full_screen' else '固定範圍'}")
    if screenshot_mode == 'fixed_area':
        log_message(f"固定範圍: {fixed_area}")
    input("請確保目標窗口已打開並位於當前窗口之後，然後按下 Enter 鍵開始...")

    # 切換到目標窗口並獲取句柄
    target_hwnd = switch_to_target_window()
    if not target_hwnd:
        log_message("無法切換到目標窗口", logging.ERROR)
        return

    window_title = win32gui.GetWindowText(target_hwnd)
    log_message(f"目標窗口標題: {window_title}")
    
    image_files = []
    for i in range(1, screenshot_count + 1):
        log_message(f"正在進行第 {i} 次截圖...")
        take_screenshot(i, target_hwnd)
        image_files.append(os.path.join(save_directory, f"{file_prefix}{i:03d}.png"))

    log_message("截圖完成！")

    # 如果設置了 PDF 輸出，則合併圖片為 PDF
    if pdf_output:
        pdf_path = os.path.join(save_directory, pdf_output)
        merge_images_to_pdf(image_files, pdf_path)

if __name__ == "__main__":
    main()