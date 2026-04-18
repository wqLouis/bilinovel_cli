# bilinovel-cli

哔哩轻小说命令行下载工具。

[English](./README_en.md)

## 安装

```bash
# 安装 playwright 浏览器
playwright install chromium
```

## 使用方法

```bash
# 查看小说信息
bilinovel info <novel_id>

# 查看目录
bilinovel catalog <novel_id>

# 下载小说（交互式选择卷）
bilinovel download <novel_id>

# 下载指定卷
bilinovel download <novel_id> -v 0 1 2

# 设置请求间隔（秒）
bilinovel download <novel_id> -i 1.0

# 指定输出目录
bilinovel download <novel_id> -o ./novels
```

## 免安装运行

```bash
uv run python main.py <command>
```

## 输出格式

小说以每章一个 .txt 文件的方式保存，按卷分组。

```
小说标题/
├── 卷标题_1/
│   ├── Chapter 1.txt
│   └── Chapter 2.txt
└── 卷标题_2/
    └── Chapter 1.txt
```

## 致谢

- [bilinovel-download](https://github.com/ShqWW/bilinovel-download/tree/master) - 提供了 rubbish_secret_map 字符映射数据
