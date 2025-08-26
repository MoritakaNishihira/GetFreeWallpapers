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
        
        # ダウンロードディレクトリを作成
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def search_wallpapers(self, theme, count=10, resolution="regular", orientation="landscape"):
        """
        テーマに基づいて壁紙を検索
        
        Args:
            theme (str): 検索テーマ（例: "nature", "city", "minimal"）
            count (int): 取得枚数（最大30）
            resolution (str): 画質 ("thumb", "small", "regular", "full", "raw")
            orientation (str): 向き ("landscape", "portrait", "squarish")
            
        Returns:
            list: 画像データのリスト
        """
        url = f"{self.base_url}/search/photos"
        params = {
            "query": theme,
            "per_page": min(count, 30),  # 最大30枚まで
            "orientation": orientation,
            "order_by": "relevant"
        }
        
        try:
            print(f"🔍 テーマ '{theme}' で検索中...")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            photos = data.get("results", [])
            
            print(f"✅ {len(photos)}枚の画像が見つかりました")
            return photos
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 検索エラー: {e}")
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
                    "resolution": "regular",
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
    
    def download_image(self, photo, resolution="regular"):
        """
        画像をダウンロード
        
        Args:
            photo (dict): Unsplash APIから取得した画像データ
            resolution (str): ダウンロード解像度
            
        Returns:
            str: ダウンロードしたファイルパス（失敗時はNone）
        """
        try:
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
            filepath = os.path.join(self.download_dir, filename)
            
            # 既にダウンロード済みかチェック
            if os.path.exists(filepath):
                print(f"⏭️  既存: {filename}")
                return filepath
            
            # 画像をダウンロード
            print(f"⬇️  ダウンロード中: {filename}")
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # ファイルに保存
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # メタデータを保存
            self.save_metadata(photo, filepath)
            
            print(f"✅ 完了: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
            return None
    
    def save_metadata(self, photo, filepath):
        """
        画像のメタデータをJSONファイルに保存
        """
        metadata = {
            "id": photo["id"],
            "description": photo.get("alt_description"),
            "photographer": photo["user"]["name"],
            "photographer_url": photo["user"]["links"]["html"],
            "unsplash_url": photo["links"]["html"],
            "download_date": datetime.now().isoformat(),
            "license": "Unsplash License",
            "tags": [tag["title"] for tag in photo.get("tags", [])]
        }
        
        metadata_path = filepath.replace(".jpg", "_metadata.json")
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
        resolution = settings.get("resolution", "regular")
        
        print(f"🚀 GetFreeWallpapers - 壁紙収集を開始します")
        print(f"📝 有効なテーマ数: {len(enabled_themes)}")
        print(f"📊 各テーマ {count_per_theme}枚ずつ取得")
        print(f"💾 保存先: {self.download_dir}")
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
            for photo in photos:
                if self.download_image(photo, resolution):
                    theme_downloaded += 1
                    total_downloaded += 1
                
                # API制限を考慮して少し待機
                time.sleep(0.5)
            
            print(f"📁 {theme_name}: {theme_downloaded}枚ダウンロード完了")
            print("-" * 30)
        
        print(f"🎉 収集完了！合計 {total_downloaded}枚の壁紙をダウンロードしました")
        print(f"📂 保存場所: {self.download_dir}")
    
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