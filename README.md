# 自動翻頁截圖工具

這是一個自動化工具，用於捕獲多頁文檔或網頁的截圖。它可以自動翻頁並拍攝截圖，最後可選擇將所有截圖合併為一個 PDF 文件。

## 功能

- 自動切換到目標窗口
- 支持全螢幕或固定範圍截圖
- 定時截取圖像
- 自動模擬翻頁操作
- 可選的 PDF 合併功能
- 可自定義的配置選項

## 安裝

1. 確保您已安裝 Python 3.6 或更高版本。

2. 克隆此儲存庫：
   ```
   git clone https://github.com/yourusername/auto-pager-screenshot.git
   cd auto-pager-screenshot
   ```

3. 安裝所需的依賴：
   ```
   pip install mss Pillow pywin32 pyautogui img2pdf
   ```

## 使用方法

1. 編輯 `auto_pager_screenshot_config.ini` 文件以設置您的偏好：
   ```ini
   [Settings]
   save_directory = R:\output
   file_prefix = page_
   screenshot_count = 5
   delay_between_screenshots = 1.5
   print_to_console = True
   next_page_action = RIGHT
   pdf_output = output.pdf
   screenshot_mode = full_screen
   fixed_area = 0,0,1920,1080
   ```

2. 運行腳本：
   ```
   python auto_pager_screenshot.py
   ```

3. 按照提示操作，確保目標窗口在當前窗口之後，然後按 Enter 開始截圖過程。

## 配置選項

- `save_directory`: 截圖儲存目錄
- `file_prefix`: 截圖檔案名稱前綴
- `screenshot_count`: 要執行的截圖次數
- `delay_between_screenshots`: 每次截圖之間的延遲時間（秒）
- `print_to_console`: 是否將訊息印到控制台
- `next_page_action`: 翻頁操作，可選值：RIGHT, LEFT, SPACE, MOUSE_LEFT 或其他有效的鍵盤按鍵
- `pdf_output`: PDF 輸出檔案名稱，如果不需要生成 PDF 則留空
- `screenshot_mode`: 截圖模式，可選值：full_screen（全螢幕）或 fixed_area（固定範圍）
- `fixed_area`: 固定範圍截圖的座標和大小，格式：x,y,width,height（僅在 screenshot_mode 為 fixed_area 時使用）

## 注意事項

- 確保目標窗口在運行腳本時是可見的，並且位於當前窗口之後。
- 如果使用 PDF 合併功能，請確保您有足夠的磁碟空間來儲存所有截圖和最終的 PDF 文件。
- 使用固定範圍截圖時，請確保提供的座標和大小適合您的螢幕分辨率。

## 故障排除

- 如果遇到找不到配置文件的錯誤，請確保 `auto_pager_screenshot_config.ini` 文件存在於腳本同一目錄下。
- 如果翻頁操作不正確，請在配置文件中調整 `next_page_action` 設置。
- 如果截圖質量不佳，可能需要調整 `delay_between_screenshots` 的值。
- 如果固定範圍截圖不正確，請檢查 `fixed_area` 的設置是否符合您的螢幕佈局。

## 貢獻

歡迎提交 Pull Requests 來改進這個專案。對於重大更改，請先開 issue 討論您想要改變的內容。

## 授權

本專案採用 Apache License 2.0 授權。完整的授權文本可以在 [LICENSE](LICENSE) 文件中找到。

Copyright 2024 [Your Name or Organization]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
