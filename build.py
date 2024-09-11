import os
import subprocess
import sys
import venv
import shutil

# 获取当前系统的用户名
current_username = os.environ.get('USERNAME') or os.environ.get('USER')

# 設定變數
project_dir = os.path.dirname(os.path.abspath(__file__))  # 專案目錄
venv_dir = os.path.join(project_dir, 'venv')  # 虛擬環境目錄
upx_dir = r'e:\toolp\upx'  # UPX 路徑
script_name = 'auto_pager_screenshot.py'  # 主程式檔名
icon_file = os.path.join(project_dir, 'icon.png')  # 圖標檔案
output_dir = os.path.join(project_dir, 'dist')  # 輸出目錄
exe_name = 'auto_pager_screenshot.exe'  # 可執行檔名稱

# 建立虛擬環境
def create_virtual_env():
    if not os.path.exists(venv_dir):
        print("正在建立虛擬環境...")
        venv.create(venv_dir, with_pip=True)

# 安裝依賴
def install_dependencies():
    print("正在安裝依賴套件...")
    subprocess.run([os.path.join(venv_dir, 'Scripts', 'pip'), 'install', 'pyinstaller', 'pillow', 'mss', 'pyautogui', 'img2pdf', 'pywin32'], check=True)

# 執行 PyInstaller 打包
def build_executable():
    print("正在打包可執行檔...")
    subprocess.run([
        os.path.join(venv_dir, 'Scripts', 'pyinstaller'),
        '--onefile', 
        f'--icon={icon_file}',  # 設定圖標
        '--hidden-import=ctypes',  # 強制打包 ctypes
        '--add-binary', rf'C:\Users\{current_username}\Anaconda3\envs\h5\DLLs\_ctypes.pyd;.',
		'--add-binary', rf'C:\Users\{current_username}\Anaconda3\envs\h5\python310.dll;.',
		'--add-binary', rf'C:\Users\{current_username}\Anaconda3\envs\h5\Library\bin\libcrypto-3-x64.dll;.',
        script_name
    ], check=True)


# 使用 UPX 壓縮可執行檔
def compress_executable():
    print("正在使用 UPX 壓縮可執行檔...")
    exe_path = os.path.join(output_dir, exe_name)
    upx_exe = os.path.join(upx_dir, 'upx.exe')
    subprocess.run([upx_exe, '--best', '--ultra-brute', exe_path], check=True)

# 主函數
def main():
    # 建立虛擬環境
    create_virtual_env()

    # 安裝依賴
    install_dependencies()

    # 執行打包
    build_executable()

    # 壓縮可執行檔
    #compress_executable()

    print(f"已生成並壓縮可執行檔：{os.path.join(output_dir, exe_name)}")

if __name__ == '__main__':
    main()
