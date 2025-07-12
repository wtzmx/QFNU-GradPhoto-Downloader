# 测试和演示文件说明

本目录包含项目的测试脚本和演示程序。

## 📁 文件说明

### 🧪 测试脚本
- **`test_downloader.py`** - 核心功能测试
  - 相册信息提取测试
  - API照片数据解析测试
  - 文件名提取功能测试

- **`test_concurrent.py`** - 并发功能测试
  - 并发下载功能测试
  - 进度跟踪功能测试
  - 线程安全性测试

- **`quick_test.py`** - 快速功能验证
  - 默认URL解析测试
  - 图片质量选择测试
  - 基本功能验证

### 🎯 演示程序
- **`demo_api.py`** - API功能演示
  - 相册信息提取演示
  - 图片质量选项演示
  - API数据结构演示

- **`performance_demo.py`** - 性能对比演示
  - 串行 vs 并发性能对比
  - 不同并发数效果展示
  - 真实场景性能估算

## 🚀 运行方式

### 运行所有测试
```bash
# 在项目根目录运行
python tests/test_downloader.py
python tests/test_concurrent.py
python tests/quick_test.py
```

### 查看演示
```bash
# API功能演示
python tests/demo_api.py

# 性能对比演示
python tests/performance_demo.py
```

## 📊 测试覆盖

- ✅ URL解析和验证
- ✅ API数据处理
- ✅ 并发下载机制
- ✅ 线程安全性
- ✅ 错误处理
- ✅ 性能基准测试

## 💡 开发建议

在修改主程序后，建议运行相关测试确保功能正常：

1. **修改URL处理逻辑** → 运行 `test_downloader.py`
2. **修改并发机制** → 运行 `test_concurrent.py`
3. **修改基础功能** → 运行 `quick_test.py`
4. **性能优化后** → 运行 `performance_demo.py`
