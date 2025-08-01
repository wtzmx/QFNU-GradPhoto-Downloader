#!/usr/bin/env python3
"""
毕业典礼照片批量下载脚本
注意：请确保已获得合法授权并遵守网站使用条款
"""

import requests
import json
import os
import time
import re
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
import hashlib
import hmac
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue


class PhotoDownloader:
    def __init__(self, download_dir: str = "graduation_photos", debug: bool = False, max_workers: int = 8):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.debug = debug
        self.access_token = None
        self.max_workers = max_workers

        # 并发控制
        self.download_lock = threading.Lock()
        self.progress_lock = threading.Lock()
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0
        }

        # 基础请求头模板
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Origin': 'https://www.xxpie.com',
        }

        # 图片质量选择
        self.quality_options = {
            'thumbnail': 'url_thumbnail',      # 缩略图
            'large500': 'url_large500',        # 500px
            'large800': 'url_large800',        # 800px
            'large1024': 'url_large1024',      # 1024px
            'large': 'url_large',              # 1920px
            'large1920': 'url_large1920',      # 2560px
            'origin': 'url_origin'             # 原图
        }

    def create_session(self) -> requests.Session:
        """为每个线程创建独立的session"""
        session = requests.Session()
        session.headers.update(self.base_headers)
        return session

    def debug_print(self, message: str):
        """调试输出"""
        if self.debug:
            print(f"[DEBUG] {message}")

    def extract_album_info(self, album_url: str) -> Dict[str, str]:
        """从相册URL中提取相册信息"""
        try:
            parsed_url = urlparse(album_url)
            query_params = parse_qs(parsed_url.query)

            album_id = query_params.get('id', [None])[0]
            no_watermark = query_params.get('nowatermark', [None])[0]

            if not album_id:
                raise ValueError("无法从URL中提取album_id")

            return {
                'album_id': album_id,
                'no_watermark': no_watermark or '',
                'referer': album_url
            }
        except Exception as e:
            raise ValueError(f"解析相册URL失败: {e}")

    def extract_access_token(self, html_content: str) -> Optional[str]:
        """从页面内容中提取access token"""
        # 查找可能包含token的模式
        token_patterns = [
            r'"x-access-token":\s*"([^"]+)"',
            r'x-access-token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'accessToken["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        ]

        for pattern in token_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                token = match.group(1)
                if len(token) > 50:  # JWT token通常很长
                    self.debug_print(f"找到access token: {token[:20]}...")
                    return token

        return None
        
    def get_album_page(self, album_url: str) -> Optional[str]:
        """获取相册页面内容"""
        try:
            session = self.create_session()
            # 设置正确的referer
            session.headers.update({
                'Referer': album_url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            })

            response = session.get(album_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"获取相册页面失败: {e}")
            return None

    def get_photos_from_api(self, album_info: Dict[str, str], access_token: str = None) -> List[Dict]:
        """通过API获取照片列表"""
        all_photos = []
        page_no = 1
        page_size = 60

        session = self.create_session()

        # 设置API请求头
        api_headers = session.headers.copy()
        api_headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Referer': album_info['referer'],
        })

        if access_token:
            api_headers['x-access-token'] = access_token
            self.debug_print(f"使用access token: {access_token[:20]}...")

        while True:
            try:
                # 构建API URL
                api_url = "https://int.xxpie.com/api/pm/queryAlbumItemsPgByDefaultSort"
                params = {
                    'album_id': album_info['album_id'],
                    'page_no': page_no,
                    'page_size': page_size,
                    'platform': 'H5'
                }

                # 添加可选参数
                if album_info.get('no_watermark'):
                    params['no_watermark'] = album_info['no_watermark']

                # 尝试从相册URL中提取sub_album_id
                referer_params = parse_qs(urlparse(album_info['referer']).query)
                if 'sub_album_id' in referer_params:
                    params['sub_album_id'] = referer_params['sub_album_id'][0]

                self.debug_print(f"请求API: {api_url}")
                self.debug_print(f"参数: {params}")

                response = session.get(api_url, params=params, headers=api_headers)
                response.raise_for_status()

                data = response.json()
                self.debug_print(f"API响应状态码: {data.get('code', 'unknown')}")

                if data.get('code') != 0:
                    print(f"API返回错误: {data.get('message', '未知错误')}")
                    break

                result = data.get('result', {})
                photos = result.get('photos', [])

                if not photos:
                    self.debug_print(f"第{page_no}页没有更多照片")
                    break

                all_photos.extend(photos)
                print(f"获取第{page_no}页: {len(photos)}张照片")

                # 检查是否还有更多页面
                if len(photos) < page_size:
                    break

                page_no += 1
                time.sleep(0.1)  # API请求间隔

            except requests.RequestException as e:
                print(f"API请求失败: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"API响应解析失败: {e}")
                break

        return all_photos
    
    def extract_image_urls(self, html_content: str) -> List[Dict[str, str]]:
        """从页面内容中提取图片URL"""
        image_info = []

        # 方法1：查找可能包含图片信息的JSON数据
        json_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.albumData\s*=\s*({.+?});',
            r'var\s+albumData\s*=\s*({.+?});',
            r'photoList\s*:\s*(\[.+?\])',
        ]

        for pattern in json_patterns:
            json_match = re.search(pattern, html_content, re.DOTALL)
            if json_match:
                try:
                    data_str = json_match.group(1)
                    data = json.loads(data_str)

                    # 尝试不同的数据结构
                    photo_lists = []
                    if isinstance(data, dict):
                        # 查找可能的照片列表
                        for key in ['photos', 'photoList', 'images', 'list', 'data']:
                            if key in data and isinstance(data[key], list):
                                photo_lists.append(data[key])

                        # 递归查找嵌套结构
                        def find_photo_arrays(obj, depth=0):
                            if depth > 3:  # 限制递归深度
                                return
                            if isinstance(obj, dict):
                                for v in obj.values():
                                    if isinstance(v, list) and len(v) > 0:
                                        # 检查是否像照片数组
                                        if isinstance(v[0], dict) and any(k in str(v[0]) for k in ['url', 'src', 'image']):
                                            photo_lists.append(v)
                                    elif isinstance(v, (dict, list)):
                                        find_photo_arrays(v, depth + 1)
                            elif isinstance(obj, list):
                                for item in obj:
                                    find_photo_arrays(item, depth + 1)

                        find_photo_arrays(data)
                    elif isinstance(data, list):
                        photo_lists.append(data)

                    # 处理找到的照片列表
                    for photo_list in photo_lists:
                        for photo in photo_list:
                            if isinstance(photo, dict):
                                # 查找URL字段
                                url = None
                                name = None

                                for url_key in ['url', 'src', 'image', 'imageUrl', 'photoUrl']:
                                    if url_key in photo and photo[url_key]:
                                        url = photo[url_key]
                                        break

                                for name_key in ['name', 'filename', 'title', 'originalName']:
                                    if name_key in photo and photo[name_key]:
                                        name = photo[name_key]
                                        break

                                if url and 'imagex.xxpie.com' in url:
                                    # 从URL中提取文件名（如果没有找到name）
                                    if not name:
                                        parsed_url = urlparse(url)
                                        query_params = parse_qs(parsed_url.query)
                                        name = query_params.get('attname', [f'image_{len(image_info)+1}.jpg'])[0]

                                    image_info.append({
                                        'url': url,
                                        'name': name
                                    })

                    if image_info:
                        print(f"通过JSON数据找到 {len(image_info)} 张图片")
                        return image_info

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"解析JSON数据失败: {e}")
                    continue

        # 方法2：使用正则表达式查找imagex.xxpie.com域名的图片链接
        print("尝试使用正则表达式提取图片链接...")
        url_patterns = [
            r'https://imagex\.xxpie\.com/[^"\s<>]+',
            r'"(https://imagex\.xxpie\.com/[^"]+)"',
            r"'(https://imagex\.xxpie\.com/[^']+)'",
        ]

        all_urls = set()
        for pattern in url_patterns:
            urls = re.findall(pattern, html_content)
            all_urls.update(urls)

        for url in all_urls:
            # 确保URL完整且包含必要参数
            if 'attname=' in url and 'sign=' in url:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                filename = query_params.get('attname', [f'image_{len(image_info)+1}.jpg'])[0]
                filename = unquote(filename)  # URL解码

                image_info.append({
                    'url': url,
                    'name': filename
                })

        # 去重
        seen_urls = set()
        unique_images = []
        for img in image_info:
            if img['url'] not in seen_urls:
                seen_urls.add(img['url'])
                unique_images.append(img)

        print(f"通过正则表达式找到 {len(unique_images)} 张图片")
        return unique_images
    
    def download_single_image(self, image_info: Dict, referer_url: str, thread_id: int) -> Dict:
        """下载单张图片（线程安全版本）"""
        result = {
            'success': False,
            'filename': image_info['name'],
            'error': None,
            'skipped': False,
            'size': 0
        }

        try:
            # 为每个线程创建独立的session
            session = self.create_session()

            # 设置下载请求头
            headers = session.headers.copy()
            headers.update({
                'Referer': referer_url or 'https://www.xxpie.com/',
                'Origin': 'https://www.xxpie.com',
                'Priority': 'u=1, i',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
            })

            # 清理文件名
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', image_info['name'])
            filepath = self.download_dir / safe_filename

            # 检查文件是否已存在
            if filepath.exists():
                existing_size = filepath.stat().st_size
                expected_size = image_info.get('size', 0)
                if expected_size > 0 and existing_size == expected_size:
                    result['skipped'] = True
                    result['success'] = True
                    result['size'] = existing_size
                    return result

            # 下载文件
            response = session.get(image_info['url'], headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                result['error'] = f"响应不是图片类型: {content_type}"
                return result

            # 确保文件有扩展名
            if '.' not in safe_filename:
                if 'jpeg' in content_type or 'jpg' in content_type:
                    safe_filename += '.jpg'
                elif 'png' in content_type:
                    safe_filename += '.png'
                else:
                    safe_filename += '.jpg'
                filepath = self.download_dir / safe_filename

            # 写入文件
            downloaded_size = 0
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

            result['success'] = True
            result['size'] = downloaded_size
            result['filename'] = safe_filename

        except requests.RequestException as e:
            result['error'] = f"网络错误: {e}"
        except IOError as e:
            result['error'] = f"文件写入错误: {e}"
        except Exception as e:
            result['error'] = f"未知错误: {e}"

        return result

    def update_progress(self, result: Dict):
        """更新下载进度（线程安全）"""
        with self.progress_lock:
            if result['success']:
                if result['skipped']:
                    self.stats['skipped'] += 1
                else:
                    self.stats['completed'] += 1
            else:
                self.stats['failed'] += 1

            # 显示进度
            total = self.stats['total']
            completed = self.stats['completed']
            failed = self.stats['failed']
            skipped = self.stats['skipped']
            processed = completed + failed + skipped

            if result['success']:
                status = "跳过" if result['skipped'] else "完成"
                size_info = f" ({result['size']/1024/1024:.1f}MB)" if result['size'] > 0 else ""
                print(f"[{processed}/{total}] {status}: {result['filename']}{size_info}")
            else:
                print(f"[{processed}/{total}] 失败: {result['filename']} - {result['error']}")

            # 显示总体进度
            if processed % 50 == 0 or processed == total:
                progress_percent = (processed / total) * 100
                print(f"\n📊 总进度: {progress_percent:.1f}% ({processed}/{total}) - 成功:{completed}, 跳过:{skipped}, 失败:{failed}\n")
    
    def choose_quality(self) -> str:
        """选择图片质量"""
        print("\n请选择下载图片质量:")
        print("1. 缩略图 (thumbnail) - 最小文件")
        print("2. 500px (large500) - 小文件")
        print("3. 800px (large800) - 中等文件")
        print("4. 1024px (large1024) - 较大文件")
        print("5. 1920px (large) - 大文件")
        print("6. 2560px (large1920) - 超大文件")
        print("7. 原图 (origin) - 最大文件，最高质量")

        while True:
            choice = input("请选择 (1-7，默认选择原图): ").strip()
            if not choice:
                choice = "7"

            quality_map = {
                "1": "thumbnail",
                "2": "large500",
                "3": "large800",
                "4": "large1024",
                "5": "large",
                "6": "large1920",
                "7": "origin"
            }

            if choice in quality_map:
                selected_quality = quality_map[choice]
                print(f"已选择: {selected_quality}")
                return selected_quality
            else:
                print("无效选择，请输入1-7之间的数字")

    def download_album(self, album_url: str, quality: str = "origin") -> int:
        """下载整个相册"""
        print(f"开始处理相册: {album_url}")

        try:
            # 解析相册信息
            album_info = self.extract_album_info(album_url)
            print(f"相册ID: {album_info['album_id']}")

            # 获取相册页面
            html_content = self.get_album_page(album_url)
            if not html_content:
                return 0

            # 保存页面内容用于调试
            debug_file = self.download_dir / "page_content.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"页面内容已保存到: {debug_file}")

            # 尝试提取access token
            access_token = self.extract_access_token(html_content)
            if access_token:
                print("✅ 找到访问令牌")
            else:
                print("⚠️  未找到访问令牌，将尝试无认证访问")

            # 通过API获取照片列表
            print("\n正在获取照片列表...")
            photos = self.get_photos_from_api(album_info, access_token)

            if not photos:
                print("❌ 未能获取到照片列表")
                print("可能的原因:")
                print("1. 需要登录访问")
                print("2. 相册不存在或已删除")
                print("3. 网络连接问题")
                return 0

            print(f"✅ 成功获取 {len(photos)} 张照片信息")

            # 转换为下载列表
            image_list = []
            quality_key = self.quality_options.get(quality, 'url_origin')

            for photo in photos:
                if quality_key in photo and photo[quality_key]:
                    image_list.append({
                        'url': photo[quality_key],
                        'name': photo.get('file_name', f"photo_{photo.get('gallery_ossobject_id', 'unknown')}.jpg"),
                        'size': photo.get('file_size', 0),
                        'width': photo.get('width', 0),
                        'height': photo.get('height', 0)
                    })

            if not image_list:
                print(f"❌ 没有找到{quality}质量的图片URL")
                return 0

            print(f"\n📊 图片信息统计:")
            print(f"图片数量: {len(image_list)}")
            print(f"选择质量: {quality}")

            # 计算总大小
            total_size = sum(img.get('size', 0) for img in image_list)
            if total_size > 0:
                print(f"预计总大小: {total_size / 1024 / 1024:.1f} MB")

            # 显示前几张图片信息
            print(f"\n前5张图片预览:")
            for i, img in enumerate(image_list[:5]):
                size_info = f" ({img['size']/1024/1024:.1f}MB)" if img['size'] > 0 else ""
                resolution = f" {img['width']}x{img['height']}" if img['width'] > 0 else ""
                print(f"  {i+1}. {img['name']}{size_info}{resolution}")

            if len(image_list) > 5:
                print(f"  ... 还有 {len(image_list) - 5} 张图片")

            # 确认下载
            confirm = input(f"\n确认下载这 {len(image_list)} 张图片？(y/N): ").strip().lower()
            if confirm != 'y':
                print("已取消下载")
                return 0

            # 开始下载
            return self.batch_download(image_list, album_url)

        except Exception as e:
            print(f"❌ 处理相册时出错: {e}")
            import traceback
            traceback.print_exc()
            return 0


    def batch_download(self, image_list: List[Dict], referer_url: str) -> int:
        """并发批量下载图片"""
        self.stats['total'] = len(image_list)
        self.stats['completed'] = 0
        self.stats['failed'] = 0
        self.stats['skipped'] = 0

        failed_list = []

        print(f"\n🚀 开始并发下载 {len(image_list)} 张图片...")
        print(f"📊 并发线程数: {self.max_workers}")
        print(f"{'='*60}")

        start_time = time.time()

        # 使用线程池进行并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有下载任务
            future_to_image = {
                executor.submit(self.download_single_image, image_info, referer_url, i): image_info
                for i, image_info in enumerate(image_list)
            }

            # 处理完成的任务
            for future in as_completed(future_to_image):
                image_info = future_to_image[future]
                try:
                    result = future.result()
                    self.update_progress(result)

                    if not result['success']:
                        failed_list.append(image_info)

                except Exception as e:
                    print(f"任务执行异常: {image_info['name']} - {e}")
                    failed_list.append(image_info)
                    with self.progress_lock:
                        self.stats['failed'] += 1

        end_time = time.time()
        duration = end_time - start_time

        # 显示最终统计
        print(f"\n{'='*60}")
        print(f"📊 下载完成统计:")
        print(f"   总数量: {self.stats['total']}")
        print(f"   成功: {self.stats['completed']}")
        print(f"   跳过: {self.stats['skipped']}")
        print(f"   失败: {self.stats['failed']}")
        print(f"   耗时: {duration:.1f}秒")

        if self.stats['completed'] > 0:
            avg_speed = self.stats['completed'] / duration
            print(f"   平均速度: {avg_speed:.1f}张/秒")

        # 处理失败的图片
        if failed_list:
            print(f"\n❌ 失败的图片 ({len(failed_list)} 张):")
            for img in failed_list[:10]:  # 只显示前10个
                print(f"   - {img['name']}")
            if len(failed_list) > 10:
                print(f"   ... 还有 {len(failed_list) - 10} 张")

            # 询问是否重试
            retry = input(f"\n是否重试失败的 {len(failed_list)} 张图片？(y/N): ").strip().lower()
            if retry == 'y':
                print(f"\n🔄 开始重试失败的图片...")
                retry_success = self.retry_failed_downloads(failed_list, referer_url)
                print(f"\n重试完成！重试成功 {retry_success}/{len(failed_list)} 张图片")
                return self.stats['completed'] + retry_success

        return self.stats['completed']

    def retry_failed_downloads(self, failed_list: List[Dict], referer_url: str) -> int:
        """重试失败的下载（使用较少的并发数）"""
        retry_workers = min(4, self.max_workers)  # 重试时使用较少的线程
        retry_success = 0

        print(f"使用 {retry_workers} 个线程重试...")

        with ThreadPoolExecutor(max_workers=retry_workers) as executor:
            future_to_image = {
                executor.submit(self.download_single_image, image_info, referer_url, i): image_info
                for i, image_info in enumerate(failed_list)
            }

            for future in as_completed(future_to_image):
                image_info = future_to_image[future]
                try:
                    result = future.result()
                    if result['success']:
                        retry_success += 1
                        status = "跳过" if result['skipped'] else "完成"
                        print(f"重试{status}: {result['filename']}")
                    else:
                        print(f"重试失败: {result['filename']} - {result['error']}")
                except Exception as e:
                    print(f"重试异常: {image_info['name']} - {e}")

        return retry_success


def main():
    """主函数"""
    print("毕业典礼照片批量下载工具 v4.0 (并发版本)")
    print("=" * 60)
    print("🚀 v4.0 新功能:")
    print("• 多线程并发下载，速度大幅提升")
    print("• 智能进度显示和统计信息")
    print("• 线程安全的文件处理")
    print("• 失败重试机制")
    print("• 支持大量图片的高效下载")
    print("=" * 60)
    print("📋 继承功能:")
    print("• 使用官方API获取照片列表")
    print("• 支持多种图片质量选择")
    print("• 显示文件大小和分辨率信息")
    print("• 改进的错误处理机制")
    print("=" * 60)
    print("注意事项：")
    print("1. 请确保已获得学校或照片提供方的合法授权")
    print("2. 请遵守网站使用条款和robots.txt规定")
    print("3. 请合理使用，避免对服务器造成过大压力")
    print("4. 本工具仅供学习交流使用，请勿用于商业用途")
    print("=" * 60)

    # 获取相册URL
    default_url = "https://www.xxpie.com/m/album?id=684fe6d7e66eb911b3071bc3&nowatermark=Njg0ZmU2ZDdlNjZlYjkxMWIzMDcxYmMzJDA=&mini=0"

    print(f"\n默认相册URL:")
    print(f"{default_url}")

    while True:
        album_url = input(f"\n请输入相册页面URL (直接按回车使用默认URL): ").strip()

        # 如果用户直接按回车，使用默认URL
        if not album_url:
            album_url = default_url
            print(f"✅ 使用默认相册URL")
            break

        if not album_url.startswith('https://www.xxpie.com/m/album'):
            print("❌ 错误：请提供有效的相册URL")
            print("URL应该以 'https://www.xxpie.com/m/album' 开头")
            print("示例: https://www.xxpie.com/m/album?id=684fe6d7e66eb911b3071bc3&nowatermark=...")

            retry = input("是否重新输入？(y/N): ").strip().lower()
            if retry != 'y':
                print("已退出程序")
                return
            continue

        print(f"✅ 使用自定义相册URL")
        break

    print(f"\n相册URL: {album_url}")

    # 设置下载目录
    default_dir = "graduation_photos"
    download_dir = input(f"请输入下载目录 (默认: {default_dir}): ").strip()
    if not download_dir:
        download_dir = default_dir

    print(f"下载目录: {download_dir}")

    # 设置并发数
    print(f"\n⚙️  并发设置:")
    print(f"推荐并发数:")
    print(f"• 网络较慢: 4-8 线程")
    print(f"• 网络一般: 8-16 线程")
    print(f"• 网络较快: 16-32 线程")

    while True:
        max_workers_input = input(f"请输入并发线程数 (默认: 8): ").strip()
        if not max_workers_input:
            max_workers = 8
            break
        try:
            max_workers = int(max_workers_input)
            if 1 <= max_workers <= 50:
                break
            else:
                print("并发数应在1-50之间")
        except ValueError:
            print("请输入有效的数字")

    print(f"并发线程数: {max_workers}")

    try:
        # 创建下载器
        downloader = PhotoDownloader(download_dir, debug=False, max_workers=max_workers)

        # 选择图片质量
        quality = downloader.choose_quality()

        # 确认开始处理
        confirm = input(f"\n确认开始处理相册？(y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消下载")
            return

        # 开始下载
        success_count = downloader.download_album(album_url, quality)

        if success_count > 0:
            print(f"\n🎉 下载完成！共成功下载 {success_count} 张图片")
            print(f"📁 文件保存在: {download_dir}")
        else:
            print("\n❌ 没有成功下载任何图片")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断下载")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()