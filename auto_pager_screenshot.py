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

VERSION="1.0.0"

# 設置日誌
logging.basicConfig(filename='auto_pager_screenshot.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    encoding='utf-8')

# 自定義日誌函數
def log_message(message, level=logging.INFO):
    logging.log(level, message)
    print(message)

def parse_region_entries(raw_text, setting_name):
    regions = []
    if not raw_text:
        return regions
    entries = [entry.strip() for entry in raw_text.split('|') if entry.strip()]
    for idx, entry in enumerate(entries, start=1):
        label = None
        coords_text = entry
        if ':' in entry:
            label_part, coords_part = entry.split(':', 1)
            label_part = label_part.strip()
            if label_part:
                label = label_part
            coords_text = coords_part
        try:
            left, top, width, height = map(int, map(str.strip, coords_text.split(',')))
        except ValueError as exc:
            raise ValueError(f"{setting_name} 第 {idx} 筆格式錯誤，需為 'x,y,width,height'") from exc
        if width <= 0 or height <= 0:
            raise ValueError(f"{setting_name} 中的 width 與 height 必須為正值")
        regions.append({'label': label, 'bbox': (left, top, width, height)})
    return regions

def format_region_summary(regions):
    entries = []
    for idx, region in enumerate(regions, start=1):
        if region['bbox'] is None:
            continue
        label_text = region['label'] if region['label'] else f"區塊{idx}"
        bbox_text = ','.join(map(str, region['bbox']))
        entries.append(f"{label_text}:{bbox_text}")
    return ' | '.join(entries) if entries else '單一區塊'

def build_region_titles(regions):
    titles = []
    for idx, region in enumerate(regions, start=1):
        if region['bbox'] is None:
            continue
        titles.append(region['label'] if region['label'] else f"區塊{idx}")
    return titles

def adjust_regions_for_origin(regions, offset_x, offset_y, setting_name):
    adjusted = []
    for idx, region in enumerate(regions, start=1):
        bbox = region['bbox']
        if bbox is None:
            adjusted.append(region)
            continue
        left, top, width, height = bbox
        adjusted_left = left - offset_x
        adjusted_top = top - offset_y
        if adjusted_left < 0 or adjusted_top < 0:
            raise ValueError(
                f"{setting_name} 第 {idx} 筆座標 ({left},{top}) 減去起點偏移 ({offset_x},{offset_y}) 後為負值，請確認座標系統")
        adjusted.append({'label': region['label'], 'bbox': (adjusted_left, adjusted_top, width, height)})
    return adjusted

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
    image_format = config.get('Settings', 'image_format', fallback='PNG').upper()
    image_quality = config.getint('Settings', 'image_quality', fallback=95)
    capture_coordinate_space = config.get('Settings', 'capture_coordinate_space', fallback='relative').strip().lower()
    capture_regions_raw = config.get('Settings', 'capture_regions', fallback='').strip()
    capture_first_region_raw = config.get('Settings', 'capture_first_region', fallback='').strip()

    # 解析固定範圍的座標和大小
    if screenshot_mode == 'fixed_area':
        fixed_area_values = tuple(map(int, fixed_area.split(',')))
        if len(fixed_area_values) != 4:
            raise ValueError("固定範圍格式錯誤，應為 'x,y,width,height'")
        left, top, width, height = fixed_area_values
        if width <= 0 or height <= 0:
            raise ValueError("固定範圍的 width 與 height 必須為正值")
        fixed_area = {
            'left': left,
            'top': top,
            'width': width,
            'height': height,
        }

    if image_format == 'JPG':
        image_format = 'JPEG'
    supported_formats = {'PNG', 'JPEG'}
    if image_format not in supported_formats:
        raise ValueError(f"不支援的圖檔格式: {image_format}，支援格式: {', '.join(sorted(supported_formats))}")
    if not (1 <= image_quality <= 100):
        raise ValueError("image_quality 必須介於 1 到 100 之間")

    if capture_coordinate_space not in {'relative', 'absolute'}:
        raise ValueError("capture_coordinate_space 僅支援 'relative' 或 'absolute'")

    capture_regions = parse_region_entries(capture_regions_raw, 'capture_regions')

    if not capture_regions:
        capture_regions.append({'label': None, 'bbox': None})

    regions_with_bbox = [region for region in capture_regions if region['bbox'] is not None]
    all_labeled = bool(regions_with_bbox) and all(region['label'] for region in regions_with_bbox)
    any_labeled = any(region['label'] for region in regions_with_bbox)
    if any_labeled and not all_labeled:
        raise ValueError("capture_regions 設定需全部帶名稱或全部不帶名稱")
    use_labeled_regions = all_labeled

    capture_first_regions = parse_region_entries(capture_first_region_raw, 'capture_first_region')
    if capture_first_regions:
        if use_labeled_regions and not all(region['label'] for region in capture_first_regions):
            raise ValueError("已使用具名區塊，capture_first_region 亦須提供名稱")
        if not use_labeled_regions and any(region['label'] for region in capture_first_regions):
            raise ValueError("目前為連續頁碼命名，capture_first_region 不可帶名稱")

    region_offset_x = 0
    region_offset_y = 0
    if capture_coordinate_space == 'absolute':
        if screenshot_mode == 'fixed_area':
            region_offset_x = fixed_area['left']
            region_offset_y = fixed_area['top']
        else:
            with mss() as sct:
                monitor = sct.monitors[1]
            region_offset_x = monitor.get('left', 0)
            region_offset_y = monitor.get('top', 0)

    capture_regions = adjust_regions_for_origin(capture_regions, region_offset_x, region_offset_y, 'capture_regions')
    capture_first_regions = adjust_regions_for_origin(capture_first_regions, region_offset_x, region_offset_y, 'capture_first_region')


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
    fixed_area = {'left': 0, 'top': 0, 'width': 1920, 'height': 1080}
    image_format = 'PNG'
    image_quality = 95
    capture_coordinate_space = 'relative'
    capture_regions = [{'label': None, 'bbox': None}]
    use_labeled_regions = False
    capture_regions_raw = ''
    capture_first_regions = []
    capture_first_region_raw = ''
    region_offset_x = 0
    region_offset_y = 0

# 確保儲存目錄存在
os.makedirs(save_directory, exist_ok=True)

image_extension = 'jpg' if image_format == 'JPEG' else image_format.lower()

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

def take_screenshot(page_number, hwnd, sequence_start=None, region_set=None):
    with mss() as sct:
        if screenshot_mode == 'full_screen':
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
        else:
            screenshot = sct.grab(fixed_area)

        base_img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    img_width, img_height = base_img.size
    saved_paths = []
    seq_counter = sequence_start

    regions = region_set if region_set is not None else capture_regions

    for idx, region in enumerate(regions):
        bbox = region['bbox']
        region_img = base_img
        if bbox:
            left, top, width, height = bbox
            right = left + width
            bottom = top + height
            if not (0 <= left < right <= img_width and 0 <= top < bottom <= img_height):
                raise ValueError(f"capture_regions 的座標超出截圖範圍: {bbox}")
            region_img = base_img.crop((left, top, right, bottom))
        else:
            region_img = base_img.copy()

        if use_labeled_regions:
            suffix = f"_{region['label']}" if region['label'] else f"_{idx+1}"
            filename = f"{file_prefix}{page_number:03d}{suffix}.{image_extension}"
        else:
            if seq_counter is None:
                raise ValueError("序號尚未初始化，無法建立檔名")
            filename = f"{file_prefix}{seq_counter:03d}.{image_extension}"
            seq_counter += 1

        full_path = os.path.join(save_directory, filename)
        save_kwargs = {}
        if image_format == 'JPEG':
            save_kwargs['quality'] = image_quality
            save_kwargs['optimize'] = True
            save_kwargs['subsampling'] = 2
        region_img.save(full_path, format=image_format, **save_kwargs)
        log_message(f"截圖已儲存: {full_path}")
        saved_paths.append(full_path)

    win32gui.SetForegroundWindow(hwnd)
    send_next_page_command(hwnd)
    time.sleep(delay_between_screenshots)
    return saved_paths

def merge_images_to_pdf(image_files, pdf_path):
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_files))
    log_message(f"PDF 文件已生成: {pdf_path}")

def main():
    log_message(f"自動翻頁截圖工具啟動 v{VERSION}")
    log_message(f"將進行 {screenshot_count} 次截圖，儲存至 {save_directory}")
    log_message(f"翻頁操作: {next_page_action}")
    log_message(f"截圖模式: {'全螢幕' if screenshot_mode == 'full_screen' else '固定範圍'}")
    if screenshot_mode == 'fixed_area':
        log_message(f"固定範圍: {fixed_area}")
    log_message(f"多區塊設定: {format_region_summary(capture_regions)}")
    if capture_first_regions:
        log_message(f"首張覆蓋: {format_region_summary(capture_first_regions)}")
    coord_space_text = '相對 (以截圖左上角為原點)' if capture_coordinate_space == 'relative' else f"絕對 (已套用偏移 {region_offset_x},{region_offset_y})"
    log_message(f"座標模式: {coord_space_text}")
    naming_text = '頁碼+區塊名稱' if use_labeled_regions else '連續頁碼'
    log_message(f"檔名模式: {naming_text}")
    quality_suffix = f", 品質: {image_quality}" if image_format == 'JPEG' else ''
    log_message(f"圖檔格式: {image_format}{quality_suffix}")
    input("請確保目標窗口已打開並位於當前窗口之後，然後按下 Enter 鍵開始...")

    # 切換到目標窗口並獲取句柄
    target_hwnd = switch_to_target_window()
    if not target_hwnd:
        log_message("無法切換到目標窗口", logging.ERROR)
        return

    window_title = win32gui.GetWindowText(target_hwnd)
    log_message(f"目標窗口標題: {window_title}")
    
    image_files = []
    next_image_number = 1
    default_region_titles = build_region_titles(capture_regions)
    first_region_titles = build_region_titles(capture_first_regions) if capture_first_regions else default_region_titles
    for i in range(1, screenshot_count + 1):
        use_first_override = bool(capture_first_regions) and i == 1
        titles_for_log = first_region_titles if use_first_override else default_region_titles
        if titles_for_log:
            log_message(f"正在進行第 {i} 次截圖 ({'/'.join(titles_for_log)})...")
        else:
            log_message(f"正在進行第 {i} 次截圖...")
        seq_start = None if use_labeled_regions else next_image_number
        region_set = capture_first_regions if use_first_override else capture_regions
        saved_paths = take_screenshot(i, target_hwnd, seq_start, region_set)
        image_files.extend(saved_paths)
        if not use_labeled_regions:
            next_image_number += len(saved_paths)

    log_message("截圖完成！")

    # 如果設置了 PDF 輸出，則合併圖片為 PDF
    if pdf_output:
        pdf_path = os.path.join(save_directory, pdf_output)
        merge_images_to_pdf(image_files, pdf_path)

if __name__ == "__main__":
    main()