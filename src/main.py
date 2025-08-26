#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetFreeWallpapers - Unsplash APIを使った無料壁紙自動収集ツール

機能:
- テーマ別の壁紙検索・ダウンロード
- JSON設定ファイルでのテーマ管理
- ダウンロードフォルダ内のgfpフォルダに保存
- メタデータ付きでダウンロード
"""

import requests
import os
import json
import time
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

class GetFreeWallpapers:
    def __init__(self, api_key):
        """
        GetFreeWallpapers - Unsplash壁紙収集ツール
        
        Args:
            api_key (str): Unsplash API キー
        """
        self.api_key = api_key
        self.base_url = "https://api.unsplash.com"
        self.headers = {"Authorization": f"Client-ID {api_key}"}
        
        # ダウンロードフォルダ内にgfpフォルダを作成
        downloads_folder = Path.home() / "Downloads"
        self.download_dir = downloads_folder / "gfp"
        
        # srcフォルダと同じ階層にdownloaded_jsonフォルダを作成
        current_dir = Path(__file__).parent  # src フォルダのパス
        project_root = current_dir.parent    # プロジェクトルートのパス
        self.json_dir = project_root / "downloaded_json"
        
        # ダウンロードディレクトリとJSONディレクトリを作成
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
    
    def search_wallpapers(self, theme, count=10, resolution="full", orientation="landscape"):
        """
        テーマに基づいて壁紙を検索
        
        Args:
            theme (str): 検索テーマ（例: "nature", "city", "minimal"）
            count (int): 取得枚数（最大30）
            resolution (str): 画質 ("thumb", "small", "regular", "full", "raw")
            orientation (str): 向き ("landscape", "portrait", "squarish")
            
        Returns:
            list: 画像データのリスト（フルHD以上の横長画像のみ）
        """
        url = f"{self.base_url}/search/photos"
        params = {
            "query": theme,
            "per_page": min(count * 3, 30),  # フィルタリングを考慮して多めに取得
            "orientation": orientation,
            "order_by": "relevant"
        }
        
        try:
            print(f"🔍 テーマ '{theme}' で検索中...")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            all_photos = data.get("results", [])
            
            # フルHD以上の横長画像のみをフィルタリング
            filtered_photos = []
            for photo in all_photos:
                width = photo.get("width", 0)
                height = photo.get("height", 0)
                
                # フルHD以上 (1920x1080) かつ横長 (アスペクト比 > 1.2) の画像のみ
                if width >= 1920 and height >= 1080 and (width / height) > 1.2:
                    filtered_photos.append(photo)
                    if len(filtered_photos) >= count:
                        break
            
            print(f"✅ {len(filtered_photos)}枚のフルHD以上横長画像が見つかりました")
            return filtered_photos
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 検索エラー: {e}")
            return []
    
    def load_themes_config(self, config_file="themes.json"):
        """
        テーマ設定ファイルを読み込み
        
        Args:
            config_file (str): 設定ファイル名
            
        Returns:
            dict: テーマ設定
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 設定ファイル '{config_file}' を読み込みました")
            return config
        except FileNotFoundError:
            # デフォルト設定ファイルを作成
            default_config = {
                "settings": {
                    "count_per_theme": 5,
                    "resolution": "full",
                    "orientation": "landscape"
                },
                "themes": [
                    {
                        "name": "自然風景",
                        "query": "nature landscape",
                        "enabled": True
                    },
                    {
                        "name": "ミニマルデザイン",
                        "query": "minimal abstract",
                        "enabled": True
                    },
                    {
                        "name": "都市建築",
                        "query": "city architecture",
                        "enabled": True
                    },
                    {
                        "name": "海の夕日",
                        "query": "ocean sunset",
                        "enabled": False
                    },
                    {
                        "name": "森と山",
                        "query": "forest mountains",
                        "enabled": False
                    }
                ]
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            print(f"📝 デフォルト設定ファイル '{config_file}' を作成しました")
            print(f"💡 設定を変更してから再実行してください")
            return default_config
        except json.JSONDecodeError as e:
            print(f"❌ 設定ファイルの形式が正しくありません: {e}")
            return None
    
    def is_already_downloaded(self, photo):
        """
        画像が既にダウンロード済みかを判定（downloaded_jsonフォルダ内のメタデータを確認）
        
        Args:
            photo (dict): Unsplash APIから取得した画像データ
            
        Returns:
            tuple: (bool, str) - (既にダウンロード済みか, 既存ファイルパス)
        """
        photo_id = photo["id"]
        
        # downloaded_jsonフォルダ内の既存メタデータファイルをチェック
        if not self.json_dir.exists():
            return False, None
            
        for json_file in self.json_dir.glob("*_metadata.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                
                # 画像IDが一致する場合
                if existing_metadata.get("id") == photo_id:
                    # 対応する画像ファイルが存在するかチェック
                    image_filename = existing_metadata.get("image_file")
                    if image_filename:
                        image_path = self.download_dir / image_filename
                        if image_path.exists():
                            return True, str(image_path)
                        else:
                            # メタデータはあるが画像ファイルがない場合は古いJSONを削除
                            json_file.unlink()
                            print(f"🗑️  古いメタデータファイルを削除: {json_file.name}")
                            
            except (json.JSONDecodeError, OSError) as e:
                # 破損したJSONファイルは削除
                try:
                    json_file.unlink()
                    print(f"🗑️  破損したメタデータファイルを削除: {json_file.name}")
                except:
                    pass
        
        return False, None
    
    def download_image(self, photo, resolution="full"):
        """
        画像をダウンロード
        
        Args:
            photo (dict): Unsplash APIから取得した画像データ
            resolution (str): ダウンロード解像度
            
        Returns:
            str: ダウンロードしたファイルパス（失敗時はNone）
        """
        try:
            # 既にダウンロード済みかチェック
            is_downloaded, existing_path = self.is_already_downloaded(photo)
            if is_downloaded:
                print(f"⏭️  既存: {os.path.basename(existing_path)} (ID: {photo['id']})")
                return existing_path
            
            # 画像URLを取得
            image_url = photo["urls"].get(resolution)
            if not image_url:
                print(f"❌ {resolution}解像度が利用できません")
                return None
            
            # ファイル名を生成
            photo_id = photo["id"]
            photographer = photo["user"]["name"].replace(" ", "_")
            description = photo.get("alt_description", "wallpaper").replace(" ", "_")[:30]
            
            # ファイル拡張子を取得
            parsed_url = urlparse(image_url)
            ext = ".jpg"  # Unsplashは主にJPG形式
            
            filename = f"{photo_id}_{photographer}_{description}{ext}"
            # ファイル名から不正な文字を除去
            filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
            filepath = self.download_dir / filename
            
            # 画像をダウンロード
            print(f"⬇️  ダウンロード中: {filename} ({photo.get('width', '?')}x{photo.get('height', '?')})")
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # ファイルに保存
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # メタデータを保存（JSONフォルダに）
            self.save_metadata(photo, str(filepath))
            
            print(f"✅ 完了: {filename}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
            return None
    
    def save_metadata(self, photo, filepath):
        """
        画像のメタデータをdownloaded_jsonフォルダ内のJSONファイルに保存
        """
        metadata = {
            "id": photo["id"],
            "description": photo.get("alt_description"),
            "photographer": photo["user"]["name"],
            "photographer_url": photo["user"]["links"]["html"],
            "unsplash_url": photo["links"]["html"],
            "download_date": datetime.now().isoformat(),
            "license": "Unsplash License",
            "tags": [tag["title"] for tag in photo.get("tags", [])],
            "dimensions": {
                "width": photo.get("width"),
                "height": photo.get("height")
            },
            "image_file": os.path.basename(filepath)
        }
        
        # JSONファイルはdownloaded_jsonフォルダに保存
        json_filename = os.path.basename(filepath).replace(".jpg", "_metadata.json")
        metadata_path = self.json_dir / json_filename
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def collect_wallpapers_from_config(self, config_file="themes.json"):
        """
        設定ファイルから壁紙を収集
        
        Args:
            config_file (str): 設定ファイル名
        """
        config = self.load_themes_config(config_file)
        if not config:
            return
        
        settings = config.get("settings", {})
        themes = config.get("themes", [])
        
        # 有効なテーマのみを抽出
        enabled_themes = [theme for theme in themes if theme.get("enabled", True)]
        
        if not enabled_themes:
            print("❌ 有効なテーマが設定されていません")
            return
        
        total_downloaded = 0
        count_per_theme = settings.get("count_per_theme", 5)
        resolution = settings.get("resolution", "full")
        
        print(f"🚀 GetFreeWallpapers - 壁紙収集を開始します")
        print(f"📝 有効なテーマ数: {len(enabled_themes)}")
        print(f"📊 各テーマ {count_per_theme}枚ずつ取得（フルHD以上の横長画像のみ）")
        print(f"💾 保存先: {self.download_dir}")
        print(f"📄 メタデータ保存先: {self.json_dir}")
        print("-" * 50)
        
        for theme_config in enabled_themes:
            theme_name = theme_config.get("name", "不明")
            query = theme_config.get("query", "")
            
            print(f"🎨 テーマ: {theme_name} (検索: '{query}')")
            
            if not query:
                print(f"⚠️  スキップ: 検索クエリが設定されていません")
                continue
            
            photos = self.search_wallpapers(
                query, 
                count_per_theme, 
                resolution, 
                settings.get("orientation", "landscape")
            )
            
            if not photos:
                continue
            
            theme_downloaded = 0
            theme_skipped = 0
            for photo in photos:
                result = self.download_image(photo, resolution)
                if result:
                    # 既存ファイルかどうかで処理を分ける
                    if "既存" in str(result) or self.is_already_downloaded(photo)[0]:
                        theme_skipped += 1
                    else:
                        theme_downloaded += 1
                        total_downloaded += 1
                
                # API制限を考慮して少し待機
                time.sleep(0.5)
            
            if theme_skipped > 0:
                print(f"📁 {theme_name}: 新規{theme_downloaded}枚、既存{theme_skipped}枚")
            else:
                print(f"📁 {theme_name}: {theme_downloaded}枚ダウンロード完了")
            print("-" * 30)
        
        print(f"🎉 収集完了！合計 {total_downloaded}枚のフルHD以上壁紙をダウンロードしました")
        print(f"📂 画像保存場所: {self.download_dir}")
        print(f"📄 メタデータ保存場所: {self.json_dir}")
    
    def collect_wallpapers(self, themes, count_per_theme=10, resolution="regular"):
        """
        複数のテーマで壁紙を収集
        
        Args:
            themes (list): テーマのリスト
            count_per_theme (int): テーマ毎の取得枚数
            resolution (str): ダウンロード解像度
        """
        total_downloaded = 0
        
        print(f"🚀 壁紙収集を開始します")
        print(f"📝 テーマ: {', '.join(themes)}")
        print(f"📊 各テーマ {count_per_theme}枚ずつ取得")
        print(f"💾 保存先: {self.download_dir}/")
        print("-" * 50)
        
        for theme in themes:
            photos = self.search_wallpapers(theme, count_per_theme, resolution)
            
            if not photos:
                continue
            
            theme_downloaded = 0
            for photo in photos:
                if self.download_image(photo, resolution):
                    theme_downloaded += 1
                    total_downloaded += 1
                
                # API制限を考慮して少し待機
                time.sleep(0.5)
            
            print(f"📁 {theme}: {theme_downloaded}枚ダウンロード完了")
            print("-" * 30)
        
        print(f"🎉 収集完了！合計 {total_downloaded}枚の壁紙をダウンロードしました")
        print(f"📂 保存場所: {self.download_dir}")

def main():
    # ここにあなたのUnsplash APIキーを設定してください
    API_KEY = "PIjfN_jat7xYlFUpFKMmvv_a9HU-YTwT9CkhKeZgGt4"  # https://unsplash.com/developers で取得
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌ エラー: APIキーを設定してください")
        print("1. https://unsplash.com/developers にアクセス")
        print("2. アプリケーションを作成")
        print("3. Access Keyを取得")
        print("4. スクリプト内のAPI_KEYを置き換えてください")
        return
    
    # 壁紙収集ツールを初期化
    collector = GetFreeWallpapers(API_KEY)
    
    # 設定ファイルから壁紙を収集
    collector.collect_wallpapers_from_config("themes.json")

if __name__ == "__main__":
    main()