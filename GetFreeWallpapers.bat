@echo off
chcp 65001 >nul
echo.
echo ================================
echo   GetFreeWallpapers 起動中...
echo ================================
echo.

REM スクリプトのあるディレクトリに移動
cd /d "%~dp0"

REM Pythonのバージョン確認
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Pythonがインストールされていません
    echo 💡 https://python.org からPythonをダウンロードしてインストールしてください
    echo.
    pause
    exit /b 1
)

REM 必要なライブラリのインストール確認
echo 📦 必要なライブラリをチェック中...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  requestsライブラリがインストールされていません
    echo 📥 自動インストールを実行します...
    pip install requests
    if errorlevel 1 (
        echo ❌ requestsのインストールに失敗しました
        echo 💡 手動で 'pip install requests' を実行してください
        pause
        exit /b 1
    )
    echo ✅ requestsをインストールしました
)

REM GetFreeWallpapersスクリプトの存在確認
if not exist "src/main.py" (
    echo ❌ main.py が見つかりません
    echo 💡 同じフォルダにPythonスクリプトを配置してください
    echo.
    pause
    exit /b 1
)

REM APIキーの設定確認
findstr /C:"YOUR_API_KEY_HERE" src/main.py >nul
if not errorlevel 1 (
    echo ❌ APIキーが設定されていません
    echo.
    echo 📝 設定方法:
    echo 1. https://unsplash.com/developers にアクセス
    echo 2. アプリケーションを作成してAccess Keyを取得
    echo 3. src/main.py のAPI_KEYを実際のキーに置き換え
    echo.
    pause
    exit /b 1
)

REM ToolSettings.jsonの存在確認
if not exist "ToolSettings.json" (
    echo 📝 初回実行: ToolSettings.json が作成されます
)

echo 🚀 GetFreeWallpapers を実行します...
echo ℹ️  既存画像はスキップして、設定枚数分を確実にダウンロードします
echo 🗄️  メタデータはSQLiteデータベースで管理されます
echo.

REM Pythonスクリプトを実行
python src/main.py

REM 実行結果の確認
if errorlevel 1 (
    echo.
    echo ❌ エラーが発生しました
    echo 💡 上記のエラーメッセージを確認してください
) else (
    echo.
    echo ✅ 実行完了しました
    echo 📂 ダウンロードフォルダの 'gfp' フォルダをご確認ください
    echo 🗄️  メタデータは 'wallpapers.db' データベースに保存されています
    echo 💡 'python src/db_manager.py stats' でデータベース統計を確認できます
)

echo.
echo ================================
echo   処理が完了しました
echo ================================
echo.
pause