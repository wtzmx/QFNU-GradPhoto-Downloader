#!/usr/bin/env python3
"""
性能对比演示 - 展示并发下载的优势
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
from pathlib import Path

def simulate_download(url, filename, delay=0.1):
    """模拟下载一个文件"""
    time.sleep(delay)  # 模拟网络延迟和下载时间
    return f"Downloaded: {filename}"

def serial_download_demo(file_count=50):
    """串行下载演示"""
    print(f"🐌 串行下载演示 ({file_count}个文件)")
    print("-" * 40)
    
    start_time = time.time()
    results = []
    
    for i in range(file_count):
        filename = f"photo_{i:03d}.jpg"
        result = simulate_download(f"http://example.com/{filename}", filename, 0.05)
        results.append(result)
        
        # 显示进度
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            speed = (i + 1) / elapsed
            print(f"进度: {i+1}/{file_count}, 速度: {speed:.1f}张/秒")
    
    total_time = time.time() - start_time
    avg_speed = file_count / total_time
    
    print(f"✅ 串行下载完成")
    print(f"   总时间: {total_time:.2f}秒")
    print(f"   平均速度: {avg_speed:.1f}张/秒")
    
    return total_time, avg_speed

def concurrent_download_demo(file_count=50, max_workers=8):
    """并发下载演示"""
    print(f"\n🚀 并发下载演示 ({file_count}个文件, {max_workers}线程)")
    print("-" * 40)
    
    start_time = time.time()
    completed = 0
    lock = threading.Lock()
    
    def download_with_progress(i):
        nonlocal completed
        filename = f"photo_{i:03d}.jpg"
        result = simulate_download(f"http://example.com/{filename}", filename, 0.05)
        
        with lock:
            completed += 1
            if completed % 10 == 0:
                elapsed = time.time() - start_time
                speed = completed / elapsed
                print(f"进度: {completed}/{file_count}, 速度: {speed:.1f}张/秒")
        
        return result
    
    # 使用线程池并发下载
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_with_progress, i) for i in range(file_count)]
        results = [future.result() for future in futures]
    
    total_time = time.time() - start_time
    avg_speed = file_count / total_time
    
    print(f"✅ 并发下载完成")
    print(f"   总时间: {total_time:.2f}秒")
    print(f"   平均速度: {avg_speed:.1f}张/秒")
    
    return total_time, avg_speed

def performance_comparison():
    """性能对比"""
    print("=" * 60)
    print("📊 性能对比演示")
    print("=" * 60)
    print("注意：这是模拟测试，实际效果取决于网络条件")
    print()
    
    file_count = 100
    
    # 串行下载
    serial_time, serial_speed = serial_download_demo(file_count)
    
    # 不同并发数的测试
    concurrent_results = []
    for workers in [4, 8, 16]:
        concurrent_time, concurrent_speed = concurrent_download_demo(file_count, workers)
        concurrent_results.append((workers, concurrent_time, concurrent_speed))
    
    # 显示对比结果
    print(f"\n" + "=" * 60)
    print("📈 性能对比结果")
    print("=" * 60)
    print(f"{'方式':<15} {'时间(秒)':<10} {'速度(张/秒)':<12} {'加速比':<8}")
    print("-" * 50)
    print(f"{'串行下载':<15} {serial_time:<10.2f} {serial_speed:<12.1f} {'1.0x':<8}")
    
    for workers, time_taken, speed in concurrent_results:
        speedup = serial_time / time_taken
        print(f"{f'{workers}线程并发':<15} {time_taken:<10.2f} {speed:<12.1f} {speedup:<8.1f}x")
    
    # 计算最佳性能
    best_workers, best_time, best_speed = max(concurrent_results, key=lambda x: x[2])
    best_speedup = serial_time / best_time
    
    print(f"\n🏆 最佳性能: {best_workers}线程并发")
    print(f"   速度提升: {best_speedup:.1f}倍")
    print(f"   时间节省: {((serial_time - best_time) / serial_time * 100):.1f}%")

def real_world_estimation():
    """真实世界性能估算"""
    print(f"\n" + "=" * 60)
    print("🌍 真实场景性能估算")
    print("=" * 60)
    
    scenarios = [
        ("小相册", 100, "约2-3MB/张"),
        ("中等相册", 500, "约3-4MB/张"),
        ("大相册", 1000, "约3-5MB/张"),
        ("超大相册", 3749, "约3-5MB/张"),  # 用户的实际情况
    ]
    
    print(f"{'场景':<10} {'照片数':<8} {'文件大小':<12} {'串行时间':<10} {'并发时间(8线程)':<15} {'时间节省':<10}")
    print("-" * 80)
    
    for name, count, size, in scenarios:
        # 假设串行下载速度为1.5张/秒，并发8线程为12张/秒
        serial_time_min = count / 1.5 / 60  # 转换为分钟
        concurrent_time_min = count / 12 / 60
        time_saved = serial_time_min - concurrent_time_min
        
        print(f"{name:<10} {count:<8} {size:<12} {serial_time_min:<10.1f}分 {concurrent_time_min:<15.1f}分 {time_saved:<10.1f}分")
    
    print(f"\n💡 对于3749张照片的相册:")
    print(f"   串行下载: 约41.7分钟")
    print(f"   8线程并发: 约5.2分钟")
    print(f"   时间节省: 约36.5分钟 (87.5%)")

def main():
    """主演示函数"""
    print("毕业典礼照片下载工具 - 性能演示")
    print("展示v4.0并发下载的性能优势")
    
    try:
        # 性能对比演示
        performance_comparison()
        
        # 真实场景估算
        real_world_estimation()
        
        print(f"\n" + "=" * 60)
        print("🎯 总结")
        print("=" * 60)
        print("✅ 并发下载显著提升下载速度")
        print("✅ 线程数越多，速度提升越明显（有上限）")
        print("✅ 对于大量照片，时间节省非常显著")
        print("✅ v4.0版本特别适合3000+张照片的相册")
        
        print(f"\n🚀 立即体验高速下载:")
        print(f"python photo_downloader.py")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  演示被中断")

if __name__ == "__main__":
    main()
