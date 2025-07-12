#!/usr/bin/env python3
"""
快速测试默认URL功能
"""

from photo_downloader import PhotoDownloader

def test_default_url():
    """测试默认URL解析"""
    print("测试默认URL功能")
    print("=" * 50)
    
    # 默认URL
    default_url = "https://www.xxpie.com/m/album?id=684fe6d7e66eb911b3071bc3&nowatermark=Njg0ZmU2ZDdlNjZlYjkxMWIzMDcxYmMzJDA=&mini=0"
    
    print(f"默认相册URL:")
    print(f"{default_url}")
    
    downloader = PhotoDownloader(debug=True)
    
    try:
        # 测试URL解析
        album_info = downloader.extract_album_info(default_url)
        
        print(f"\n✅ URL解析成功:")
        print(f"   相册ID: {album_info['album_id']}")
        print(f"   无水印参数: {album_info['no_watermark']}")
        
        # 测试API URL构建
        api_url = "https://int.xxpie.com/api/pm/queryAlbumItemsPgByDefaultSort"
        params = {
            'album_id': album_info['album_id'],
            'page_no': 1,
            'page_size': 60,
            'platform': 'H5'
        }
        
        if album_info.get('no_watermark'):
            params['no_watermark'] = album_info['no_watermark']
        
        print(f"\n📡 API请求信息:")
        print(f"   URL: {api_url}")
        print(f"   参数: {params}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_quality_selection():
    """测试图片质量选择"""
    print(f"\n" + "=" * 50)
    print("测试图片质量选择")
    print("=" * 50)
    
    downloader = PhotoDownloader()
    
    print("可用的图片质量选项:")
    quality_descriptions = {
        'thumbnail': '缩略图 - 最小文件',
        'large500': '500px - 小文件',
        'large800': '800px - 中等文件',
        'large1024': '1024px - 较大文件',
        'large': '1920px - 大文件',
        'large1920': '2560px - 超大文件',
        'origin': '原图 - 最大文件，最高质量 ⭐️推荐'
    }
    
    for i, (quality, url_key) in enumerate(downloader.quality_options.items(), 1):
        description = quality_descriptions.get(quality, '')
        print(f"  {i}. {quality:12} -> {description}")
    
    print(f"\n💡 使用建议:")
    print(f"   • 网络较慢或存储空间有限：选择 1-4")
    print(f"   • 一般使用：选择 5-6") 
    print(f"   • 最佳质量：选择 7 (原图)")
    
    return True

def main():
    """主测试函数"""
    print("毕业典礼照片下载工具 - 快速测试")
    print("测试默认URL和基本功能")
    
    tests = [
        ("默认URL解析", test_default_url),
        ("图片质量选择", test_quality_selection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"\n✅ {test_name}: 通过")
                passed += 1
            else:
                print(f"\n❌ {test_name}: 失败")
        except Exception as e:
            print(f"\n❌ {test_name}: 异常 - {e}")
    
    print(f"\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        print(f"\n🚀 现在可以运行主程序:")
        print(f"python photo_downloader.py")
        print(f"直接按回车使用默认相册，选择图片质量后开始下载！")
    else:
        print("⚠️  部分测试失败")

if __name__ == "__main__":
    main()
