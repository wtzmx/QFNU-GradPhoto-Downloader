#!/usr/bin/env python3
"""
演示新的API功能
"""

from photo_downloader import PhotoDownloader
import json

def demo_album_info():
    """演示相册信息提取"""
    print("=" * 50)
    print("演示：相册信息提取")
    print("=" * 50)
    
    # 使用默认的相册URL
    test_url = "https://www.xxpie.com/m/album?id=684fe6d7e66eb911b3071bc3&nowatermark=Njg0ZmU2ZDdlNjZlYjkxMWIzMDcxYmMzJDA=&mini=0"
    
    downloader = PhotoDownloader(debug=True)
    
    try:
        album_info = downloader.extract_album_info(test_url)
        print(f"✅ 成功解析相册信息:")
        print(f"   相册ID: {album_info['album_id']}")
        print(f"   无水印参数: {album_info['no_watermark']}")
        print(f"   引用页面: {album_info['referer'][:60]}...")
        return album_info
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None

def demo_quality_options():
    """演示图片质量选项"""
    print("\n" + "=" * 50)
    print("演示：图片质量选项")
    print("=" * 50)
    
    downloader = PhotoDownloader()
    
    print("可用的图片质量选项:")
    for i, (quality, url_key) in enumerate(downloader.quality_options.items(), 1):
        print(f"  {i}. {quality:12} -> {url_key}")
    
    # 模拟照片数据
    sample_photo = {
        "file_name": "R5L_0934.jpg",
        "file_size": 3283905,
        "width": 3907,
        "height": 2604,
        "url_thumbnail": "https://imagex.xxpie.com/...thumbnail.jpeg",
        "url_large500": "https://imagex.xxpie.com/...500px.jpeg", 
        "url_large800": "https://imagex.xxpie.com/...800px.jpeg",
        "url_large1024": "https://imagex.xxpie.com/...1024px.jpeg",
        "url_large": "https://imagex.xxpie.com/...1920px.jpeg",
        "url_large1920": "https://imagex.xxpie.com/...2560px.jpeg",
        "url_origin": "https://imagex.xxpie.com/...origin.image"
    }
    
    print(f"\n示例照片信息:")
    print(f"  文件名: {sample_photo['file_name']}")
    print(f"  大小: {sample_photo['file_size']/1024/1024:.1f}MB")
    print(f"  分辨率: {sample_photo['width']}x{sample_photo['height']}")
    
    print(f"\n不同质量的URL示例:")
    for quality, url_key in downloader.quality_options.items():
        if url_key in sample_photo:
            print(f"  {quality:12}: {sample_photo[url_key][:50]}...")

def demo_api_structure():
    """演示API数据结构"""
    print("\n" + "=" * 50)
    print("演示：API数据结构")
    print("=" * 50)
    
    # 模拟API响应结构
    api_response = {
        "code": 0,
        "result": {
            "count": 0,
            "photos": [
                {
                    "gallery_ossobject_version_id": "728385355681918976",
                    "file_name": "R5L_0934.jpg",
                    "file_size": 3283905,
                    "width": 3907,
                    "height": 2604,
                    "url_origin": "https://imagex.xxpie.com/H175048175625322001_PC_HELPER~tplv-kw15pnjg77-image.image?attname=R5L_0934.jpg&sign=1752301348294-s0000-imagex-f052278b9e8a3195cd0c27acdfd2daf9",
                    "photographer": {
                        "nick_name": "摄影师·李开龙"
                    }
                }
            ]
        }
    }
    
    print("API响应结构示例:")
    print(json.dumps(api_response, indent=2, ensure_ascii=False)[:500] + "...")
    
    print(f"\n关键字段说明:")
    print(f"  code: API状态码 (0表示成功)")
    print(f"  result.photos: 照片数组")
    print(f"  file_name: 原始文件名")
    print(f"  file_size: 文件大小(字节)")
    print(f"  width/height: 图片分辨率")
    print(f"  url_*: 不同质量的图片URL")

def main():
    """主演示函数"""
    print("毕业典礼照片下载工具 v3.0 - API功能演示")
    print("本演示展示新版本的主要功能和改进")
    
    # 演示相册信息提取
    album_info = demo_album_info()
    
    # 演示图片质量选项
    demo_quality_options()
    
    # 演示API数据结构
    demo_api_structure()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)
    print("主要改进总结:")
    print("✅ 使用官方API，更稳定可靠")
    print("✅ 支持7种图片质量选择")
    print("✅ 自动提取访问令牌")
    print("✅ 显示详细文件信息")
    print("✅ 分页获取完整列表")
    print("✅ 改进的错误处理")
    
    print(f"\n要开始下载，请运行:")
    print(f"python photo_downloader.py")

if __name__ == "__main__":
    main()
