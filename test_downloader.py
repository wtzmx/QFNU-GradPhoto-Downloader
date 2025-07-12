#!/usr/bin/env python3
"""
测试照片下载器的功能
"""

import sys
from photo_downloader import PhotoDownloader

def test_album_info_extraction():
    """测试相册信息提取功能"""
    print("测试相册信息提取功能...")

    # 使用默认的相册URL
    test_url = "https://www.xxpie.com/m/album?id=684fe6d7e66eb911b3071bc3&nowatermark=Njg0ZmU2ZDdlNjZlYjkxMWIzMDcxYmMzJDA=&mini=0"

    downloader = PhotoDownloader(debug=True)
    try:
        album_info = downloader.extract_album_info(test_url)
        print(f"相册ID: {album_info['album_id']}")
        print(f"无水印参数: {album_info['no_watermark']}")
        print(f"引用页面: {album_info['referer']}")
        return album_info['album_id'] == "684fe6d7e66eb911b3071bc3"
    except Exception as e:
        print(f"提取失败: {e}")
        return False

def test_api_photo_parsing():
    """测试API照片数据解析"""
    print("\n测试API照片数据解析...")

    # 模拟API返回的照片数据
    test_photo = {
        "gallery_ossobject_version_id": "728385355681918976",
        "file_name": "R5L_0934.jpg",
        "file_size": 3283905,
        "width": 3907,
        "height": 2604,
        "url_thumbnail": "https://imagex.xxpie.com/H175048175625322001_PC_HELPER~tplv-kw15pnjg77-photos.thumbnail.jpeg?sign=1752301348288-s0000-imagex-025a11b69e1d61cf11d9394bb28fa707",
        "url_origin": "https://imagex.xxpie.com/H175048175625322001_PC_HELPER~tplv-kw15pnjg77-image.image?attname=R5L_0934.jpg&sign=1752301348294-s0000-imagex-f052278b9e8a3195cd0c27acdfd2daf9"
    }

    downloader = PhotoDownloader(debug=True)

    # 测试不同质量的URL提取
    for quality, url_key in downloader.quality_options.items():
        if url_key in test_photo:
            print(f"  {quality}: {test_photo[url_key][:60]}...")

    # 测试图片信息转换
    image_info = {
        'url': test_photo['url_origin'],
        'name': test_photo['file_name'],
        'size': test_photo['file_size'],
        'width': test_photo['width'],
        'height': test_photo['height']
    }

    print(f"\n转换后的图片信息:")
    print(f"  文件名: {image_info['name']}")
    print(f"  大小: {image_info['size']/1024/1024:.1f}MB")
    print(f"  分辨率: {image_info['width']}x{image_info['height']}")

    return image_info['name'] == "R5L_0934.jpg"

def test_filename_extraction():
    """测试文件名提取功能"""
    print("\n测试文件名提取功能...")
    
    test_url = "https://imagex.xxpie.com/H175048175625322001_PC_HELPER~tplv-kw15pnjg77-image.image?attname=R5L_0934.jpg&sign=1752300960749-s0000-imagex-80e9963217df404c9d3530a08b99775e"
    
    from urllib.parse import urlparse, parse_qs, unquote
    
    parsed_url = urlparse(test_url)
    query_params = parse_qs(parsed_url.query)
    filename = query_params.get('attname', ['unknown'])[0]
    filename = unquote(filename)
    
    print(f"URL: {test_url[:80]}...")
    print(f"提取的文件名: {filename}")
    
    return filename == "R5L_0934.jpg"

def main():
    """主测试函数"""
    print("照片下载器测试程序")
    print("=" * 50)
    
    tests = [
        ("相册信息提取功能", test_album_info_extraction),
        ("API照片数据解析", test_api_photo_parsing),
        ("文件名提取功能", test_filename_extraction),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: 通过")
                passed += 1
            else:
                print(f"❌ {test_name}: 失败")
        except Exception as e:
            print(f"❌ {test_name}: 异常 - {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
