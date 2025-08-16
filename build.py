import os
import sys
import subprocess
import shutil

def get_version():
    """バージョン情報を取得"""
    try:
        # twitchTransFreeNeo/__init__.pyからバージョンを読み取り
        init_file = os.path.join("twitchTransFreeNeo", "__init__.py")
        with open(init_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    # __version__ = "1.0.0" の形式から抽出
                    return line.split('"')[1]
    except Exception as e:
        print(f"Error reading version from __init__.py: {e}")
    
    # バージョン情報が取得できない場合は、環境変数から取得を試みる
    if "VERSION" in os.environ:
        return os.environ["VERSION"]
    
    return "unknown"

def build_for_os(os_name, arch, add_data_option):
    """OS別ビルド処理"""
    version = get_version()
    print(f"Building twitchTransFreeNeo v{version} for {os_name} ({arch})...")
    
    # distフォルダを削除
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # PyInstallerコマンド構築
    command = [
        "pyinstaller",
        "--onefile",
        "--icon=icon.ico",  # アイコン設定
        "--runtime-tmpdir=.",  # runtime-tmpdirを追加
        "--hidden-import=twitchTransFreeNeo",  # メインパッケージを強制包含
        "--hidden-import=twitchTransFreeNeo.gui",  # guiモジュールを強制包含
        "--hidden-import=twitchTransFreeNeo.core",  # coreモジュールを強制包含
        "--hidden-import=twitchTransFreeNeo.utils",  # utilsモジュールを強制包含
        "--hidden-import=twitchTransFreeNeo.gui.main_window",
        "--hidden-import=twitchTransFreeNeo.gui.settings_window",
        "--hidden-import=twitchTransFreeNeo.gui.chat_display",
        "--hidden-import=twitchTransFreeNeo.core.chat_monitor",
        "--hidden-import=twitchTransFreeNeo.core.translator",
        "--hidden-import=twitchTransFreeNeo.core.database",
        "--hidden-import=twitchTransFreeNeo.core.tts",
        "--hidden-import=twitchTransFreeNeo.utils.config_manager",
        add_data_option,
        "--name=twitchTransFreeNeo",  # 出力ファイル名を明示的に指定
        "run.py"  # エントリーポイント
    ]
    
    # Windowsの場合のみ --windowed オプションを追加
    if os_name == "windows":
        command.insert(-2, "--windowed")
    
    print(f"Executing: {' '.join(command)}")
    subprocess.run(command, check=True)

    # ファイル名の変更
    if os_name == "windows":
        old_name = "dist/twitchTransFreeNeo.exe"
        new_name = f"dist/twitchTransFreeNeo_{version}_win.exe"
        if os.path.exists(old_name):
            os.rename(old_name, new_name)
    elif os_name == "linux":
        old_name = "dist/twitchTransFreeNeo"
        new_name = f"dist/twitchTransFreeNeo_{version}_linux"
        if os.path.exists(old_name):
            os.rename(old_name, new_name)
    elif os_name == "macos":
        old_name = "dist/twitchTransFreeNeo"
        if arch == "arm64":
            new_name = f"dist/twitchTransFreeNeo_{version}_macos_M1.command"
        elif arch == "x86_64":
            new_name = f"dist/twitchTransFreeNeo_{version}_macos_Intel.command"
        else:
            new_name = f"dist/twitchTransFreeNeo_{version}_macos.command"
        
        if os.path.exists(old_name):
            os.rename(old_name, new_name)

    print(f"Build for {os_name} ({arch}) completed.")

def download_cacert():
    """cacert.pemをダウンロード"""
    if not os.path.exists("cacert.pem"):
        print("cacert.pem not found. Downloading...")
        try:
            import urllib.request
            urllib.request.urlretrieve("https://curl.se/ca/cacert.pem", "cacert.pem")
            print("cacert.pem downloaded successfully.")
        except Exception as e:
            print(f"Failed to download cacert.pem: {e}")
            return False
    return True


def main(target_os):
    """メイン処理"""
    print(f"Starting build process for {target_os}")
    
    # 必要ファイルの準備
    if not download_cacert():
        return
    
    # distフォルダの準備
    if not os.path.exists("dist"):
        os.makedirs("dist")

    # 各OS向けにビルド
    if target_os == "windows":
        build_for_os("windows", "", "--add-data=cacert.pem;.")
    elif target_os == "linux":
        build_for_os("linux", "", "--add-data=cacert.pem:.")
    elif target_os == "macos_M1":
        build_for_os("macos", "arm64", "--add-data=cacert.pem:.")
    elif target_os == "macos_Intel":
        build_for_os("macos", "x86_64", "--add-data=cacert.pem:.")
    else:
        print(f"Unknown target OS: {target_os}")
        return

    print("Build process completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build.py <target_os>")
        print("target_os: windows, linux, macos_M1, macos_Intel")
        sys.exit(1)
    
    main(sys.argv[1])