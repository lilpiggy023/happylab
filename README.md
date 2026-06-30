# 素材打标台

本项目是一个本地运行的投流素材工作台，支持素材库、剧集库、AI 拉片、自动打标、标签库维护、Prompt 配置，以及短剧投流故事线和剪映草稿导出流程。

## 主要功能

- 上传素材并自动执行抽帧、拆音频、转写、AI 拉片和自动打标
- 管理素材库与剧集库，支持按素材名和标签筛选
- 维护多层级标签体系、标签定义、标签墓地和标签合并/转移
- 在 Prompt 页面编辑拉片、打标、字幕转写、字幕翻译、故事线、剪辑清单等 AI Prompt
- 基于剧集生成投流故事线、剪辑清单、预览视频和剪映草稿包

## 启动方式

```powershell
cd C:\Users\xieyiming\Documents\AI拉片\material_tagging_app
python .\server.py
```

打开：

```text
http://127.0.0.1:8765
```

## 数据说明

标签库配置文件保存在：

```text
material_tagging_app/data/tag_library.json
```

上传视频、剧集源文件、分析产物、本地安装包和模型文件体积较大，已通过 `.gitignore` 排除，不直接进入 Git 仓库。

## 本地模型

本地模型没有直接放入 Git 文件树，已上传到 GitHub Release：

```text
https://github.com/lilpiggy023/ShortDrama_Ai_Marketing/releases/tag/local-models-v1
```

包含：

- `faster-whisper-small-bucket.zip`
- `vosk-model-small-en-us-0.15.zip`

下载后建议放回：

```text
C:\Users\xieyiming\Documents\AI拉片\models
C:\Users\xieyiming\Documents\AI拉片\vosk-model-small-en-us-0.15
```

