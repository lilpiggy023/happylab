from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote
from email.parser import BytesParser
from email.policy import default
import base64
import json
import hashlib
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import threading
import traceback
import urllib.error
import urllib.request
import uuid
import copy


ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(ROOT, ".."))
STATIC_DIR = os.path.join(ROOT, "static")
LOCAL_VIDEO_DEPS = os.path.join(WORKSPACE, ".codex_video_deps")
if os.path.isdir(LOCAL_VIDEO_DEPS) and LOCAL_VIDEO_DEPS not in sys.path:
    sys.path.insert(0, LOCAL_VIDEO_DEPS)
DATA_DIR = os.path.join(ROOT, "data")
ASSET_DIR = os.path.join(DATA_DIR, "assets")
SERIES_DIR = os.path.join(DATA_DIR, "series")
DB_PATH = os.path.join(DATA_DIR, "tag_library.json")
SKILL_SCRIPT = r"C:\Users\xieyiming\.codex\skills\video-ai-analysis-skill-v1\scripts\video_ai_prep.py"
VOSK_MODEL_CANDIDATES = [
    r"C:\tmp\ai_lapian\vosk-model-small-en-us-0.15",
    os.path.join(WORKSPACE, "vosk-model-small-en-us-0.15"),
]
AI_BASE_URL = "https://ai.pocketcity.com/v1/chat/completions"
AI_MODEL = "gemini-3.1-pro-preview"
PERSONA_CATEGORY = "人设组合"
CATEGORY_ALIASES = {
    "人设组合": PERSONA_CATEGORY,
    "核心人设组合": PERSONA_CATEGORY,
    "人设": PERSONA_CATEGORY,
    "人设组合（身份/角色配置 + 气质/状态 + 人物关系 + 关系张力）": PERSONA_CATEGORY,
    "人设组合（身份/角色配置 + 气质/状态 + 核心关系 + 关系张力）": PERSONA_CATEGORY,
}
TASKS = {}
TASK_LOCK = threading.Lock()
DB_LOCK = threading.RLock()

DEFAULT_PROMPTS = {
    "reportSystem": "你是严谨的短剧投流素材拉片专家，输出 Markdown，不输出无依据内容。",
    "reportUser": "你是投流短剧素材拉片分析师。请严格参照 Video AI Analysis Skill V1，基于抽帧图片、metadata、已生成的音频转写字幕、画面烧录字幕/OCR，生成正式的中文优先中英双语 Markdown 拉片报告。\n请以 audio_transcript 为主要台词依据，同时逐帧读取画面里的烧录字幕、片头字、CTA文案和可见文字。若音频转写和画面字幕互相冲突，以剧情动作和画面可见字幕交叉校验，并明确标注不确定处。\n不要写占位模板，不要声称看不到已提供的图片；如果转写不可靠，要明确说明并结合画面判断。\n报告必须包含：基础信息、一句话判断、关键叙事结构、可学习点、完整转写/字幕表、分段拉片、关键新增发现、画面与声音协同、AI生成特征、风险与审核点、改稿建议、可复用优化版梗概、发布判断。\n报告需要能直接用于后续素材自动打标。\n\n素材结构化信息：\n```json\n{context_json}\n```",
    "tagSystem": "你是投流素材标签策略专家，严格输出可解析 JSON。",
    "tagUser": "请根据拉片报告为投流素材打标，只能输出 JSON，不要输出 Markdown。\nJSON 格式：{\"tags\": {\"一级标签\": [\"二级标签\"]}, \"tagDefinitions\": {\"一级标签\": {\"二级标签\": \"标签定义\"}}, \"summary\": \"一句话摘要\", \"evidence\": {\"一级/二级\": [\"证据短语\"]}}。\n请同时参考标签库和标签墓地：\n1. 优先和标签库比对，相似含义必须直接使用标签库已有标签；\n2. 不要生成标签墓地中已有或高度相似的标签；\n3. 只有标签库和标签墓地都没有合适标签时，才可以少量新增标签，并且必须在 tagDefinitions 中给出新标签定义；\n4. 相似含义请合并，不要制造近义重复标签。\n\n标签库与标签墓地：\n{schema_json}\n\n拉片报告：\n{report_text}",
    "storylineSystem": 'You are a short-drama ad editing strategist. Return valid JSON only.',
    "storylineUser": 'You are designing paid-acquisition short-drama edits. Based on the report, transcript, tags, and frame index, generate 3-5 distinct storylines that can become 20-90 second ads.\nReturn only one valid JSON object. Do not output Markdown.\nRequired JSON shape: {"storylines":[{"id":"story-1","title":"Chinese storyline title","duration":"target edit duration","targetAudience":"audience","hook":"first 3 seconds hook","arc":"editing narrative arc","reason":"why it may convert","risk":"review or comprehension risk","segments":[{"episodeId":"episode id when source is a series","sourceStart":"00:00.00","sourceEnd":"00:05.00","role":"hook/conflict/twist/payoff/promise","reason":"why this source segment is useful"}]}]}\nRules: if source_type is series, every segment must include episodeId; use source timecodes when possible; preserve strong conflict, identity relationship, reversal, payoff, and suspense; do not invent events not supported by the source.\n\nSOURCE CONTEXT:\n{source_context}',
    "cutlistSystem": 'You are a short-drama ad editor. Return valid timeline JSON only.',
    "cutlistUser": 'Turn the selected ad storyline into an executable cutlist. Return only one valid JSON object.\nRequired JSON shape: {"title":"Chinese edit title","estimatedDuration":"estimated final duration","logic":"editing logic","segments":[{"episodeId":"episode id when source is a series","sourceStart":"00:00.00","sourceEnd":"00:05.00","role":"hook/conflict/twist/payoff/CTA","caption":"optional overlay subtitle","reason":"why this segment is selected"}],"coverSuggestion":"cover suggestion","subtitleStyle":"subtitle style suggestion"}\nRules: if source_type is series, every segment must include episodeId; source timecodes must be from the original episode/video and within duration; each segment should be 1-12 seconds when possible; total target is 20-90 seconds; segments may come from different episodes if useful.\n\nSELECTED STORYLINE:\n{selected_storyline}\n\nSOURCE CONTEXT:\n{source_context}',
    "transcribeSystem": '你是严谨的多语种字幕转写员。你必须只输出一个 JSON 对象，不输出 Markdown、解释或代码块。',
    "transcribeUser": '请转写这个短视频音频。自动识别语言，不要默认英文。必须只输出 JSON 对象，格式：{"language":"识别语言","segments":[{"index":1,"start":"00:00.00","end":"00:02.30","text":"原文字幕","translation_zh":"中文翻译","confidence":"high/medium/low"}],"notes":"不确定说明"}。segments 至少 1 条。不要输出 ```json。',
    "translateSystem": '你是专业字幕翻译员。只输出合法 JSON，不输出 Markdown、解释或代码块。',
    "translateUser": '把下面字幕逐条翻译成自然、准确的简体中文。保留 index，不要合并、不要增删条目。只输出 JSON：{"segments":[{"index":1,"translation_zh":"中文翻译"}],"notes":""}\n\n{transcript_payload}',
    "transcriptRepairSystem": '你是 JSON 修复器。只输出合法 JSON 对象。',
    "transcriptRepairUser": '把下面模型返回内容整理成合法 JSON。字段必须是 language、segments、notes；segments 每项必须包含 index、start、end、text、translation_zh、confidence。只能输出 JSON。\n\n{raw_response}',
}
PROMPT_META = {
    "skillName": "Video AI Analysis Skill V1",
    "model": AI_MODEL,
    "endpoint": AI_BASE_URL,
    "placeholders": {
        "reportUser": ["{context_json}"],
        "tagUser": ["{schema_json}", "{report_text}"],
        "storylineUser": ["{source_context}"],
        "cutlistUser": ["{selected_storyline}", "{source_context}"],
        "translateUser": ["{transcript_payload}"],
        "transcriptRepairUser": ["{raw_response}"],
    },
}

def is_within(base, target):
    base = os.path.abspath(base)
    target = os.path.abspath(target)
    return target == base or target.startswith(base + os.sep)


def asset_url(asset_id, relative_path):
    rel = relative_path.replace(os.sep, "/")
    return f"/asset-files/{asset_id}/{rel}"


def series_episode_url(episode_id, relative_path):
    rel = relative_path.replace(os.sep, "/")
    return f"/series-files/{episode_id}/{rel}"


def collect_episode_artifacts(episode):
    episode_id = episode.get("id", "")
    analysis_dir = episode.get("analysisDir", "")
    artifacts = {"analysisDir": analysis_dir, "storyboard": None, "frames": [], "reports": [], "artifactNotes": [], "files": []}
    if not analysis_dir or not os.path.isdir(analysis_dir):
        return artifacts
    for root, _, files in os.walk(analysis_dir):
        for name in files:
            full_path = os.path.join(root, name)
            rel = os.path.relpath(full_path, analysis_dir)
            lower = name.lower()
            item = {"name": name, "path": full_path, "relativePath": rel, "url": series_episode_url(episode_id, rel), "size": os.path.getsize(full_path)}
            if lower == "storyboard.jpg":
                artifacts["storyboard"] = item
            elif lower.endswith(".md"):
                if re.match(r"ai_video_analysis(_visual)?_bilingual\.md$", lower): artifacts["reports"].append(item)
                else: artifacts["artifactNotes"].append(item)
            elif lower.endswith((".txt", ".srt", ".json", ".wav", ".mp3", ".mp4")):
                artifacts["files"].append(item)
            elif rel.replace("\\", "/").lower().startswith("frames/") and lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                artifacts["frames"].append(item)
    for key in ["frames", "reports", "artifactNotes", "files"]:
        artifacts[key] = sorted(artifacts[key], key=lambda x: x.get("relativePath") or x.get("name") or "")
    return artifacts


def episode_file_names(artifacts):
    return {str(item.get("name") or "").lower() for item in (artifacts or {}).get("files", [])}


def episode_has_report(artifacts):
    return bool((artifacts or {}).get("reports"))


def episode_has_transcript(artifacts):
    names = episode_file_names(artifacts)
    return any(name in names for name in ["transcript.txt", "transcript_zh.txt", "transcript.json", "transcript_zh.json"])


def episode_has_prep_outputs(artifacts):
    names = episode_file_names(artifacts)
    return bool((artifacts or {}).get("storyboard") or (artifacts or {}).get("frames") or "audio_for_ai.mp3" in names or "audio_16k_mono.wav" in names or "prep_result.json" in names)


def derive_series_episode_status(ep, artifacts=None):
    artifacts = artifacts or collect_episode_artifacts(ep)
    if episode_has_report(artifacts):
        return "分析完成"
    if episode_has_transcript(artifacts):
        return "字幕转写完成，待生成 AI 报告"
    if episode_has_prep_outputs(artifacts):
        return "抽帧与音频完成，待转写字幕"
    if str(ep.get("status") or "").startswith("分析失败"):
        return ep.get("status")
    return "等待分析"


def series_episode_complete(ep):
    return episode_has_report(collect_episode_artifacts(ep))




def enrich_series(db):
    changed = False
    for series in db.get("series", []):
        series.setdefault("episodes", [])
        if not isinstance(series.get("storylines"), list):
            series["storylines"] = []
            changed = True
        series["episodes"].sort(key=lambda ep: int(ep.get("episodeNo") or 0))
        for ep in series.get("episodes", []):
            artifacts = collect_episode_artifacts(ep)
            derived_status = derive_series_episode_status(ep, artifacts)
            if ep.get("artifacts") != artifacts:
                ep["artifacts"] = artifacts
                changed = True
            if ep.get("status") != derived_status and ep.get("status") not in ["处理中", "排队中"]:
                ep["status"] = derived_status
                ep["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
                changed = True
    if changed:
        save_db(db)
    return db




def create_series(title):
    safe_title = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", title or "untitled-series").strip("-") or "untitled-series"
    series_id = f"series-{int(time.time() * 1000)}-{safe_title[:24]}"
    folder = os.path.join(SERIES_DIR, series_id)
    os.makedirs(folder, exist_ok=True)
    return series_id, folder


def find_or_create_series(db, title):
    clean = str(title or "").strip() or "未命名剧集"
    for row in db.get("series", []):
        if row.get("title") == clean:
            return row
    series_id, folder = create_series(clean)
    row = {"id": series_id, "title": clean, "folder": folder, "episodes": [], "storylines": [], "createdAt": time.strftime("%Y-%m-%d %H:%M:%S")}
    db.setdefault("series", []).insert(0, row)
    return row


def get_series_episode_record(episode_id):
    db = load_db()
    for series in db.get("series", []):
        for ep in series.get("episodes", []):
            if ep.get("id") == episode_id:
                return db, series, ep
    raise ValueError("剧集单集不存在")


def update_series_episode_record(episode_id, updater):
    db, series, ep = get_series_episode_record(episode_id)
    updater(ep, series)
    ep["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_db(db)
    return ep


def create_series_pipeline_task(series_id, episode_id, api_key=""):
    task_id = f"series-task-{episode_id}"
    db, series, ep = get_series_episode_record(episode_id)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    with TASK_LOCK:
        existing = TASKS.get(task_id)
        if existing and existing.get("status") in ["排队中", "处理中"]:
            return dict(existing)
        task = {"id": task_id, "seriesId": series_id, "episodeId": episode_id, "title": f"{series.get('title')} 第{ep.get('episodeNo')}集", "status": "排队中", "stage": "等待分析", "progress": 3, "createdAt": now, "updatedAt": now, "error": ""}
        TASKS[task_id] = task
    threading.Thread(target=run_series_pipeline_task, args=(task_id, episode_id, api_key), daemon=True).start()
    return dict(task)


def run_series_pipeline_task(task_id, episode_id, api_key=""):
    try:
        db, series, ep = get_series_episode_record(episode_id)
        analysis_dir = ep.get("analysisDir")
        artifacts = collect_episode_artifacts(ep)
        if episode_has_report(artifacts):
            def after_existing_report(row, _series):
                row["status"] = "分析完成"
                row["artifacts"] = collect_episode_artifacts(row)
            update_series_episode_record(episode_id, after_existing_report)
            update_task(task_id, status="完成", stage="分析完成", progress=100, error="")
            return

        if not episode_has_prep_outputs(artifacts):
            update_task(task_id, status="处理中", stage="解析抽帧与音频", progress=10)
            skill_result = run_skill(ep.get("videoPath", ""), analysis_dir)
            storyboard_path, storyboard_warning = ensure_storyboard_from_frames(analysis_dir)
            audio_path, audio_warning = ensure_ai_audio({"videoPath": ep.get("videoPath"), "analysisDir": analysis_dir})
            if not skill_result.get("ok"):
                raise ValueError("素材解析失败，请检查 ffmpeg 或视频文件")
            def after_prep(row, _series):
                row["skillResult"] = skill_result
                row["audioPath"] = audio_path
                row["storyboardPath"] = storyboard_path
                row["status"] = "抽帧与音频完成，待转写字幕"
                row.pop("taskError", None)
                row["artifacts"] = collect_episode_artifacts(row)
            ep = update_series_episode_record(episode_id, after_prep)
            artifacts = collect_episode_artifacts(ep)
        else:
            update_task(task_id, status="处理中", stage="复用已有抽帧与音频", progress=28)
            storyboard_path = find_analysis_file(analysis_dir, "storyboard.jpg") or ep.get("storyboardPath", "")
            audio_path = find_analysis_file(analysis_dir, "audio_for_ai.mp3") or find_analysis_file(analysis_dir, "audio_16k_mono.wav") or ep.get("audioPath", "")
            def after_reuse_prep(row, _series):
                if storyboard_path:
                    row["storyboardPath"] = storyboard_path
                if audio_path:
                    row["audioPath"] = audio_path
                row["status"] = "抽帧与音频完成，待转写字幕"
                row.pop("taskError", None)
                row["artifacts"] = collect_episode_artifacts(row)
            ep = update_series_episode_record(episode_id, after_reuse_prep)

        artifacts = collect_episode_artifacts(ep)
        if not episode_has_transcript(artifacts):
            update_task(task_id, stage="本地 ASR 转写字幕", progress=38)
            transcript_path = transcribe_asset_local_asr(ep, "auto", "", api_key)
            def after_transcribe(row, _series):
                row["transcriptPath"] = transcript_path
                row["transcriptMethod"] = "本地ASR"
                row["status"] = "字幕转写完成，待生成 AI 报告"
                row.pop("taskError", None)
                row["artifacts"] = collect_episode_artifacts(row)
            ep = update_series_episode_record(episode_id, after_transcribe)
        else:
            update_task(task_id, stage="复用已有字幕", progress=62)
            transcript_path = find_analysis_file(analysis_dir, "transcript.txt") or find_analysis_file(analysis_dir, "transcript_zh.txt") or ep.get("transcriptPath", "")
            def after_reuse_transcript(row, _series):
                if transcript_path:
                    row["transcriptPath"] = transcript_path
                row["status"] = "字幕转写完成，待生成 AI 报告"
                row.pop("taskError", None)
                row["artifacts"] = collect_episode_artifacts(row)
            ep = update_series_episode_record(episode_id, after_reuse_transcript)

        artifacts = collect_episode_artifacts(ep)
        if not episode_has_report(artifacts):
            update_task(task_id, stage="AI 生成拉片报告", progress=70)
            report_path = generate_ai_report(ep, api_key)
        else:
            report_path = (artifacts.get("reports") or [{}])[0].get("path", "")
        def after_report(row, _series):
            if report_path:
                row["sourceReportPath"] = report_path
            row["status"] = "分析完成"
            row.pop("taskError", None)
            row["artifacts"] = collect_episode_artifacts(row)
        update_series_episode_record(episode_id, after_report)
        update_task(task_id, status="完成", stage="分析完成", progress=100, error="")
    except Exception as exc:
        message = str(exc) or type(exc).__name__
        update_task(task_id, status="失败", stage="分析失败", progress=100, error=message)
        try:
            def after_error(row, _series):
                row["status"] = f"分析失败：{message}"
                row["taskError"] = message
                row["artifacts"] = collect_episode_artifacts(row)
            update_series_episode_record(episode_id, after_error)
        except Exception:
            pass
        print("series pipeline task failed", task_id, traceback.format_exc())



def looks_like_placeholder_report(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            text = f.read(5000)
    except Exception:
        return False
    markers = [
        "视觉拉片初稿",
        "素材包自动生成",
        "This report was generated from the prepared analysis package",
        "core conflict and relationship map should be refined",
    ]
    return any(marker in text for marker in markers)


def collect_artifacts(asset):
    asset_id = asset.get("id", "")
    analysis_dir = asset.get("analysisDir", "")
    artifacts = {
        "analysisDir": analysis_dir,
        "storyboard": None,
        "frames": [],
        "reports": [],
        "artifactNotes": [],
        "files": [],
    }
    if not analysis_dir or not os.path.isdir(analysis_dir):
        return artifacts

    for root, _, files in os.walk(analysis_dir):
        for name in files:
            full_path = os.path.join(root, name)
            rel = os.path.relpath(full_path, analysis_dir)
            rel_url = asset_url(asset_id, rel)
            lower = name.lower()
            item = {
                "name": name,
                "path": full_path,
                "relativePath": rel,
                "url": rel_url,
                "size": os.path.getsize(full_path),
            }
            if lower == "storyboard.jpg":
                artifacts["storyboard"] = item
            elif lower.endswith(".md"):
                if re.match(r"ai_video_analysis(_visual)?_bilingual\.md$", lower):
                    artifacts["reports"].append(item)
                else:
                    artifacts["artifactNotes"].append(item)
            elif lower.endswith((".txt", ".srt", ".json")):
                artifacts["files"].append(item)
            elif rel.replace("\\", "/").lower().startswith("frames/") and lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
                artifacts["frames"].append(item)
            elif lower.endswith((".wav", ".mp3", ".mp4")):
                artifacts["files"].append(item)

    artifacts["frames"] = sorted(artifacts["frames"], key=lambda x: x["relativePath"])
    artifacts["reports"] = sorted(artifacts["reports"], key=lambda x: x["name"])
    artifacts["artifactNotes"] = sorted(artifacts["artifactNotes"], key=lambda x: x["name"])
    artifacts["files"] = sorted(artifacts["files"], key=lambda x: x["name"])
    return artifacts


def write_artifact_report(asset, analysis_dir, skill_result):
    report_path = os.path.join(analysis_dir, "analysis_artifacts_note.md")
    status = "成功" if skill_result.get("ok") else "失败"
    lines = [
        f"# {asset.get('title') or asset.get('sourceName') or asset.get('id')} 拉片产物说明",
        "",
        f"- 素材 ID：`{asset.get('id')}`",
        f"- 原视频：`{asset.get('videoPath')}`",
        f"- 拉片状态：{status}",
        f"- 耗时：{skill_result.get('seconds')} 秒",
        f"- 拉片目录：`{analysis_dir}`",
        "",
        "## 主要产物",
        "",
        "- `storyboard.jpg`：抽帧总览图",
        "- `frames/`：代表帧图片",
        "- `metadata.json`：视频基础信息与帧路径",
        "- `audio_for_ai.mp3`：生成正式报告时供大模型转录的压缩音频附件（如可提取）",
        "- `transcript.txt/json/srt`：旧版本地转写产物；可能来自英文 Vosk，仅作低可信参考",
        "",
        "## 说明",
        "",
        "这份文件只记录本次上传拉片生成的素材包，不是双语拉片报告。正式报告需要先完成音频转写，再由 AI 大模型读取字幕、storyboard 和代表帧后生成，并命名为 `AI_video_analysis_bilingual.md` 或 `AI_video_analysis_visual_bilingual.md`，放入同一 analysis 目录后，前端才会展示为可打标报告。",
    ]
    if skill_result.get("stderr"):
        lines.extend(["", "## 运行提示", "", "```text", skill_result.get("stderr", ""), "```"])
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path


def enrich_assets(db):
    changed = False
    for asset in db.get("assets", []):
        analysis_dir = asset.get("analysisDir", "")
        if analysis_dir and os.path.isdir(analysis_dir):
            if not find_analysis_file(analysis_dir, "storyboard.jpg"):
                storyboard_path, _ = ensure_storyboard_from_frames(analysis_dir)
                if storyboard_path:
                    changed = True
            has_report = any(
                name.lower().endswith(".md")
                for _, _, files in os.walk(analysis_dir)
                for name in files
            )
            if not has_report:
                write_artifact_report(asset, analysis_dir, asset.get("skillResult", {}))
                changed = True
        artifacts = collect_artifacts(asset)
        if not artifacts.get("reports") and asset.get("status") in ("拉片完成", "双语报告已生成，待自动打标", "AI分析任务包已准备，待大模型生成正式报告"): 
            asset["status"] = "拉片素材包完成，待AI分析生成双语报告"
            changed = True
        if asset.get("artifacts") != artifacts:
            asset["artifacts"] = artifacts
            changed = True
    if changed:
        save_db(db)
    return db

TAG_SCHEMA = {
    "视频结构": [
        "危机开场",
        "羞辱开场",
        "家庭压迫启动",
        "事故归责升级",
        "赔偿二选一",
        "替代受辱",
        "儿童危机升级",
        "身份伏笔",
        "CTA截断爽点",
    ],
    "核心冲突": [
        "家庭暴力",
        "婆家压迫",
        "重男轻女",
        "婚姻背叛",
        "情敌替代",
        "儿童危机",
        "弱者被冤",
        "金钱赔偿冲突",
        "阶层羞辱",
        "人格羞辱",
        "权势身份反转",
    ],
    "人设": [
        "受辱母亲",
        "被威胁孩子",
        "弱势劳动者",
        "失语弱者",
        "保护者",
        "强势丈夫",
        "恶婆家",
        "富人反派",
        "情敌/替代者",
        "隐藏高位人物",
        "旁观确认者",
    ],
    "题材": [
        "竖屏短剧",
        "虐爽短剧",
        "家庭伦理",
        "豪门反转",
        "母女亲情",
        "底层逆袭",
        "儿童救援",
        "女性受辱反击",
    ],
    "情绪机制": [
        "亲子保护欲",
        "憋屈感",
        "愤怒感",
        "无助感",
        "背叛感",
        "同情心",
        "期待反杀",
        "身份爽感",
    ],
    "钩子设计": [
        "儿童求救钩子",
        "极端羞辱钩子",
        "下跪动作钩子",
        "逼签悬念",
        "赔钱二选一",
        "亲人代受惩罚",
        "高位人物出现",
        "未完待续",
    ],
    "叙事道具": [
        "豪车",
        "清洁工具",
        "签字文件",
        "金项链",
        "家族信物",
        "工资/月薪",
        "家族身份称号",
        "下载页",
    ],
    "关系设定": [
        "母女关系",
        "夫妻压迫关系",
        "婆媳压迫关系",
        "情敌关系",
        "雇佣/服务关系",
        "富人压迫穷人",
        "家族寻找线",
    ],
    "画面表现": [
        "烧录字幕驱动",
        "人物近景对峙",
        "公开羞辱",
        "家庭室内争执",
        "车辆冲突",
        "下跪动作",
        "封锁现场",
        "下载页收口",
    ],
    "风险标签": [
        "家庭暴力风险",
        "儿童伤害风险",
        "人格贬低风险",
        "残障羞辱风险",
        "强制下跪风险",
        "贫富羞辱风险",
        "平台审核风险",
    ],
    "投流价值": [
        "前3秒强钩子",
        "前5秒亲子危机强",
        "情绪浓度高",
        "冲突易懂",
        "爽点延后",
        "关键词重复有效",
        "下载导流强",
    ],
    "优化方向": [
        "明确人物关系",
        "补足事故因果",
        "弱化羞辱台词",
        "强化反转台词",
        "提前埋身份线",
        "保留替代受辱结构",
    ],
}


SYNONYMS = {
    "首富救援": "权势身份反转",
    "首富身份反转": "权势身份反转",
    "高位身份反转": "权势身份反转",
    "Widodo家族线": "权势身份反转",
    "Widodo 线索": "权势身份反转",
    "亲人替母受罚": "替代受辱",
    "亲人代受辱": "替代受辱",
    "替母下跪": "替代受辱",
    "儿童遇险": "儿童危机",
    "亲子危机": "儿童危机",
    "孩子遇险": "儿童危机",
    "低位清洁工": "弱势劳动者",
    "清洁工受辱": "弱势劳动者",
    "富人羞辱": "阶层羞辱",
    "婆家羞辱": "婆家压迫",
    "CTA 导流": "CTA截断爽点",
}


RULES = [
    ("视频结构", "危机开场", ["不要乱碰我的孩子", "快救我", "save me", "danger"]),
    ("视频结构", "羞辱开场", ["下跪的方式", "像宠物狗", "kneel", "sujud"]),
    ("视频结构", "家庭压迫启动", ["婆家", "丈夫", "签", "四年", "in-laws", "husband"]),
    ("视频结构", "事故归责升级", ["车因为她坏了", "车损", "damaged", "push my mother"]),
    ("视频结构", "赔偿二选一", ["下跪三次", "或者赔钱", "kneel three", "or pay"]),
    ("视频结构", "替代受辱", ["我替她", "kneel instead", "sujud gantinya"]),
    ("视频结构", "儿童危机升级", ["Siti jatuh", "Siti 从上面", "把 Siti 带回家"]),
    ("视频结构", "身份伏笔", ["Widodo", "首富", "richest", "Junior Director", "金项链"]),
    ("视频结构", "CTA截断爽点", ["Download and watch more", "MaxReels", "Google Play"]),
    ("核心冲突", "家庭暴力", ["打", "mukul", "violence", "轻轻打"]),
    ("核心冲突", "婆家压迫", ["婆家", "in-laws", "mother-in-law"]),
    ("核心冲突", "重男轻女", ["男孩", "anak laki", "生男孩", "son-preference"]),
    ("核心冲突", "婚姻背叛", ["Dewi", "心爱的", "情敌", "favored rival"]),
    ("核心冲突", "情敌替代", ["Dewi", "替代", "kesayanganku"]),
    ("核心冲突", "儿童危机", ["Siti", "孩子", "child", "anakku"]),
    ("核心冲突", "弱者被冤", ["被冤", "诬陷", "falsely accuses", "apologize"]),
    ("核心冲突", "金钱赔偿冲突", ["赔钱", "一个月工资", "monthly salary", "compensation"]),
    ("核心冲突", "阶层羞辱", ["清洁工", "富", "企业家", "low-status", "class"]),
    ("核心冲突", "人格羞辱", ["像宠物狗", "没用", "useless", "dog"]),
    ("核心冲突", "权势身份反转", ["Widodo", "首富", "Junior Director", "richest"]),
    ("人设", "受辱母亲", ["母亲", "mother", "ibu"]),
    ("人设", "被威胁孩子", ["Siti", "孩子", "child"]),
    ("人设", "弱势劳动者", ["清洁工", "cleaner", "收拾"]),
    ("人设", "失语弱者", ["哑巴", "mute", "voiceless"]),
    ("人设", "保护者", ["保护", "替她", "belain", "protect"]),
    ("人设", "强势丈夫", ["丈夫", "husband"]),
    ("人设", "恶婆家", ["婆家", "in-laws"]),
    ("人设", "富人反派", ["富家", "豪车", "rich woman"]),
    ("人设", "情敌/替代者", ["Dewi", "情敌", "favored rival"]),
    ("人设", "隐藏高位人物", ["Agus Widodo", "Junior Director", "首富"]),
    ("人设", "旁观确认者", ["对，是的", "Eh iya", "确认身份"]),
    ("题材", "竖屏短剧", ["1080x1920", "vertical", "竖屏"]),
    ("题材", "虐爽短剧", ["虐爽", "humiliated", "payoff", "revenge"]),
    ("题材", "家庭伦理", ["家庭", "母亲", "丈夫", "婆家"]),
    ("题材", "豪门反转", ["Widodo", "首富", "豪门", "家族"]),
    ("题材", "母女亲情", ["母女", "Siti", "母亲", "daughter"]),
    ("题材", "底层逆袭", ["低位", "清洁工", "反转", "low-status"]),
    ("题材", "儿童救援", ["救我和 Siti", "带回家", "child danger"]),
    ("题材", "女性受辱反击", ["女主", "mother being publicly humiliated", "受辱"]),
    ("情绪机制", "亲子保护欲", ["不要乱碰我的孩子", "保护母亲", "protecting the mother"]),
    ("情绪机制", "憋屈感", ["被迫", "道歉", "humiliation"]),
    ("情绪机制", "愤怒感", ["重男轻女", "像宠物狗", "没用"]),
    ("情绪机制", "无助感", ["哑巴", "无法辩解", "powerless"]),
    ("情绪机制", "背叛感", ["Dewi", "丈夫", "心爱的"]),
    ("情绪机制", "同情心", ["对不起", "母亲", "贫穷"]),
    ("情绪机制", "期待反杀", ["反转", "救援", "revenge", "payback"]),
    ("情绪机制", "身份爽感", ["首富", "Widodo", "Junior Director"]),
    ("钩子设计", "儿童求救钩子", ["不要乱碰我的孩子", "快救我和 Siti"]),
    ("钩子设计", "极端羞辱钩子", ["像宠物狗", "下跪的方式"]),
    ("钩子设计", "下跪动作钩子", ["下跪", "sujud", "kneel"]),
    ("钩子设计", "逼签悬念", ["不想签", "tanda"]),
    ("钩子设计", "赔钱二选一", ["下跪三次", "或者赔钱"]),
    ("钩子设计", "亲人代受惩罚", ["我替她", "kneel instead"]),
    ("钩子设计", "高位人物出现", ["Junior Director", "Agus Widodo", "首富"]),
    ("钩子设计", "未完待续", ["Download and watch more", "CTA", "下载页"]),
    ("叙事道具", "豪车", ["豪车", "车", "car"]),
    ("叙事道具", "清洁工具", ["清洁", "收拾", "cleaner"]),
    ("叙事道具", "签字文件", ["签", "tanda"]),
    ("叙事道具", "金项链", ["金项链", "kalung emas", "necklace"]),
    ("叙事道具", "家族信物", ["信物", "token"]),
    ("叙事道具", "工资/月薪", ["一个月工资", "gaji", "monthly salary"]),
    ("叙事道具", "家族身份称号", ["Widodo", "Junior Director", "首富"]),
    ("叙事道具", "下载页", ["Download", "MaxReels", "Google Play"]),
    ("关系设定", "母女关系", ["母女", "女儿", "Siti", "daughter"]),
    ("关系设定", "夫妻压迫关系", ["丈夫", "husband", "四年"]),
    ("关系设定", "婆媳压迫关系", ["婆家", "mother-in-law"]),
    ("关系设定", "情敌关系", ["Dewi", "情敌"]),
    ("关系设定", "雇佣/服务关系", ["清洁工", "服务", "cleaner"]),
    ("关系设定", "富人压迫穷人", ["富", "穷", "清洁工", "low-status"]),
    ("关系设定", "家族寻找线", ["Widodo", "寻找", "信物"]),
    ("画面表现", "烧录字幕驱动", ["烧录字幕", "visible subtitle", "OCR"]),
    ("画面表现", "人物近景对峙", ["近景", "争吵", "close-up"]),
    ("画面表现", "公开羞辱", ["公开羞辱", "publicly humiliated"]),
    ("画面表现", "家庭室内争执", ["家庭室内", "domestic confrontation"]),
    ("画面表现", "车辆冲突", ["车", "vehicle", "car"]),
    ("画面表现", "下跪动作", ["下跪", "kneel", "sujud"]),
    ("画面表现", "封锁现场", ["不要让任何人逃走", "lockdown", "escape"]),
    ("画面表现", "下载页收口", ["下载页", "Download", "CTA"]),
    ("风险标签", "家庭暴力风险", ["家庭暴力", "打", "mukul"]),
    ("风险标签", "儿童伤害风险", ["Siti 从上面", "孩子受伤", "child injury"]),
    ("风险标签", "人格贬低风险", ["像宠物狗", "没用", "dog", "useless"]),
    ("风险标签", "残障羞辱风险", ["哑巴", "mute"]),
    ("风险标签", "强制下跪风险", ["下跪", "kneel", "sujud"]),
    ("风险标签", "贫富羞辱风险", ["贫富", "清洁工", "穷"]),
    ("风险标签", "平台审核风险", ["风险", "moderation", "平台"]),
    ("投流价值", "前3秒强钩子", ["00:00", "第一帧", "开场"]),
    ("投流价值", "前5秒亲子危机强", ["00:04", "不要乱碰我的孩子"]),
    ("投流价值", "情绪浓度高", ["情绪", "羞辱", "危机"]),
    ("投流价值", "冲突易懂", ["简单", "快速理解", "easy to read"]),
    ("投流价值", "爽点延后", ["未展示", "withholds", "CTA"]),
    ("投流价值", "关键词重复有效", ["关键词重复", "Siti", "Dewi", "Widodo"]),
    ("投流价值", "下载导流强", ["MaxReels", "Download and watch more"]),
    ("优化方向", "明确人物关系", ["明确", "关系", "Define"]),
    ("优化方向", "补足事故因果", ["因果", "车损动作", "Clarify"]),
    ("优化方向", "弱化羞辱台词", ["弱化", "像狗一样", "dehumanizing"]),
    ("优化方向", "强化反转台词", ["更强钩子", "cliffhanger"]),
    ("优化方向", "提前埋身份线", ["提前", "seed", "埋"]),
    ("优化方向", "保留替代受辱结构", ["保留", "替她", "kneel instead"]),
]


def ensure_dirs():
    os.makedirs(ASSET_DIR, exist_ok=True)
    os.makedirs(SERIES_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH):
        save_db({"assets": [], "series": []})


def load_db():
    ensure_dirs()
    with DB_LOCK:
        with open(DB_PATH, "r", encoding="utf-8-sig") as f:
            raw = f.read()
        try:
            db = json.loads(raw or "{}")
        except json.JSONDecodeError:
            cleaned = (raw or "").lstrip("\ufeff").strip()
            decoder = json.JSONDecoder()
            db, end = decoder.raw_decode(cleaned)
            if cleaned[end:].strip():
                backup_dir = os.path.join(DATA_DIR, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup = os.path.join(backup_dir, f"tag_library_auto_repair_{time.strftime('%Y%m%d-%H%M%S')}.json")
                shutil.copy2(DB_PATH, backup)
                save_db(db)
        db.setdefault("assets", [])
        db.setdefault("series", [])
        return db


def save_db(db):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp_path = DB_PATH + ".tmp"
    with DB_LOCK:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DB_PATH)



def confirmed_asset_ids(db=None):
    try:
        db = db or load_db()
        return {asset.get("id") for asset in db.get("assets", []) if asset.get("confirmed")}
    except Exception:
        return set()


def mark_asset_tasks_confirmed(asset_id):
    if not asset_id:
        return
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    with TASK_LOCK:
        for task in TASKS.values():
            if task.get("assetId") == asset_id:
                task.update({
                    "status": "已入库",
                    "stage": "已确认入库",
                    "progress": 100,
                    "error": "",
                    "updatedAt": now,
                })


def task_snapshot():
    confirmed_ids = confirmed_asset_ids()
    with TASK_LOCK:
        items = [dict(task) for task in TASKS.values() if task.get("assetId") not in confirmed_ids and task.get("status") != "已入库"]
    items.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return items


def update_task(task_id, **changes):
    with TASK_LOCK:
        task = TASKS.get(task_id)
        if not task:
            return None
        task.update(changes)
        task["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
        return dict(task)


def create_pipeline_task(asset, api_key=""):
    task_id = f"task-{asset.get('id') or int(time.time() * 1000)}"
    task = {
        "id": task_id,
        "assetId": asset.get("id"),
        "title": asset.get("title") or asset.get("sourceName") or "未命名素材",
        "status": "排队中",
        "stage": "已加入任务队列",
        "progress": 3,
        "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": "",
    }
    with TASK_LOCK:
        TASKS[task_id] = task
    worker = threading.Thread(target=run_full_pipeline_task, args=(task_id, asset.get("id"), api_key), daemon=True)
    worker.start()
    return dict(task)


def update_asset_record(asset_id, updater):
    db = load_db()
    for asset in db.get("assets", []):
        if asset.get("id") == asset_id:
            updater(asset)
            asset["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_db(db)
            return asset
    raise ValueError("素材不存在。")


def get_asset_record(asset_id):
    db = load_db()
    for asset in db.get("assets", []):
        if asset.get("id") == asset_id:
            return db, asset
    raise ValueError("素材不存在。")


def run_full_pipeline_task(task_id, asset_id, api_key=""):
    try:
        update_task(task_id, status="处理中", stage="解析抽帧拆音频", progress=8)
        db, asset = get_asset_record(asset_id)
        analysis_dir = asset.get("analysisDir")
        skill_result = run_skill(asset.get("videoPath", ""), analysis_dir)
        storyboard_path, storyboard_warning = ensure_storyboard_from_frames(analysis_dir)
        audio_path, audio_warning = ensure_ai_audio({"videoPath": asset.get("videoPath"), "analysisDir": analysis_dir})
        warnings = [item for item in [storyboard_warning, audio_warning] if item]
        if warnings:
            skill_result.setdefault("warnings", []).extend(warnings)
        if not skill_result.get("ok"):
            raise ValueError("解析抽帧拆音频失败，请检查视频文件或 ffmpeg 环境。")
        def after_prep(row):
            row["skillResult"] = skill_result
            row["audioPath"] = audio_path
            row["storyboardPath"] = storyboard_path
            row["status"] = "解析完成，正在转写字幕"
            write_artifact_report(row, analysis_dir, skill_result)
            row["artifacts"] = collect_artifacts(row)
        asset = update_asset_record(asset_id, after_prep)

        update_task(task_id, stage="转写并翻译字幕", progress=35)
        transcript_path = transcribe_asset_local_asr(asset, "auto", "", api_key)
        def after_transcribe(row):
            row["transcriptPath"] = transcript_path
            row["transcriptMethod"] = "本地ASR"
            row["transcriptLanguage"] = "auto"
            row["status"] = "字幕转写完成，正在 AI 拉片"
            row["artifacts"] = collect_artifacts(row)
        asset = update_asset_record(asset_id, after_transcribe)

        update_task(task_id, stage="AI 拉片生成报告", progress=62)
        report_path = generate_ai_report(asset, api_key)
        def after_report(row):
            row["sourceReportPath"] = report_path
            row["status"] = "双语报告已生成，正在自动打标"
            row["artifacts"] = collect_artifacts(row)
        asset = update_asset_record(asset_id, after_report)

        update_task(task_id, stage="自动打标", progress=82)
        with open(report_path, "r", encoding="utf-8-sig") as f:
            report_text = f.read()
        tags, evidence, summary, ai_definitions = ai_tag_report(report_text, merged_schema(), api_key)
        merge_ai_tag_definitions(tags, ai_definitions)
        def after_tag(row):
            row["tags"] = tags
            row["autoTagSummary"] = summary
            row["sourceReportPath"] = report_path
            row["autoTagEvidence"] = evidence
            row["status"] = "自动打标完成，待人工确认"
            row["artifacts"] = collect_artifacts(row)
        update_asset_record(asset_id, after_tag)
        update_task(task_id, status="完成", stage="全流程完成，待人工确认", progress=100, error="")
    except Exception as exc:
        message = str(exc) or type(exc).__name__
        update_task(task_id, status="失败", stage="流程中断", progress=100, error=message)
        try:
            def after_error(row):
                row["status"] = f"拉片任务失败：{message}"
                row["taskError"] = message
                row["artifacts"] = collect_artifacts(row)
            update_asset_record(asset_id, after_error)
        except Exception:
            pass
        print("pipeline task failed", task_id, traceback.format_exc())
def send_json(handler, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def normalize_category(category):
    raw = str(category or "").strip()
    return CATEGORY_ALIASES.get(raw, raw)

def hidden_tags_for(db, category):
    hidden = db.get("hiddenTags", {}) or {}
    return {str(tag).strip() for tag in (hidden.get(category, []) or [])}


def add_graveyard_entry(db, entry):
    graveyard = db.setdefault("tagGraveyard", [])
    entry = dict(entry)
    entry["id"] = entry.get("id") or f"grave-{int(time.time() * 1000)}-{len(graveyard) + 1}"
    entry["deletedAt"] = entry.get("deletedAt") or time.strftime("%Y-%m-%d %H:%M:%S")
    graveyard.insert(0, entry)


def tag_graveyard(db=None):
    if db is None:
        db = load_db()
    return db.get("tagGraveyard", []) or []


def stable_tag_id(kind, *parts):
    raw = "|".join(str(part or "").strip() for part in (kind, *parts))
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    prefix = "cat" if kind == "category" else "tag"
    return f"{prefix}_{digest}"


def ensure_tag_localization(db=None, save=False):
    if db is None:
        db = load_db()
    loc = db.setdefault("tagLocalization", {})
    categories_loc = loc.setdefault("categories", {})
    tags_loc = loc.setdefault("tags", {})
    schema = merged_schema(db)
    tag_defs = tag_definitions(db)
    category_defs = category_definitions(db)
    changed = False
    for category, tags in schema.items():
        item = categories_loc.setdefault(category, {})
        if not item.get("id"):
            item["id"] = stable_tag_id("category", category)
            changed = True
        names = item.setdefault("names", {})
        if not names.get("zh"):
            names["zh"] = category
            changed = True
        defs = item.setdefault("definitions", {})
        zh_def = category_defs.get(category, "")
        if zh_def and not defs.get("zh"):
            defs["zh"] = zh_def
            changed = True
        tag_bucket = tags_loc.setdefault(category, {})
        all_tags = set(tags or [])
        for values in (db.get("levelTags", {}) or {}).get(category, {}).values():
            all_tags.update(str(value or "").strip() for value in values or [] if str(value or "").strip())
        all_tags.update((tag_defs.get(category, {}) or {}).keys())
        for tag in sorted(all_tags):
            if not tag:
                continue
            tag_item = tag_bucket.setdefault(tag, {})
            if not tag_item.get("id"):
                tag_item["id"] = stable_tag_id("tag", category, tag)
                changed = True
            tag_names = tag_item.setdefault("names", {})
            if not tag_names.get("zh"):
                tag_names["zh"] = tag
                changed = True
            tag_def_bucket = tag_item.setdefault("definitions", {})
            zh_tag_def = (tag_defs.get(category, {}) or {}).get(tag, "")
            if zh_tag_def and not tag_def_bucket.get("zh"):
                tag_def_bucket["zh"] = zh_tag_def
                changed = True
    if changed and save:
        save_db(db)
    return loc


def tag_localization(db=None):
    if db is None:
        db = load_db()
    return ensure_tag_localization(db, save=True)


def set_tag_localization(kind, category, tag="", locale="en", name="", definition=""):
    locale = str(locale or "en").strip() or "en"
    if locale not in {"zh", "en"}:
        raise ValueError("暂时只支持中文和英文。")
    category = normalize_category(category)
    tag = normalize_tag(tag) if tag else ""
    name = str(name or "").strip()
    definition = str(definition or "").strip()
    if kind == "category" and not category:
        raise ValueError("请填写一级标签。")
    if kind == "tag" and (not category or not tag):
        raise ValueError("请填写一级标签和子标签。")
    db = load_db()
    ensure_tag_localization(db)
    loc = db.setdefault("tagLocalization", {})
    if kind == "category":
        item = loc.setdefault("categories", {}).setdefault(category, {})
        item.setdefault("id", stable_tag_id("category", category))
        item.setdefault("names", {}).setdefault("zh", category)
        if name:
            item.setdefault("names", {})[locale] = name
        else:
            item.setdefault("names", {}).pop(locale, None)
        if definition:
            item.setdefault("definitions", {})[locale] = definition
        else:
            item.setdefault("definitions", {}).pop(locale, None)
        if locale == "zh":
            db.setdefault("categoryDefinitions", {})[category] = definition
    elif kind == "tag":
        item = loc.setdefault("tags", {}).setdefault(category, {}).setdefault(tag, {})
        item.setdefault("id", stable_tag_id("tag", category, tag))
        item.setdefault("names", {}).setdefault("zh", tag)
        if name:
            item.setdefault("names", {})[locale] = name
        else:
            item.setdefault("names", {}).pop(locale, None)
        if definition:
            item.setdefault("definitions", {})[locale] = definition
        else:
            item.setdefault("definitions", {}).pop(locale, None)
        if locale == "zh":
            db.setdefault("tagDefinitions", {}).setdefault(category, {})[tag] = definition
    else:
        raise ValueError("未知本地化对象。")
    save_db(db)
    return db



def apply_category_order(db, schema):
    order = [str(item).strip() for item in (db.get("categoryOrder", []) or []) if str(item).strip()]
    ordered = {}
    for category in order:
        if category in schema and category not in ordered:
            ordered[category] = schema[category]
    for category, tags in schema.items():
        if category not in ordered:
            ordered[category] = tags
    return ordered


def set_category_order(order):
    db = load_db()
    schema = merged_schema(db, apply_order=False)
    clean = []
    for item in order or []:
        category = str(item or "").strip()
        if category in schema and category not in clean:
            clean.append(category)
    for category in schema:
        if category not in clean:
            clean.append(category)
    db["categoryOrder"] = clean
    save_db(db)
    return db
def merged_schema(db=None, apply_order=True):
    if db is None:
        db = load_db()
    hidden_categories = {str(category).strip() for category in db.get("hiddenCategories", []) or []}
    hidden_tags = db.get("hiddenTags", {}) or {}
    schema = {}
    for category, tags in TAG_SCHEMA.items():
        if category in hidden_categories:
            continue
        blocked = {str(tag).strip() for tag in (hidden_tags.get(category, []) or [])}
        schema[category] = [tag for tag in tags if tag not in blocked]
    custom = db.get("customSchema", {}) or {}
    for category, tags in custom.items():
        category = str(category).strip()
        if not category:
            continue
        schema.setdefault(category, [])
        blocked = hidden_tags_for(db, category)
        for tag in tags or []:
            tag = str(tag).strip()
            if tag and tag not in blocked and tag not in schema[category]:
                schema[category].append(tag)
    return apply_category_order(db, schema) if apply_order else schema

def tag_definitions(db=None):
    if db is None:
        db = load_db()
    schema = merged_schema(db)
    stored = db.get("tagDefinitions", {}) or {}
    level_tags = db.get("levelTags", {}) or {}
    definitions = {}
    for category, tags in schema.items():
        stored_category = stored.get(category, {}) or {}
        definitions[category] = {}
        for tag in tags:
            definitions[category][tag] = str(stored_category.get(tag, "")).strip()
        for values in (level_tags.get(category, {}) or {}).values():
            for tag in values or []:
                tag = str(tag or "").strip()
                if tag and tag not in definitions[category]:
                    definitions[category][tag] = str(stored_category.get(tag, "")).strip()
        for tag, definition in stored_category.items():
            tag = str(tag or "").strip()
            if tag and definition and tag not in definitions[category]:
                definitions[category][tag] = str(definition or "").strip()
    return definitions

def category_definitions(db=None):
    if db is None:
        db = load_db()
    schema = merged_schema(db)
    stored = db.get("categoryDefinitions", {}) or {}
    return {category: str(stored.get(category, "")).strip() for category in schema}


def detailed_schema(db=None):
    schema = merged_schema(db)
    definitions = tag_definitions(db)
    return {
        category: [
            {"tag": tag, "definition": definitions.get(category, {}).get(tag, "")}
            for tag in tags
        ]
        for category, tags in schema.items()
    }


def tag_context(db=None):
    if db is None:
        db = load_db()
    return {
        "categoryDefinitions": category_definitions(db),
        "tagLibrary": detailed_schema(db),
        "localizedTagLibrary": tag_localization(db),
        "tagGraveyard": tag_graveyard(db),
    }


def add_schema_tag(category, tag="", definition="", level=1):
    category = normalize_category(category)
    tag = normalize_tag(tag)
    definition = str(definition or "").strip()
    try:
        level = min(max(int(level or 1), 1), 5)
    except Exception:
        level = 1
    if not category:
        raise ValueError("请填写一级标签。")
    db = load_db()
    hidden = db.setdefault("hiddenCategories", [])
    if category in hidden:
        db["hiddenCategories"] = [item for item in hidden if item != category]
    hidden_tags = db.setdefault("hiddenTags", {})
    custom = db.setdefault("customSchema", {})
    custom.setdefault(category, [])
    if tag:
        if tag in hidden_tags.get(category, []):
            hidden_tags[category] = [item for item in hidden_tags.get(category, []) if item != tag]
            if not hidden_tags[category]:
                del hidden_tags[category]
        if level == 1 and tag not in custom[category] and tag not in TAG_SCHEMA.get(category, []):
            custom[category].append(tag)
        level_tags = db.setdefault("levelTags", {})
        level_tags.setdefault(category, {})
        bucket = level_tags[category].setdefault(str(level), [])
        if tag not in bucket:
            bucket.append(tag)
        levels = db.setdefault("categoryLevels", {})
        levels[category] = max(category_level_count(db, category), level)
        defs = db.setdefault("tagDefinitions", {})
        defs.setdefault(category, {})
        if definition or tag not in defs[category]:
            defs[category][tag] = definition
    save_db(db)
    return db

def set_tag_definition(category, tag, definition, level=1):
    category = normalize_category(category)
    tag = str(tag or "").strip()
    definition = str(definition or "").strip()
    try:
        level = min(max(int(level or 1), 1), 5)
    except Exception:
        level = 1
    if not category or not tag:
        raise ValueError("请填写一级标签和子标签。")
    db = add_schema_tag(category, tag, definition, level)
    defs = db.setdefault("tagDefinitions", {})
    defs.setdefault(category, {})
    defs[category][tag] = definition
    save_db(db)
    return db



def set_category_levels(category, levels):
    category = normalize_category(category)
    if not category:
        raise ValueError("请填写一级标签。")
    try:
        levels = int(levels)
    except Exception:
        raise ValueError("层级必须是 1-5 的数字。")
    levels = min(max(levels, 1), 5)
    db = add_schema_tag(category)
    db.setdefault("categoryLevels", {})[category] = levels
    save_db(db)
    return db

def set_category_level_name(category, level, name):
    category = normalize_category(category)
    if not category:
        raise ValueError("请填写一级标签。")
    try:
        level = min(max(int(level or 1), 1), 5)
    except Exception:
        raise ValueError("层级必须是 1-5 的数字。")
    name = str(name or "").strip() or tag_level_label(level)
    db = add_schema_tag(category)
    db.setdefault("categoryLevelNames", {}).setdefault(category, {})[str(level)] = name
    save_db(db)
    return db
def set_category_definition(category, definition):
    category = normalize_category(category)
    definition = str(definition or "").strip()
    if not category:
        raise ValueError("请填写一级标签。")
    db = add_schema_tag(category)
    defs = db.setdefault("categoryDefinitions", {})
    defs[category] = definition
    save_db(db)
    return db


def rename_schema_category(category, new_category):
    category = str(category or "").strip()
    new_category = str(new_category or "").strip()
    if not category or not new_category:
        raise ValueError("请填写原一级标签和新一级标签名。")
    if category == new_category:
        return load_db()
    db = load_db()
    schema = merged_schema(db)
    if category not in schema and category not in (db.get("levelTags", {}) or {}):
        raise ValueError("原一级标签不存在。")

    custom = db.setdefault("customSchema", {})
    hidden_categories = db.setdefault("hiddenCategories", [])
    if category in TAG_SCHEMA and category not in hidden_categories:
        hidden_categories.append(category)

    tags_to_move = list(schema.get(category, []))
    source_custom = custom.pop(category, []) or []
    custom.setdefault(new_category, [])
    for tag in list(tags_to_move) + list(source_custom):
        if tag and tag not in custom[new_category] and tag not in TAG_SCHEMA.get(new_category, []):
            custom[new_category].append(tag)

    level_tags = db.setdefault("levelTags", {})
    source_levels = level_tags.pop(category, {}) or {}
    target_levels = level_tags.setdefault(new_category, {})
    for level, values in source_levels.items():
        bucket = target_levels.setdefault(str(level), [])
        for value in values or []:
            if value and value not in bucket:
                bucket.append(value)

    category_levels = db.setdefault("categoryLevels", {})
    source_level_count = category_levels.pop(category, None)
    if source_level_count is not None:
        try:
            source_level_count = int(source_level_count)
        except Exception:
            source_level_count = 1
        category_levels[new_category] = max(int(category_levels.get(new_category, 1) or 1), source_level_count)

    level_names = db.setdefault("categoryLevelNames", {})
    source_names = level_names.pop(category, {}) or {}
    target_names = level_names.setdefault(new_category, {})
    for level, name in source_names.items():
        if name and not target_names.get(str(level)):
            target_names[str(level)] = name

    tag_defs = db.setdefault("tagDefinitions", {})
    if category in tag_defs:
        target_defs = tag_defs.setdefault(new_category, {})
        for tag, definition in tag_defs.pop(category).items():
            target_defs.setdefault(tag, definition)

    category_defs = db.setdefault("categoryDefinitions", {})
    if category in category_defs:
        definition = category_defs.pop(category)
        if definition or new_category not in category_defs:
            category_defs[new_category] = category_defs.get(new_category) or definition

    loc = db.setdefault("tagLocalization", {})
    categories_loc = loc.setdefault("categories", {})
    if category in categories_loc:
        item = categories_loc.pop(category)
        item.setdefault("names", {})["zh"] = new_category
        categories_loc[new_category] = item
    tags_loc = loc.setdefault("tags", {})
    if category in tags_loc:
        target_tags = tags_loc.setdefault(new_category, {})
        for tag_key, item in tags_loc.pop(category).items():
            target_tags.setdefault(tag_key, item)

    hidden_tags = db.setdefault("hiddenTags", {})
    if category in hidden_tags:
        target_hidden = hidden_tags.setdefault(new_category, [])
        for tag in hidden_tags.pop(category) or []:
            if tag not in target_hidden:
                target_hidden.append(tag)
    if not hidden_tags.get(new_category):
        hidden_tags.pop(new_category, None)

    order = db.setdefault("categoryOrder", [])
    if isinstance(order, list):
        next_order = []
        inserted = False
        for item in order:
            if item == category:
                if new_category not in next_order:
                    next_order.append(new_category)
                inserted = True
            elif item == new_category:
                if new_category not in next_order:
                    next_order.append(new_category)
                inserted = True
            else:
                next_order.append(item)
        if not inserted:
            next_order.append(new_category)
        db["categoryOrder"] = next_order

    for asset in db.get("assets", []):
        tags = asset.get("tags", {}) or {}
        if category in tags:
            moved = tags.pop(category)
            tags.setdefault(new_category, [])
            seen = {tag_path_key(value) for value in tags[new_category]}
            for tag in moved:
                key = tag_path_key(tag)
                if key and key not in seen:
                    tags[new_category].append(tag)
                    seen.add(key)

    for entry in db.get("tagGraveyard", []) or []:
        if entry.get("category") == category:
            entry["category"] = new_category
        if entry.get("mergedIntoCategory") == category:
            entry["mergedIntoCategory"] = new_category

    save_db(db)
    return db

def tag_levels_for(db, category, tag):
    info = hierarchical_schema(db).get(category, {})
    levels = []
    for level, values in (info.get("tagsByLevel", {}) or {}).items():
        if tag in (values or []):
            try:
                levels.append(int(level))
            except Exception:
                pass
    return sorted(set(levels))


def resolve_merge_level(db, category, source_tag, target_tag, preferred_level=1):
    source_levels = tag_levels_for(db, category, source_tag)
    target_levels = tag_levels_for(db, category, target_tag)
    try:
        preferred_level = min(max(int(preferred_level or 1), 1), 5)
    except Exception:
        preferred_level = 1
    if preferred_level in source_levels and preferred_level in target_levels:
        return preferred_level
    common = sorted(set(source_levels) & set(target_levels))
    if common:
        return common[0]
    if not source_levels:
        raise ValueError("源标签不在当前标签体系中，不能合并。")
    if not target_levels:
        raise ValueError("目标标签不在当前标签体系中，不能合并。")
    raise ValueError("源标签和目标标签不在同一层级，不能跨层级合并。")

def merge_schema_tag(category, source_tag, target_tag, level=1, reason=""):
    category = normalize_category(category)
    source_tag = str(source_tag or "").strip()
    target_tag = str(target_tag or "").strip()
    if not category or not source_tag or not target_tag:
        raise ValueError("请选择一级标签、源标签和目标标签。")
    if source_tag == target_tag:
        raise ValueError("源标签和目标标签不能相同。")
    reason = str(reason or "").strip()
    db = load_db()
    level = resolve_merge_level(db, category, source_tag, target_tag, level)
    definitions_before = tag_definitions(db)
    source_definition = definitions_before.get(category, {}).get(source_tag, "")
    if not source_definition:
        for def_key, def_value in (definitions_before.get(category, {}) or {}).items():
            path = split_tag_path(def_key)
            if len(path) >= level and path[level - 1] == source_tag:
                source_definition = def_value or ""
                break
    level_tags = db.setdefault("levelTags", {})
    bucket = level_tags.setdefault(category, {}).setdefault(str(level), [])
    bucket[:] = [item for item in bucket if item != source_tag]
    if target_tag not in bucket:
        bucket.append(target_tag)

    custom = db.setdefault("customSchema", {})
    custom.setdefault(category, [])
    hidden_tags = db.setdefault("hiddenTags", {})
    blocked_defaults = hidden_tags.setdefault(category, [])
    next_schema_tags = []
    seen_schema = set()
    for value in list(custom.get(category, [])) + list(TAG_SCHEMA.get(category, [])):
        original_key = tag_path_key(split_tag_path(value))
        path = split_tag_path(value)
        if len(path) >= level and path[level - 1] == source_tag:
            if original_key in TAG_SCHEMA.get(category, []) and original_key not in blocked_defaults:
                blocked_defaults.append(original_key)
            path[level - 1] = target_tag
        key = tag_path_key(path)
        if key and key not in seen_schema and key not in TAG_SCHEMA.get(category, []):
            next_schema_tags.append(key)
            seen_schema.add(key)
    custom[category] = next_schema_tags
    if not hidden_tags.get(category):
        hidden_tags.pop(category, None)

    defs = db.setdefault("tagDefinitions", {})
    if category in defs:
        category_defs = defs.setdefault(category, {})
        for def_key in list(category_defs.keys()):
            path = split_tag_path(def_key)
            if def_key == source_tag or (len(path) >= level and path[level - 1] == source_tag):
                del category_defs[def_key]

    for asset in db.get("assets", []):
        tags = asset.get("tags", {}) or {}
        if category in tags:
            next_values = []
            seen = set()
            for value in tags.get(category, []) or []:
                path = split_tag_path(value)
                if len(path) >= level and path[level - 1] == source_tag:
                    path[level - 1] = target_tag
                key = tag_path_key(path)
                if key and key not in seen:
                    next_values.append(path)
                    seen.add(key)
            if next_values:
                tags[category] = next_values
            else:
                tags.pop(category, None)
        evidence = asset.get("autoTagEvidence")
        if isinstance(evidence, dict):
            next_evidence = {}
            for key, phrases in evidence.items():
                parts = str(key or "").split("/")
                if parts and normalize_category(parts[0]) == category and len(parts) > level and parts[level] == source_tag:
                    parts[0] = category
                    parts[level] = target_tag
                    key = "/".join(parts)
                if key in next_evidence:
                    for phrase in phrases or []:
                        if phrase not in next_evidence[key]:
                            next_evidence[key].append(phrase)
                else:
                    next_evidence[key] = phrases
            asset["autoTagEvidence"] = next_evidence

    add_graveyard_entry(db, {
        "type": "tag",
        "category": category,
        "tag": source_tag,
        "level": level,
        "definition": source_definition,
        "reason": reason or f"合并到「{target_tag}」",
        "mergedInto": target_tag,
        "mergedIntoCategory": category,
    })
    save_db(db)
    return db


def transfer_schema_tag(source_category, source_tag, source_level, target_category, target_level):
    source_category = normalize_category(source_category)
    target_category = normalize_category(target_category)
    source_tag = str(source_tag or "").strip()
    try:
        source_level = min(max(int(source_level or 1), 1), 5)
    except Exception:
        source_level = 1
    try:
        target_level = min(max(int(target_level or 1), 1), 5)
    except Exception:
        target_level = 1
    if not source_category or not target_category or not source_tag:
        raise ValueError("请选择源一级标签、子标签和目标位置。")
    db = load_db()
    schema = merged_schema(db)
    if target_category not in schema and target_category not in db.get("levelTags", {}):
        raise ValueError("目标一级标签不存在。")
    actual_levels = tag_levels_for(db, source_category, source_tag)
    if source_level not in actual_levels:
        if len(actual_levels) == 1:
            source_level = actual_levels[0]
        else:
            raise ValueError("源标签不在当前层级，无法转移。")
    level_tags = db.setdefault("levelTags", {})
    source_bucket = level_tags.setdefault(source_category, {}).setdefault(str(source_level), [])
    if source_tag not in source_bucket:
        source_bucket.append(source_tag)
    level_tags[source_category][str(source_level)] = [item for item in source_bucket if item != source_tag]
    target_bucket = level_tags.setdefault(target_category, {}).setdefault(str(target_level), [])
    if source_tag not in target_bucket:
        target_bucket.append(source_tag)
    db.setdefault("categoryLevels", {})[target_category] = max(category_level_count(db, target_category), target_level)

    hidden_tags = db.setdefault("hiddenTags", {})
    custom = db.setdefault("customSchema", {})
    custom.setdefault(source_category, [])
    for value in list(custom.get(source_category, []) or []):
        path = split_tag_path(value)
        if value == source_tag or (len(path) >= source_level and path[source_level - 1] == source_tag):
            custom[source_category] = [item for item in custom.get(source_category, []) if item != value]
    blocked_defaults = hidden_tags.setdefault(source_category, [])
    for value in TAG_SCHEMA.get(source_category, []) or []:
        path = split_tag_path(value)
        if len(path) >= source_level and path[source_level - 1] == source_tag and value not in blocked_defaults:
            blocked_defaults.append(value)
    if not hidden_tags.get(source_category):
        hidden_tags.pop(source_category, None)

    defs = db.setdefault("tagDefinitions", {})
    source_defs = defs.setdefault(source_category, {})
    target_defs = defs.setdefault(target_category, {})
    moved_definition = source_defs.pop(source_tag, "")
    for def_key in list(source_defs.keys()):
        path = split_tag_path(def_key)
        if len(path) >= source_level and path[source_level - 1] == source_tag:
            del source_defs[def_key]
    if moved_definition and not target_defs.get(source_tag):
        target_defs[source_tag] = moved_definition

    save_db(db)
    return db
def rename_schema_tag(category, tag, new_tag, level=1):
    category = normalize_category(category)
    tag = str(tag or "").strip()
    new_tag = str(new_tag or "").strip()
    try:
        level = min(max(int(level or 1), 1), 5)
    except Exception:
        level = 1
    if not category or not tag or not new_tag:
        raise ValueError("请填写一级标签、原子标签和新子标签名。")
    if tag == new_tag:
        return load_db()
    db = load_db()
    actual_levels = tag_levels_for(db, category, tag)
    if level not in actual_levels:
        if len(actual_levels) == 1:
            level = actual_levels[0]
        elif actual_levels:
            readable = "、".join(category_level_label(db, category, item) for item in actual_levels)
            raise ValueError(f"原标签存在于多个层级（{readable}），请刷新后重新选择。")
        else:
            label = category_level_label(db, category, level)
            raise ValueError(f"原{label}标签不存在。")
    target_levels = tag_levels_for(db, category, new_tag)
    if level in target_levels:
        label = category_level_label(db, category, level)
        raise ValueError(f"新{label}标签名已存在。")
    level_tags = db.setdefault("levelTags", {}).setdefault(category, {})
    bucket = level_tags.setdefault(str(level), [])
    if tag in bucket:
        level_tags[str(level)] = [new_tag if item == tag else item for item in bucket]
    elif new_tag not in bucket:
        bucket.append(new_tag)

    custom = db.setdefault("customSchema", {})
    custom.setdefault(category, [])
    hidden_tags = db.setdefault("hiddenTags", {})
    if level == 1:
        if tag in custom.get(category, []):
            custom[category] = [item for item in custom.get(category, []) if item != tag]
        elif tag in TAG_SCHEMA.get(category, []):
            hidden_tags.setdefault(category, [])
            if tag not in hidden_tags[category]:
                hidden_tags[category].append(tag)
        if new_tag in hidden_tags.get(category, []):
            hidden_tags[category] = [item for item in hidden_tags.get(category, []) if item != new_tag]
            if not hidden_tags[category]:
                del hidden_tags[category]
        if new_tag not in TAG_SCHEMA.get(category, []) and new_tag not in custom[category]:
            custom[category].append(new_tag)

    defs = db.setdefault("tagDefinitions", {}).setdefault(category, {})
    if tag in defs and new_tag not in defs:
        defs[new_tag] = defs.pop(tag)
    elif tag in defs:
        defs.pop(tag, None)
    for def_key in list(defs.keys()):
        path = split_tag_path(def_key)
        if len(path) >= level and path[level - 1] == tag:
            next_path = list(path)
            next_path[level - 1] = new_tag
            next_key = tag_path_key(next_path)
            defs.setdefault(next_key, defs.pop(def_key))

    for value in list(custom.get(category, []) or []):
        path = split_tag_path(value)
        if len(path) >= level and path[level - 1] == tag:
            next_path = list(path)
            next_path[level - 1] = new_tag
            next_value = tag_path_key(next_path)
            custom[category] = [item for item in custom[category] if item != value]
            if next_value and next_value not in custom[category] and next_value not in TAG_SCHEMA.get(category, []):
                custom[category].append(next_value)

    for asset in db.get("assets", []):
        values = (asset.get("tags", {}) or {}).get(category, [])
        if not values:
            continue
        next_values = []
        changed = False
        for item in values:
            path = split_tag_path(item)
            if len(path) >= level and path[level - 1] == tag:
                path[level - 1] = new_tag
                changed = True
            next_values.append(path if isinstance(item, list) else tag_path_key(path))
        if changed:
            asset.setdefault("tags", {})[category] = []
            seen = set()
            for item in next_values:
                key = tag_path_key(item)
                if key and key not in seen:
                    seen.add(key)
                    asset["tags"][category].append(item)

    loc_tags = db.setdefault("tagLocalization", {}).setdefault("tags", {}).setdefault(category, {})
    if tag in loc_tags:
        item = loc_tags.pop(tag)
        item.setdefault("names", {})["zh"] = new_tag
        loc_tags[new_tag] = item

    for entry in db.get("tagGraveyard", []) or []:
        if entry.get("category") == category and entry.get("tag") == tag:
            entry["tag"] = new_tag
    save_db(db)
    return db
def delete_schema_tag(category, tag, reason="", level=1):
    category = normalize_category(category)
    tag = str(tag or "").strip()
    reason = str(reason or "").strip()
    try:
        preferred_level = min(max(int(level or 1), 1), 5)
    except Exception:
        preferred_level = 1
    if not category or not tag:
        raise ValueError("请填写一级标签和子标签。")
    if not reason:
        raise ValueError("请填写删除原因。")
    db = load_db()
    definitions = tag_definitions(db)
    definition = definitions.get(category, {}).get(tag, "")
    level_tags = db.setdefault("levelTags", {}).setdefault(category, {})

    existing_levels = []
    for level_key, values in (level_tags or {}).items():
        if tag in (values or []):
            try:
                existing_levels.append(int(level_key))
            except Exception:
                pass
    if preferred_level in existing_levels:
        levels_to_clean = [preferred_level]
    elif existing_levels:
        levels_to_clean = sorted(set(existing_levels))
    else:
        # The UI may still hold a stale tag after earlier edits. Delete should be idempotent,
        # so scan all possible levels and clear any path/definition residue instead of failing.
        levels_to_clean = list(range(1, 6))

    for actual_level in levels_to_clean:
        bucket = level_tags.setdefault(str(actual_level), [])
        if tag in bucket:
            level_tags[str(actual_level)] = [item for item in bucket if item != tag]

    hidden_tags = db.setdefault("hiddenTags", {})
    custom = db.setdefault("customSchema", {})
    custom.setdefault(category, [])
    next_custom = []
    for value in custom.get(category, []) or []:
        path = split_tag_path(value)
        should_delete = value == tag or any(len(path) >= actual_level and path[actual_level - 1] == tag for actual_level in levels_to_clean)
        if should_delete:
            continue
        next_custom.append(value)
    custom[category] = next_custom

    default_blocked = hidden_tags.setdefault(category, [])
    for value in TAG_SCHEMA.get(category, []) or []:
        path = split_tag_path(value)
        if any(len(path) >= actual_level and path[actual_level - 1] == tag for actual_level in levels_to_clean) and value not in default_blocked:
            default_blocked.append(value)
    if not hidden_tags.get(category):
        hidden_tags.pop(category, None)

    defs = db.setdefault("tagDefinitions", {})
    if category in defs:
        for def_key in list(defs[category].keys()):
            path = split_tag_path(def_key)
            should_delete = def_key == tag or any(len(path) >= actual_level and path[actual_level - 1] == tag for actual_level in levels_to_clean)
            if should_delete:
                del defs[category][def_key]

    for asset in db.get("assets", []):
        tags = asset.get("tags", {}) or {}
        if category in tags:
            next_values = []
            seen = set()
            for value in tags.get(category, []) or []:
                path = split_tag_path(value)
                if any(len(path) >= actual_level and path[actual_level - 1] == tag for actual_level in levels_to_clean):
                    continue
                key = tag_path_key(path)
                if key and key not in seen:
                    next_values.append(path)
                    seen.add(key)
            if next_values:
                tags[category] = next_values
            else:
                del tags[category]
        evidence = asset.get("autoTagEvidence")
        if isinstance(evidence, dict):
            next_evidence = {}
            for key, phrases in evidence.items():
                parts = str(key or "").split("/")
                should_delete = False
                if parts and normalize_category(parts[0]) == category:
                    for actual_level in levels_to_clean:
                        if len(parts) > actual_level and parts[actual_level] == tag:
                            should_delete = True
                            break
                if not should_delete:
                    next_evidence[key] = phrases
            asset["autoTagEvidence"] = next_evidence

    graveyard_level = preferred_level if preferred_level in levels_to_clean else (levels_to_clean[0] if levels_to_clean else preferred_level)
    add_graveyard_entry(db, {
        "type": "tag",
        "category": category,
        "tag": tag,
        "level": graveyard_level,
        "definition": definition,
        "reason": reason,
    })
    save_db(db)
    return db
def move_schema_tag(source_category, target_category, tag):
    source_category = str(source_category or "").strip()
    target_category = str(target_category or "").strip()
    tag = str(tag or "").strip()
    if not source_category or not target_category or not tag:
        raise ValueError("请选择原一级标签、目标一级标签和二级标签。")
    if source_category == target_category:
        raise ValueError("目标一级标签不能和原一级标签相同。")
    db = load_db()
    schema = merged_schema(db)
    if tag not in schema.get(source_category, []):
        raise ValueError("原一级标签下不存在该二级标签。")
    if target_category not in schema:
        raise ValueError("目标一级标签不存在。")

    definitions = tag_definitions(db)
    definition = definitions.get(source_category, {}).get(tag, "")
    custom = db.setdefault("customSchema", {})
    hidden_tags = db.setdefault("hiddenTags", {})

    if tag in custom.get(source_category, []):
        custom[source_category] = [item for item in custom.get(source_category, []) if item != tag]
    elif tag in TAG_SCHEMA.get(source_category, []):
        hidden_tags.setdefault(source_category, [])
        if tag not in hidden_tags[source_category]:
            hidden_tags[source_category].append(tag)

    if tag in hidden_tags.get(target_category, []):
        hidden_tags[target_category] = [item for item in hidden_tags.get(target_category, []) if item != tag]
        if not hidden_tags[target_category]:
            del hidden_tags[target_category]
    custom.setdefault(target_category, [])
    if tag not in TAG_SCHEMA.get(target_category, []) and tag not in custom[target_category]:
        custom[target_category].append(tag)

    defs = db.setdefault("tagDefinitions", {})
    if source_category in defs and tag in defs[source_category]:
        definition = defs[source_category].pop(tag) or definition
    if definition:
        defs.setdefault(target_category, {})
        defs[target_category].setdefault(tag, definition)

    for asset in db.get("assets", []):
        tags = asset.get("tags", {}) or {}
        if tag in tags.get(source_category, []):
            tags[source_category] = [item for item in tags.get(source_category, []) if item != tag]
            if not tags[source_category]:
                del tags[source_category]
            tags.setdefault(target_category, [])
            if tag not in tags[target_category]:
                tags[target_category].append(tag)

    save_db(db)
    return db


def delete_schema_category(category, reason=""):
    category = str(category or "").strip()
    reason = str(reason or "").strip()
    if not category:
        raise ValueError("请填写一级标签。")
    if not reason:
        raise ValueError("请填写删除原因。")
    db = load_db()
    schema_before = merged_schema(db)
    definitions = tag_definitions(db)
    category_tags = list(schema_before.get(category, []))
    custom = db.setdefault("customSchema", {})
    if category in custom:
        del custom[category]
    if category in TAG_SCHEMA:
        hidden = db.setdefault("hiddenCategories", [])
        if category not in hidden:
            hidden.append(category)
    hidden_tags = db.setdefault("hiddenTags", {})
    if category in hidden_tags:
        del hidden_tags[category]
    defs = db.setdefault("tagDefinitions", {})
    if category in defs:
        del defs[category]
    for asset in db.get("assets", []):
        tags = asset.get("tags", {}) or {}
        if category in tags:
            del tags[category]
    add_graveyard_entry(db, {
        "type": "category",
        "category": category,
        "reason": reason,
        "deletedTags": category_tags,
    })
    for tag in category_tags:
        add_graveyard_entry(db, {
            "type": "tag",
            "category": category,
            "tag": tag,
            "definition": definitions.get(category, {}).get(tag, ""),
            "reason": reason,
            "deletedWithCategory": True,
        })
    save_db(db)
    return db


def schema_response(db=None):
    if db is None:
        db = load_db()
    return {
        "schema": merged_schema(db),
        "categoryDefinitions": category_definitions(db),
        "tagDefinitions": tag_definitions(db),
        "schemaDetailed": detailed_schema(db),
        "hierarchicalSchema": hierarchical_schema(db),
        "categoryLevels": db.get("categoryLevels", {}) or {},
        "categoryLevelNames": db.get("categoryLevelNames", {}) or {},
        "categoryOrder": list(merged_schema(db).keys()),
        "tagGraveyard": tag_graveyard(db),
        "tagLocalization": tag_localization(db),
        "synonyms": SYNONYMS,
    }

def fallback_tag_definition(db, category, tag, path, level, path_definition=""):
    level_name = category_level_label(db, category, level)
    path_text = tag_path_key(path)
    if path_definition:
        return f"在「{category}」中作为「{level_name}」标签，表示「{tag}」这一层级特征；该标签来自完整路径「{path_text}」。"
    return f"在「{category}」中作为「{level_name}」标签，用于标记素材里出现的「{tag}」特征。"

def merge_ai_tag_definitions(tags, definitions):
    if not isinstance(definitions, dict):
        definitions = {}
    db = load_db()
    changed = False
    hidden = db.setdefault("hiddenCategories", [])
    custom = db.setdefault("customSchema", {})
    level_tags = db.setdefault("levelTags", {})
    stored_defs = db.setdefault("tagDefinitions", {})
    for raw_category, values in (tags or {}).items():
        original_category = str(raw_category or "").strip()
        category = normalize_category(original_category)
        if not category:
            continue
        if category in hidden:
            db["hiddenCategories"] = [item for item in hidden if item != category]
            hidden = db["hiddenCategories"]
            changed = True
        custom.setdefault(category, [])
        level_tags.setdefault(category, {})
        stored_defs.setdefault(category, {})
        raw_defs = definitions.get(original_category, {}) if original_category else {}
        normalized_defs = definitions.get(category, {}) if category else {}
        category_defs = {}
        if isinstance(raw_defs, dict):
            category_defs.update(raw_defs)
        if isinstance(normalized_defs, dict):
            category_defs.update(normalized_defs)
        for value in values or []:
            path = split_tag_path(value)
            if not path:
                continue
            levels = db.setdefault("categoryLevels", {})
            next_level_count = max(category_level_count(db, category), len(path))
            if levels.get(category) != next_level_count:
                levels[category] = next_level_count
                changed = True
            flat = tag_path_key(path)
            if flat and flat not in TAG_SCHEMA.get(category, []) and flat not in custom[category]:
                custom[category].append(flat)
                changed = True
            for idx, tag in enumerate(path, 1):
                bucket = level_tags[category].setdefault(str(idx), [])
                if tag not in bucket:
                    bucket.append(tag)
                    changed = True
                path_definition = str(category_defs.get(flat, "")).strip()
                definition = str(category_defs.get(tag, "") or path_definition).strip()
                if not definition:
                    definition = fallback_tag_definition(db, category, tag, path, idx, path_definition)
                if definition and stored_defs[category].get(tag) != definition:
                    stored_defs[category][tag] = definition
                    changed = True
    if changed:
        save_db(db)
    return db
def normalize_tag(tag):
    tag = re.sub(r"\s+", "", str(tag).strip())
    return SYNONYMS.get(tag, tag)



def split_tag_path(value):
    if isinstance(value, list):
        parts = value
    else:
        parts = re.split(r"\s*-\s*", str(value or ""))
    clean = []
    for part in parts:
        tag = normalize_tag(part)
        if tag and tag not in clean:
            clean.append(tag)
    return clean[:5]


def tag_path_key(path):
    return "-".join(split_tag_path(path))


def category_level_count(db, category):
    levels = db.get("categoryLevels", {}) if isinstance(db, dict) else {}
    try:
        value = int(levels.get(category, 1))
    except Exception:
        value = 1
    return min(max(value, 1), 5)


def tag_level_label(level):
    labels = {1: "二级", 2: "三级", 3: "四级", 4: "五级", 5: "六级"}
    return labels.get(level, f"{level + 1}级")


def category_level_label(db, category, level):
    names = ((db or {}).get("categoryLevelNames", {}) or {}).get(category, {}) or {}
    return str(names.get(str(level)) or tag_level_label(level)).strip()


def hierarchical_schema(db=None):
    if db is None:
        db = load_db()
    flat = merged_schema(db)
    stored = db.get("levelTags", {}) or {}
    result = {}
    for category, tags in flat.items():
        inferred_levels = max([len(split_tag_path(tag)) for tag in tags] + [1])
        configured = db.get("categoryLevels", {}) if isinstance(db, dict) else {}
        levels = min(max(int(configured.get(category, inferred_levels) or inferred_levels), 1), 5)
        level_tags = {str(i): [] for i in range(1, levels + 1)}
        for tag in tags:
            for idx, part in enumerate(split_tag_path(tag), 1):
                if idx > levels:
                    break
                bucket = level_tags.setdefault(str(idx), [])
                if part and part not in bucket:
                    bucket.append(part)
        for level, values in (stored.get(category, {}) or {}).items():
            try:
                idx = int(level)
            except Exception:
                continue
            if idx < 1 or idx > levels:
                continue
            bucket = level_tags.setdefault(str(idx), [])
            for value in values or []:
                tag = normalize_tag(value)
                if tag and tag not in bucket:
                    bucket.append(tag)
        result[category] = {
            "levels": levels,
            "levelLabels": {str(i): category_level_label(db, category, i) for i in range(1, levels + 1)},
            "tagsByLevel": level_tags,
        }
    return result

def normalize_tags(tags):
    merged = {}
    for category, values in (tags or {}).items():
        category = normalize_category(category)
        if not category:
            continue
        clean = []
        for value in values or []:
            path = split_tag_path(value)
            if not path:
                continue
            key = tag_path_key(path)
            if key and key not in [tag_path_key(item) for item in clean]:
                clean.append(path)
        if clean:
            merged[category] = clean
    return merged


def add_tag(tags, category, tag):
    tag = normalize_tag(tag)
    if not tag:
        return
    tags.setdefault(category, [])
    if tag not in tags[category]:
        tags[category].append(tag)


def auto_tag(text):
    haystack = text.lower()
    tags = {}
    evidence = {}
    for category, tag, keywords in RULES:
        for keyword in keywords:
            if keyword.lower() in haystack:
                add_tag(tags, category, tag)
                evidence.setdefault(f"{category}/{normalize_tag(tag)}", [])
                if keyword not in evidence[f"{category}/{normalize_tag(tag)}"]:
                    evidence[f"{category}/{normalize_tag(tag)}"].append(keyword)
                break

    if "maxreels" in haystack:
        add_tag(tags, "题材", "竖屏短剧")
        add_tag(tags, "投流价值", "下载导流强")
    if "widodo" in haystack:
        add_tag(tags, "核心冲突", "权势身份反转")
        add_tag(tags, "题材", "豪门反转")
    if "siti" in haystack:
        add_tag(tags, "核心冲突", "儿童危机")
        add_tag(tags, "题材", "母女亲情")
    if "dewi" in haystack:
        add_tag(tags, "核心冲突", "情敌替代")
    if "cleaner" in haystack or "清洁工" in haystack:
        add_tag(tags, "人设", "弱势劳动者")
        add_tag(tags, "关系设定", "雇佣/服务关系")

    return normalize_tags(tags), evidence


def summarize_report(text):
    match = re.search(r"## 一句话判断.*?\n\n中文[:：](.*?)(?:\n\nEnglish|\n## )", text, re.S)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines[:3])[:280]


def read_json_file(path, default=None):
    if not path or not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def read_text_file(path, default=""):
    if not path or not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except Exception:
        return default


def fmt_time(seconds):
    try:
        seconds = float(seconds)
    except Exception:
        seconds = 0
    minutes = int(seconds // 60)
    rest = seconds - minutes * 60
    return f"{minutes:02d}:{rest:05.2f}"


def find_analysis_file(analysis_dir, name):
    path = os.path.join(analysis_dir or "", name)
    return path if os.path.exists(path) else ""


def frame_items_from_dir(analysis_dir, limit=24):
    frames_dir = os.path.join(analysis_dir or "", "frames")
    if not os.path.isdir(frames_dir):
        return []
    items = []
    names = sorted(name for name in os.listdir(frames_dir) if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    for pos, name in enumerate(names[:limit], 1):
        match = re.search(r"frame_(\d+)_([0-9]{2})-([0-9]{2})-([0-9]{2})", name)
        if match:
            index = int(match.group(1))
            stamp = f"{match.group(2)}:{match.group(3)}.{match.group(4)}"
        else:
            index = pos
            stamp = ""
        items.append({
            "index": index,
            "stamp": stamp or f"frame {pos}",
            "file": os.path.join(frames_dir, name),
            "source": "frames_dir_fallback",
        })
    return items


def normalized_frame_items(analysis_dir, metadata=None, prep=None, limit=24):
    metadata = metadata or {}
    prep = prep or {}
    frames = metadata.get("frames") or prep.get("frames") or []
    normalized = []
    for pos, item in enumerate(frames[:limit], 1):
        if not isinstance(item, dict):
            continue
        file_path = item.get("file", "")
        if file_path and not os.path.isabs(file_path):
            file_path = os.path.join(analysis_dir, file_path)
        if file_path and os.path.exists(file_path):
            normalized.append({
                "index": item.get("index") or pos,
                "stamp": item.get("stamp") or fmt_time(item.get("timestamp", 0)),
                "file": file_path,
                "source": "metadata",
            })
    if normalized:
        return normalized
    return frame_items_from_dir(analysis_dir, limit=limit)

def ensure_storyboard_from_frames(analysis_dir):
    storyboard_path = find_analysis_file(analysis_dir, "storyboard.jpg")
    if storyboard_path:
        return storyboard_path, ""
    frames = frame_items_from_dir(analysis_dir, limit=24)
    if not frames:
        return "", "未找到可用于生成 storyboard 的抽帧图片。"
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:
        return "", f"缺少 Pillow，无法生成 storyboard：{exc}"
    thumb_w = 240
    thumbs = []
    for item in frames:
        img = Image.open(item["file"]).convert("RGB")
        w, h = img.size
        thumb_h = max(120, round(thumb_w * h / max(w, 1)))
        thumb = img.resize((thumb_w, thumb_h))
        draw = ImageDraw.Draw(thumb)
        label = f"{int(item.get('index') or len(thumbs) + 1):02d}  {item.get('stamp', '')}"
        draw.rectangle((0, 0, min(thumb_w, 148), 28), fill=(0, 0, 0))
        draw.text((8, 6), label, fill=(255, 255, 255))
        thumbs.append(thumb)
    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    max_h = max(t.height for t in thumbs)
    sheet = Image.new("RGB", (cols * thumb_w, rows * max_h), (18, 24, 32))
    for idx, thumb in enumerate(thumbs):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * max_h
        sheet.paste(thumb, (x, y))
    storyboard_path = os.path.join(analysis_dir, "storyboard.jpg")
    sheet.save(storyboard_path, quality=90)
    return storyboard_path, ""

def generate_ai_report_request(asset):
    analysis_dir = asset.get("analysisDir", "")
    if not analysis_dir or not os.path.isdir(analysis_dir):
        raise ValueError("该素材还没有可用的拉片素材包。")
    metadata_path = find_analysis_file(analysis_dir, "metadata.json")
    prep_path = find_analysis_file(analysis_dir, "prep_result.json")
    transcript_path = find_analysis_file(analysis_dir, "transcript.txt")
    transcript_json_path = find_analysis_file(analysis_dir, "transcript.json")
    storyboard_path = find_analysis_file(analysis_dir, "storyboard.jpg")
    metadata = read_json_file(metadata_path, {}) or {}
    prep = read_json_file(prep_path, {}) or {}
    frames = normalized_frame_items(analysis_dir, metadata, prep, limit=24)
    frame_lines = []
    for item in frames[:24]:
        frame_lines.append(f"- {item.get('index')}: {item.get('stamp') or fmt_time(item.get('timestamp', 0))} `{item.get('file', '')}`")
    request_path = os.path.join(analysis_dir, "AI_report_request.md")
    lines = [
        f"# {asset.get('title') or asset.get('sourceName') or asset.get('id')} AI大模型拉片任务包",
        "",
        "这不是双语拉片报告，只是给大模型分析用的任务包。正式报告必须由大模型读取抽帧和转写后生成，并命名为 `AI_video_analysis_bilingual.md` 或 `AI_video_analysis_visual_bilingual.md`。",
        "",
        "## 素材路径",
        "",
        f"- 原视频：`{asset.get('videoPath', '')}`",
        f"- 分析目录：`{analysis_dir}`",
        f"- storyboard：`{storyboard_path}`",
        f"- metadata：`{metadata_path}`",
        f"- prep_result：`{prep_path}`",
        f"- transcript.txt：`{transcript_path or '无'}`",
        f"- transcript.json：`{transcript_json_path or '无'}`",
        "",
        "## 代表帧",
        "",
        *(frame_lines or ["- 未找到代表帧"]),
        "",
        "## 给大模型的任务",
        "",
        "请严格参照 Video AI Analysis Skill V1，根据 storyboard、代表帧、metadata、prep_result、音频大模型转录与画面字幕 OCR，生成一份中文优先、中英双语 Markdown 拉片报告。",
        "",
        "报告必须包含：基础信息、一句话判断、关键叙事结构、可学习点、完整转写/字幕表、分段拉片、关键新增发现、画面与声音协同、AI生成特征、风险与审核点、改稿建议、可复用优化版梗概、发布判断。",
        "",
        "要求：不要写占位模板；必须基于图片、音频转录和画面 OCR 做具体判断；如果转写不可靠，要明确说明并结合画面分析；报告需要能用于后续自动打标。",
    ]
    with open(request_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return request_path

def current_prompts(db=None):
    if db is None:
        db = load_db()
    custom = db.get("prompts", {}) or {}
    prompts = dict(DEFAULT_PROMPTS)
    for key in DEFAULT_PROMPTS:
        if isinstance(custom.get(key), str) and custom.get(key).strip():
            prompts[key] = custom[key]
    report_prompt = prompts.get("reportUser", "")
    if "画面烧录字幕/OCR" not in report_prompt and "input_audio" not in report_prompt:
        prompts["reportUser"] = prompts.get("reportUser", "") + "\n\n补充要求：正式拉片必须基于已生成的 transcript.txt/json 字幕进行分析，并从 storyboard/代表帧中 OCR 画面烧录字幕、片头字、CTA 和所有可见文字；没有音频转写产物时不能生成报告。"
    prompt_text = prompts.get("tagUser", "")
    if "tagDefinitions" not in prompt_text:
        prompts["tagUser"] = prompts.get("tagUser", "") + "\n\n补充要求：标签体系输入包含 hierarchicalTagLibrary，按一级标签管理多层子标签池；自动打标输出 tags 时，每条标签必须是完整路径数组，且不同层级之间可以自由组合；如果新增任意层级子标签，必须在 tagDefinitions 中给出定义。"
    if "标签墓地" not in prompts.get("tagUser", ""):
        prompts["tagUser"] = prompts.get("tagUser", "") + "\n补充要求：schema_json 同时包含 tagLibrary 和 tagGraveyard；自动打标时必须参考标签墓地，不要生成墓地中已有或高度相似的标签。"
    if "完整路径数组" not in prompts.get("tagUser", ""):
        prompts["tagUser"] = prompts.get("tagUser", "") + "\n补充要求：当前标签体系支持多层子标签。tags 必须输出为 {一级标签: [[二级标签, 三级标签, 四级标签]]}，每条标签是完整路径数组；每个一级标签最多 5 层子标签，层级之间不是强绑定，可以自由组合；不要再输出单个 A-B-C 字符串。"
    if "每个路径节点" not in prompts.get("tagUser", ""):
        prompts["tagUser"] = prompts.get("tagUser", "") + "\n补充要求：tagDefinitions 必须覆盖 tags 中出现的每个路径节点，而不只是整条路径。格式为 {一级标签: {路径节点标签: 定义, 完整路径标签: 定义}}；如果新增任意子层级标签，必须给该子标签单独定义。"
    return prompts


def save_prompts(next_prompts):
    db = load_db()
    prompts = db.setdefault("prompts", {})
    for key in DEFAULT_PROMPTS:
        value = str(next_prompts.get(key, "")).strip()
        prompts[key] = value or DEFAULT_PROMPTS[key]
    save_db(db)
    return current_prompts(db)


def render_prompt_template(template, values):
    out = str(template or "")
    for key, value in values.items():
        text_value = str(value)
        out = out.replace("{{" + key + "}}", text_value)
        out = out.replace("{" + key + "}", text_value)
    return out

def parse_first_json_value(text):
    raw = str(text or "").lstrip("\ufeff").strip()
    if not raw:
        raise json.JSONDecodeError("empty response", "", 0)
    decoder = json.JSONDecoder()
    candidates = []
    for match in re.finditer(r"```(?:json)?\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL):
        block = match.group(1).strip()
        if block:
            candidates.append(block)
    candidates.append(raw)
    for candidate in candidates:
        cleaned = candidate.strip()
        if not cleaned:
            continue
        starts = []
        first_obj = cleaned.find("{")
        first_arr = cleaned.find("[")
        if first_obj == 0 or first_arr == 0:
            starts.append(0)
        for idx, ch in enumerate(cleaned):
            if ch in "[{" and idx not in starts:
                starts.append(idx)
        for start in starts:
            try:
                value, _end = decoder.raw_decode(cleaned[start:])
                return value
            except json.JSONDecodeError:
                continue
    raise json.JSONDecodeError("no valid JSON value found", raw, 0)
def require_api_key(value):
    key = str(value or "").strip()
    if not key:
        raise ValueError("请先填写模型 Key。")
    return key


def call_ai_model(api_key, messages, temperature=0.2, max_tokens=6000):
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        AI_BASE_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"模型接口返回错误 {exc.code}：{body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"模型接口连接失败：{exc.reason}") from exc
    try:
        result = parse_first_json_value(raw)
        if not isinstance(result, dict):
            raise json.JSONDecodeError("top-level response is not an object", raw, 0)
    except json.JSONDecodeError as exc:
        preview = re.sub(r"\s+", " ", raw)[:500] or "空响应"
        raise RuntimeError(f"模型接口没有返回合法 JSON：{exc.msg}。响应片段：{preview}") from exc
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "\n".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in content)
    return str(content or "").strip()

def image_part(path):
    if not path or not os.path.exists(path):
        return None
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}


def audio_part(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    fmt = "mp3" if path.lower().endswith(".mp3") else "wav"
    return {"type": "input_audio", "input_audio": {"data": encoded, "format": fmt}}


def ffmpeg_exe():
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


def ensure_ai_audio(asset):
    analysis_dir = asset.get("analysisDir", "")
    video_path = asset.get("videoPath", "")
    audio_path = find_analysis_file(analysis_dir, "audio_for_ai.mp3") or find_analysis_file(analysis_dir, "audio_16k_mono.wav")
    if audio_path:
        return audio_path, ""
    if not analysis_dir or not os.path.isdir(analysis_dir) or not video_path or not os.path.exists(video_path):
        return "", "未找到可提取音频的原视频。"
    exe = ffmpeg_exe()
    if not exe:
        return "", "当前环境未找到 ffmpeg，无法为大模型生成音频附件。"
    audio_path = os.path.join(analysis_dir, "audio_for_ai.mp3")
    cmd = [exe, "-y", "-i", video_path, "-ac", "1", "-ar", "16000", "-vn", "-b:a", "48k", audio_path]
    try:
        subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=300, check=True)
        return audio_path, ""
    except Exception as exc:
        return "", f"音频提取失败：{type(exc).__name__}: {exc}"

def extract_json_object(text):
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("模型没有返回可解析的 JSON 内容。")
    try:
        return parse_first_json_value(raw)
    except json.JSONDecodeError as exc:
        preview = re.sub(r"\s+", " ", raw)[:500] or "空响应"
        raise ValueError(f"模型返回内容不是合法 JSON：{exc.msg}。响应片段：{preview}") from exc

def transcript_paths(analysis_dir):
    return {
        "json": find_analysis_file(analysis_dir, "transcript.json"),
        "txt": find_analysis_file(analysis_dir, "transcript.txt"),
        "srt": find_analysis_file(analysis_dir, "transcript.srt"),
    }


def has_transcript(asset):
    paths = transcript_paths(asset.get("analysisDir", ""))
    return bool(paths.get("txt") and os.path.getsize(paths["txt"]) > 0)


def srt_time(value):
    if isinstance(value, (int, float)):
        seconds = max(float(value), 0)
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    raw = str(value or "").strip()
    match = re.match(r"(?:(\d+):)?(\d{1,2}):(\d{1,2})(?:[\.,](\d{1,3}))?", raw)
    if not match:
        return "00:00:00,000"
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    millis = int((match.group(4) or "0").ljust(3, "0")[:3])
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def normalize_transcript_segments(data):
    segments = data.get("segments", []) if isinstance(data, dict) else []
    normalized = []
    for idx, item in enumerate(segments, 1):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("transcript") or item.get("original") or "").strip()
        translation = str(item.get("translation_zh") or item.get("translation") or item.get("zh") or "").strip()
        if not text and not translation:
            continue
        start = item.get("start") or item.get("start_stamp") or item.get("time_start") or ""
        end = item.get("end") or item.get("end_stamp") or item.get("time_end") or ""
        normalized.append({
            "index": int(item.get("index") or idx),
            "start": start,
            "end": end,
            "text": text,
            "translation_zh": translation,
            "confidence": str(item.get("confidence") or "").strip(),
        })
    return normalized


def raw_transcript_to_data(text, note="模型返回非 JSON，已按原始文本保存为字幕。"):
    raw = str(text or "").strip()
    if not raw:
        return {"language": "auto", "segments": [], "notes": note}
    raw = re.sub(r"^```(?:text|json|markdown)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw).strip()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    segments = []
    time_pattern = re.compile(r"^\[?([0-9]{1,2}:[0-9]{2}(?:[\.:][0-9]{1,3})?)\s*(?:-|-->|~|至|到)\s*([0-9]{1,2}:[0-9]{2}(?:[\.:][0-9]{1,3})?)\]?\s*(.+)$")
    for line in lines:
        cleaned = re.sub(r"^[-*\d\.、\s]+", "", line).strip()
        if not cleaned:
            continue
        match = time_pattern.match(cleaned)
        if match:
            start, end, body = match.groups()
        else:
            start, end, body = "", "", cleaned
        if not body or body.lower().startswith(("language", "segments", "notes")):
            continue
        segments.append({
            "index": len(segments) + 1,
            "start": start,
            "end": end,
            "text": body,
            "translation_zh": "",
            "confidence": "low",
        })
    if not segments:
        segments = [{
            "index": 1,
            "start": "",
            "end": "",
            "text": raw[:6000],
            "translation_zh": "",
            "confidence": "low",
        }]
    return {"language": "auto", "segments": segments, "notes": note}

def contains_chinese(text):
    return bool(re.search(r"[\u4e00-\u9fff]", str(text or "")))


def transcript_is_chinese(language, segments):
    raw = str(language or "").strip().lower()
    if raw in ("zh", "zh-cn", "zh_hans", "zh-hans", "cn", "chinese", "中文", "汉语"):
        return True
    filled = [str(row.get("text") or "") for row in segments if str(row.get("text") or "").strip()]
    if not filled:
        return False
    chinese_count = sum(1 for item in filled if contains_chinese(item))
    return chinese_count >= max(1, math.ceil(len(filled) * 0.6))


def format_transcript_text(segments, mode="original"):
    lines = []
    for row in segments:
        start = row.get("start") or "?"
        end = row.get("end") or "?"
        original = row.get("text") or ""
        zh = row.get("translation_zh") or original
        body = zh if mode == "zh" else original
        lines.append(f"[{start}-{end}] {body}".rstrip())
    return "\n".join(lines) + ("\n" if lines else "")


def translate_transcript_segments(api_key, transcript_data):
    key = str(api_key or "").strip()
    segments = normalize_transcript_segments(transcript_data)
    language = transcript_data.get("language", "auto") if isinstance(transcript_data, dict) else "auto"
    data = dict(transcript_data or {})
    if not segments:
        data["segments"] = []
        return data
    if transcript_is_chinese(language, segments):
        for row in segments:
            if not row.get("translation_zh"):
                row["translation_zh"] = row.get("text", "")
        data["segments"] = segments
        return data
    if all(str(row.get("translation_zh") or "").strip() for row in segments):
        data["segments"] = segments
        return data
    if not key:
        data["segments"] = segments
        note = str(data.get("notes") or "").strip()
        data["notes"] = (note + "\n" if note else "") + "检测到非中文字幕，但未填写模型 Key，暂未生成中文翻译。"
        return data
    payload = {
        "language": language,
        "segments": [
            {"index": row.get("index"), "start": row.get("start"), "end": row.get("end"), "text": row.get("text", "")}
            for row in segments
        ],
    }
    prompts = current_prompts()
    messages = [
        {"role": "system", "content": prompts["translateSystem"]},
        {"role": "user", "content": render_prompt_template(prompts["translateUser"], {"transcript_payload": json.dumps(payload, ensure_ascii=False)})},
    ]
    content = call_ai_model(key, messages, temperature=0, max_tokens=10000)
    parsed = extract_json_object(content)
    translated = {}
    for item in parsed.get("segments", []) if isinstance(parsed, dict) else []:
        if isinstance(item, dict):
            idx = item.get("index")
            zh = str(item.get("translation_zh") or item.get("translation") or item.get("zh") or "").strip()
            if idx is not None and zh:
                translated[int(idx)] = zh
    for row in segments:
        idx = int(row.get("index") or 0)
        if translated.get(idx):
            row["translation_zh"] = translated[idx]
    data["segments"] = segments
    note = str(data.get("notes") or "").strip()
    data["notes"] = (note + "\n" if note else "") + "已为非中文字幕生成简体中文翻译。"
    return data

def safe_translate_transcript_segments(api_key, transcript_data):
    try:
        return translate_transcript_segments(api_key, transcript_data)
    except Exception as exc:
        data = dict(transcript_data or {})
        note = str(data.get("notes") or "").strip()
        data["notes"] = (note + "\n" if note else "") + f"中文字幕翻译失败，已保留原文字幕：{exc}"
        return data
def write_transcript_files(asset, transcript_data):
    analysis_dir = asset.get("analysisDir", "")
    os.makedirs(analysis_dir, exist_ok=True)
    segments = normalize_transcript_segments(transcript_data)
    language = transcript_data.get("language", "auto") if isinstance(transcript_data, dict) else "auto"
    notes = transcript_data.get("notes", "") if isinstance(transcript_data, dict) else ""
    model = transcript_data.get("model", AI_MODEL) if isinstance(transcript_data, dict) else AI_MODEL
    payload = {
        "asset_id": asset.get("id"),
        "video": asset.get("videoPath"),
        "language": language,
        "model": model,
        "notes": notes,
        "segments": segments,
    }
    zh_segments = []
    for row in segments:
        zh_row = dict(row)
        zh_row["original_text"] = row.get("text", "")
        zh_row["text"] = row.get("translation_zh") or row.get("text", "")
        zh_segments.append(zh_row)
    zh_payload = dict(payload)
    zh_payload["view"] = "zh"
    zh_payload["segments"] = zh_segments
    json_path = os.path.join(analysis_dir, "transcript.json")
    txt_path = os.path.join(analysis_dir, "transcript.txt")
    srt_path = os.path.join(analysis_dir, "transcript.srt")
    zh_json_path = os.path.join(analysis_dir, "transcript_zh.json")
    zh_txt_path = os.path.join(analysis_dir, "transcript_zh.txt")
    zh_srt_path = os.path.join(analysis_dir, "transcript_zh.srt")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(zh_json_path, "w", encoding="utf-8") as f:
        json.dump(zh_payload, f, ensure_ascii=False, indent=2)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(format_transcript_text(segments, "original"))
    with open(zh_txt_path, "w", encoding="utf-8") as f:
        f.write(format_transcript_text(segments, "zh"))
    with open(srt_path, "w", encoding="utf-8") as f:
        for pos, row in enumerate(segments, 1):
            body = row.get("text") or row.get("translation_zh") or ""
            f.write(f"{pos}\n{srt_time(row.get('start'))} --> {srt_time(row.get('end'))}\n{body}\n\n")
    with open(zh_srt_path, "w", encoding="utf-8") as f:
        for pos, row in enumerate(segments, 1):
            body = row.get("translation_zh") or row.get("text") or ""
            f.write(f"{pos}\n{srt_time(row.get('start'))} --> {srt_time(row.get('end'))}\n{body}\n\n")
    return txt_path

def local_asr_language_code(language):
    raw = str(language or "auto").strip().lower()
    mapping = {
        "zh": "zh", "cn": "zh", "chinese": "zh", "中文": "zh", "汉语": "zh",
        "en": "en", "english": "en", "英语": "en", "英文": "en",
        "id": "id", "indonesian": "id", "indonesia": "id", "印尼语": "id", "印尼文": "id",
        "auto": None, "": None,
    }
    if raw not in mapping:
        raise ValueError("本地 ASR 语种仅支持中文、英语和印尼语。")
    return mapping[raw]


def transcribe_asset_local_asr(asset, language="auto", model_name="", api_key=""):
    audio_path, warning = ensure_ai_audio(asset)
    if warning or not audio_path:
        raise ValueError(warning or "没有可用音频，请先完成素材拉片。")
    lang = local_asr_language_code(language)
    analysis_dir = asset.get("analysisDir", "")
    raw_path = os.path.join(analysis_dir, "transcript_local_asr_raw.txt")
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise ValueError("本地 ASR 依赖不可用：faster-whisper 未安装或加载失败。") from exc
    default_model_path = os.path.join(WORKSPACE, "models", "faster-whisper-small")
    default_model = default_model_path if os.path.isdir(default_model_path) else "small"
    model_name = str(model_name or os.environ.get("LOCAL_ASR_MODEL", default_model)).strip() or default_model
    try:
        model = WhisperModel(model_name, device="cpu", compute_type="int8", local_files_only=True)
        segments_iter, info = model.transcribe(
            audio_path,
            language=lang,
            vad_filter=True,
            beam_size=5,
        )
        segments = []
        raw_lines = []
        for idx, seg in enumerate(segments_iter, 1):
            text = str(getattr(seg, "text", "") or "").strip()
            if not text:
                continue
            start = float(getattr(seg, "start", 0) or 0)
            end = float(getattr(seg, "end", 0) or 0)
            row = {
                "index": idx,
                "start": fmt_time(start),
                "end": fmt_time(end),
                "text": text,
                "translation_zh": "",
                "confidence": "medium",
            }
            segments.append(row)
            raw_lines.append(f"[{row['start']}-{row['end']}] {text}")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write("\n".join(raw_lines))
        if not segments:
            raise RuntimeError("本地 ASR 没有识别出有效字幕。")
        detected_language = getattr(info, "language", "") or lang or "auto"
        data = {
            "language": detected_language,
            "model": f"local-faster-whisper:{model_name}",
            "notes": "本地 ASR 转写结果，建议人工复核。",
            "segments": segments,
        }
        data = safe_translate_transcript_segments(api_key, data)
        return write_transcript_files(asset, data)
    except ValueError:
        raise
    except Exception as exc:
        message = str(exc)
        if "snapshot folder" in message or "Hub" in message or "local disk" in message or "ConnectTimeout" in message:
            raise ValueError(f"本地 ASR 模型未找到：{model_name}。当前已禁用联网下载，请在弹窗里填写已下载的 faster-whisper 模型目录，或先下载模型到本机。") from exc
        raise ValueError(f"本地 ASR 转写失败：{exc}") from exc
def transcribe_asset_audio(asset, api_key):
    key = require_api_key(api_key)
    audio_path, warning = ensure_ai_audio(asset)
    if warning or not audio_path:
        raise ValueError(warning or "没有可用音频，请先完成素材拉片。")
    analysis_dir = asset.get("analysisDir", "")
    raw_path = os.path.join(analysis_dir, "transcript_raw_response.txt")
    prompts = current_prompts()
    messages = [
        {"role": "system", "content": prompts["transcribeSystem"]},
        {"role": "user", "content": [
            {"type": "text", "text": prompts["transcribeUser"]},
            audio_part(audio_path),
        ]},
    ]
    content = call_ai_model(key, messages, temperature=0, max_tokens=8000)
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(content or "")
    if not str(content or "").strip():
        raise ValueError("模型接口没有返回任何音频转写内容。当前 gemini-3.1-pro-preview / PocketCity chat/completions 调用方式可能不支持 input_audio；请改用支持音频文件的转写模型或转写接口。")
    try:
        data = extract_json_object(content)
    except ValueError:
        retry = [
            {"role": "system", "content": prompts["transcriptRepairSystem"]},
            {"role": "user", "content": render_prompt_template(prompts["transcriptRepairUser"], {"raw_response": (content or "")[:12000]})},
        ]
        fixed = call_ai_model(key, retry, temperature=0, max_tokens=8000)
        with open(os.path.join(analysis_dir, "transcript_json_repair_response.txt"), "w", encoding="utf-8") as f:
            f.write(fixed or "")
        try:
            data = extract_json_object(fixed)
        except ValueError:
            data = raw_transcript_to_data(content, "模型两次都没有返回可解析 JSON，已将原始返回按文本字幕兜底保存；建议人工复核。")
    if not normalize_transcript_segments(data):
        data = raw_transcript_to_data(content, "模型返回 JSON 但没有有效 segments，已将原始返回按文本字幕兜底保存；建议人工复核。")
    data = safe_translate_transcript_segments(key, data)
    return write_transcript_files(asset, data)
def build_report_messages(asset, extra_warnings=None):
    analysis_dir = asset.get("analysisDir", "")
    if not analysis_dir or not os.path.isdir(analysis_dir):
        raise ValueError("该素材还没有可用的拉片素材包。")
    if not has_transcript(asset):
        raise ValueError("该素材还没有完成音频转写，请先点击“音频转写”。")
    metadata_path = find_analysis_file(analysis_dir, "metadata.json")
    prep_path = find_analysis_file(analysis_dir, "prep_result.json")
    paths = transcript_paths(analysis_dir)
    storyboard_path = find_analysis_file(analysis_dir, "storyboard.jpg")
    metadata = read_json_file(metadata_path, {}) or {}
    prep = read_json_file(prep_path, {}) or {}
    transcript = read_text_file(paths.get("txt", ""), "")[:30000]
    transcript_json = read_json_file(paths.get("json", ""), {}) or {}
    frames = normalized_frame_items(analysis_dir, metadata, prep, limit=24)
    frame_lines = []
    image_parts = []
    warnings = list(extra_warnings or []) + list(prep.get("warnings", []) or [])

    storyboard_part = image_part(storyboard_path)
    if storyboard_part:
        image_parts.append({"type": "text", "text": "storyboard 总览图，请结合字幕分析整体叙事结构、画面文字和CTA："})
        image_parts.append(storyboard_part)
    for item in frames[:12]:
        stamp = item.get("stamp") or fmt_time(item.get("timestamp", 0))
        frame_lines.append(f"- {item.get('index')}: {stamp} `{item.get('file', '')}`")
        part = image_part(item.get("file", ""))
        if part:
            image_parts.append({"type": "text", "text": f"代表帧 {item.get('index')} / {stamp}，请读取画面内烧录字幕和可见文字："})
            image_parts.append(part)

    context = {
        "asset_id": asset.get("id"),
        "title": asset.get("title") or asset.get("sourceName"),
        "video_path": asset.get("videoPath"),
        "analysis_dir": analysis_dir,
        "metadata": metadata,
        "prep_warnings": warnings,
        "frame_index": frame_lines,
        "audio_transcript_txt": transcript,
        "audio_transcript_json": transcript_json,
        "transcript_txt_path": paths.get("txt"),
        "transcript_json_path": paths.get("json"),
        "transcript_srt_path": paths.get("srt"),
        "visual_subtitle_ocr_requirement": "必须从 storyboard 和代表帧中继续核对烧录字幕、片头字、CTA 与屏幕文字；但完整台词以 audio_transcript 为主。",
    }
    prompts = current_prompts()
    prompt = render_prompt_template(prompts["reportUser"], {
        "context_json": json.dumps(context, ensure_ascii=False, indent=2)[:42000],
    })
    content = [{"type": "text", "text": prompt}] + image_parts
    return [
        {"role": "system", "content": prompts["reportSystem"]},
        {"role": "user", "content": content},
    ]


def generate_ai_report(asset, api_key):
    key = require_api_key(api_key)
    if not has_transcript(asset):
        raise ValueError("该素材还没有完成音频转写，请先点击“音频转写”。")
    report = call_ai_model(key, build_report_messages(asset), temperature=0.25, max_tokens=9000)
    if not report.strip():
        raise RuntimeError("模型没有返回拉片报告。")
    analysis_dir = asset.get("analysisDir", "")
    report_path = os.path.join(analysis_dir, "AI_video_analysis_bilingual.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report.strip() + "\n")
    return report_path

def ai_tag_report(text, schema, api_key):
    key = require_api_key(api_key)
    prompts = current_prompts()
    prompt = render_prompt_template(prompts["tagUser"], {
        "schema_json": json.dumps(tag_context(), ensure_ascii=False, indent=2),
        "report_text": text[:50000],
    })
    messages = [
        {"role": "system", "content": prompts["tagSystem"] + "\n你必须只输出一个 JSON 对象，不要输出解释、Markdown 或代码块。"},
        {"role": "user", "content": prompt},
    ]
    content = call_ai_model(key, messages, temperature=0.05, max_tokens=5000)
    try:
        data = extract_json_object(content)
    except ValueError:
        retry_messages = messages + [
            {"role": "assistant", "content": content or ""},
            {"role": "user", "content": "上一次响应无法解析。请重新输出一个合法 JSON 对象，且只能输出 JSON。格式必须是：{\"tags\":{...},\"tagDefinitions\":{...},\"summary\":\"...\",\"evidence\":{...}}"},
        ]
        content = call_ai_model(key, retry_messages, temperature=0, max_tokens=5000)
        data = extract_json_object(content)
    tags = normalize_tags(data.get("tags", {}))
    summary = str(data.get("summary") or summarize_report(text)).strip()
    evidence = data.get("evidence", {}) if isinstance(data.get("evidence", {}), dict) else {}
    definitions = data.get("tagDefinitions", {}) if isinstance(data.get("tagDefinitions", {}), dict) else {}
    return tags, evidence, summary, definitions

def parse_time_to_seconds(value):
    if isinstance(value, (int, float)):
        return max(float(value), 0.0)
    raw = str(value or "").strip().replace(",", ".")
    if not raw:
        return 0.0
    parts = raw.split(":")
    try:
        if len(parts) == 3:
            return max(int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2]), 0.0)
        if len(parts) == 2:
            return max(int(parts[0]) * 60 + float(parts[1]), 0.0)
        return max(float(raw), 0.0)
    except Exception:
        return 0.0


def seconds_to_stamp(seconds):
    seconds = max(float(seconds or 0), 0.0)
    minutes = int(seconds // 60)
    rest = seconds - minutes * 60
    return f"{minutes:02d}:{rest:05.2f}"


def find_asset_by_id(db, asset_id):
    return next((item for item in db.get("assets", []) if item.get("id") == asset_id), None)


def editing_dir(asset):
    analysis_dir = asset.get("analysisDir", "")
    if not analysis_dir:
        raise ValueError("This asset has no analysis directory yet.")
    path = os.path.join(analysis_dir, "editing")
    os.makedirs(path, exist_ok=True)
    return path


def artifact_url_for_path(asset, path):
    analysis_dir = os.path.abspath(asset.get("analysisDir", ""))
    target = os.path.abspath(path)
    if not is_within(analysis_dir, target):
        return ""
    return asset_url(asset.get("id", ""), os.path.relpath(target, analysis_dir))


def load_transcript_segments(asset):
    paths = transcript_paths(asset.get("analysisDir", ""))
    data = read_json_file(find_analysis_file(asset.get("analysisDir", ""), "transcript_zh.json"), None)
    if not data:
        data = read_json_file(paths.get("json"), {}) or {}
    return normalize_transcript_segments(data)


def asset_duration_seconds(asset):
    analysis_dir = asset.get("analysisDir", "")
    metadata = read_json_file(find_analysis_file(analysis_dir, "metadata.json"), {}) or {}
    prep = read_json_file(find_analysis_file(analysis_dir, "prep_result.json"), {}) or {}
    for source in (metadata, prep):
        for key in ("duration", "duration_seconds", "durationSec"):
            try:
                value = float(source.get(key) or 0)
                if value > 0:
                    return value
            except Exception:
                pass
    segments = load_transcript_segments(asset)
    if segments:
        return max(parse_time_to_seconds(item.get("end")) for item in segments)
    return 0.0


def transcript_context_text(asset, max_chars=22000):
    analysis_dir = asset.get("analysisDir", "")
    for path in (find_analysis_file(analysis_dir, "transcript_zh.txt"), find_analysis_file(analysis_dir, "transcript.txt")):
        text = read_text_file(path, "")
        if text.strip():
            return text[:max_chars]
    lines = []
    for item in load_transcript_segments(asset)[:500]:
        text = item.get("translation_zh") or item.get("text") or ""
        if text:
            lines.append(f"[{item.get('start')}-{item.get('end')}] {text}")
    return "\n".join(lines)[:max_chars]


def report_context_text(asset, max_chars=30000):
    analysis_dir = asset.get("analysisDir", "")
    for name in ("AI_video_analysis_bilingual.md", "AI_video_analysis_visual_bilingual.md"):
        path = find_analysis_file(analysis_dir, name)
        text = read_text_file(path, "")
        if text.strip() and not looks_like_placeholder_report(path):
            return text[:max_chars]
    return ""


def build_editing_context(asset):
    analysis_dir = asset.get("analysisDir", "")
    metadata = read_json_file(find_analysis_file(analysis_dir, "metadata.json"), {}) or {}
    prep = read_json_file(find_analysis_file(analysis_dir, "prep_result.json"), {}) or {}
    transcript = transcript_context_text(asset)
    report = report_context_text(asset)
    if not transcript and not report:
        raise ValueError("This asset has no usable transcript or official analysis report. Please finish transcription and AI analysis first.")
    frames = normalized_frame_items(analysis_dir, metadata, prep, limit=48)
    return {
        "asset_id": asset.get("id"),
        "title": asset.get("title") or asset.get("sourceName"),
        "video_path": asset.get("videoPath"),
        "duration_seconds": asset_duration_seconds(asset),
        "metadata": metadata,
        "tags": asset.get("tags", {}),
        "transcript": transcript,
        "report": report,
        "frame_index": [f"{item.get('index')}: {item.get('stamp')}" for item in frames],
    }




def find_series_by_id(db, series_id):
    return next((item for item in db.get("series", []) if item.get("id") == series_id), None)


def selected_series_episodes(series, episode_limit=0):
    episodes = sorted(series.get("episodes", []), key=lambda ep: int(ep.get("episodeNo") or 0))
    try:
        limit = int(episode_limit or 0)
    except Exception:
        limit = 0
    if limit > 0:
        episodes = episodes[:limit]
    return episodes


def build_series_editing_context(series, episode_limit=0):
    episodes = selected_series_episodes(series, episode_limit)
    if not episodes:
        raise ValueError("请选择至少一集剧集用于智能剪辑")
    episode_contexts = []
    for ep in episodes:
        try:
            ctx = build_editing_context(ep)
        except ValueError:
            ctx = {
                "asset_id": ep.get("id"),
                "title": ep.get("title") or ep.get("sourceName"),
                "duration_seconds": asset_duration_seconds(ep),
                "tags": {},
                "transcript": transcript_context_text(ep),
                "report": report_context_text(ep),
                "frame_index": [],
            }
        ctx["episodeId"] = ep.get("id")
        ctx["episodeNo"] = ep.get("episodeNo")
        ctx["episodeTitle"] = ep.get("title") or ep.get("sourceName")
        episode_contexts.append(ctx)
    if not any((ctx.get("transcript") or ctx.get("report")) for ctx in episode_contexts):
        raise ValueError("所选剧集缺少字幕或拉片报告，暂不能生成故事线")
    return {
        "source_type": "series",
        "series_id": series.get("id"),
        "series_title": series.get("title"),
        "episode_count": len(episode_contexts),
        "episodes": episode_contexts,
        "instruction": "Each cut segment must include episodeId when it comes from a specific episode. Final ad edits may use segments from different episodes.",
    }


def generate_editing_storylines_from_context(context, api_key):
    key = require_api_key(api_key)
    prompts = current_prompts()
    prompt = render_prompt_template(prompts["storylineUser"], {
        "source_context": json.dumps(context, ensure_ascii=False, indent=2)[:65000],
    })
    messages = [
        {"role": "system", "content": prompts["storylineSystem"]},
        {"role": "user", "content": prompt},
    ]
    content = call_ai_model(key, messages, temperature=0.35, max_tokens=8000)
    try:
        data = extract_json_object(content)
    except ValueError:
        retry = messages + [{"role": "assistant", "content": content or ""}, {"role": "user", "content": "Return only valid JSON with shape {\"storylines\":[...]}."}]
        data = extract_json_object(call_ai_model(key, retry, temperature=0, max_tokens=8000))
    return normalize_storylines(data)


def generate_editing_cutlist_from_context(context, storyline, api_key):
    key = require_api_key(api_key)
    prompts = current_prompts()
    prompt = render_prompt_template(prompts["cutlistUser"], {
        "selected_storyline": json.dumps(storyline or {}, ensure_ascii=False, indent=2),
        "source_context": json.dumps(context, ensure_ascii=False, indent=2)[:65000],
    })
    messages = [
        {"role": "system", "content": prompts["cutlistSystem"]},
        {"role": "user", "content": prompt},
    ]
    content = call_ai_model(key, messages, temperature=0.18, max_tokens=8000)
    try:
        data = extract_json_object(content)
    except ValueError:
        retry = messages + [{"role": "assistant", "content": content or ""}, {"role": "user", "content": "Return only valid JSON with shape {\"title\":\"\",\"segments\":[...]}."}]
        data = extract_json_object(call_ai_model(key, retry, temperature=0, max_tokens=8000))
    first_episode = (context.get("episodes") or [{}])[0].get("episodeId", "")
    duration_by_episode = {str(ep.get("episodeId")): float(ep.get("duration_seconds") or 0) for ep in context.get("episodes", [])}
    raw_segments = data.get("segments") or (storyline or {}).get("suggestedSegments") or []
    segments = []
    for item in raw_segments[:40]:
        if not isinstance(item, dict):
            continue
        episode_id = str(item.get("episodeId") or item.get("episode_id") or first_episode)
        duration = duration_by_episode.get(episode_id, 0)
        normalized = normalize_cut_segments([item], duration)
        if normalized:
            normalized[0]["episodeId"] = episode_id
            segments.append(normalized[0])
    if not segments:
        raise ValueError("No usable cut segments were generated.")
    total = sum(seg["endSeconds"] - seg["startSeconds"] for seg in segments)
    return {"id": f"cut-{int(time.time())}", "title": str(data.get("title") or (storyline or {}).get("title") or "Ad cutlist").strip(), "estimatedDuration": str(data.get("estimatedDuration") or f"about {total:.0f}s"), "logic": str(data.get("logic") or "").strip(), "coverSuggestion": str(data.get("coverSuggestion") or "").strip(), "subtitleStyle": str(data.get("subtitleStyle") or "").strip(), "segments": segments}


def normalize_storylines(data):
    rows = data.get("storylines", data if isinstance(data, list) else []) if isinstance(data, (dict, list)) else []
    if not isinstance(rows, list):
        rows = []
    storylines = []
    for idx, item in enumerate(rows[:8], 1):
        if not isinstance(item, dict):
            continue
        storylines.append({
            "id": str(item.get("id") or f"story-{idx}"),
            "title": str(item.get("title") or f"Storyline {idx}").strip(),
            "duration": str(item.get("duration") or item.get("targetDuration") or "30-60s").strip(),
            "targetAudience": str(item.get("targetAudience") or "").strip(),
            "hook": str(item.get("hook") or "").strip(),
            "arc": str(item.get("arc") or item.get("storyArc") or "").strip(),
            "reason": str(item.get("reason") or item.get("why") or "").strip(),
            "risk": str(item.get("risk") or "").strip(),
            "suggestedSegments": item.get("segments") if isinstance(item.get("segments"), list) else [],
        })
    if not storylines:
        raise ValueError("The model did not return usable storylines.")
    return storylines



def unique_series_storyline_id(existing_ids, index=1):
    base = f"story-{int(time.time() * 1000)}-{index}"
    value = base
    cursor = 2
    while value in existing_ids:
        value = f"{base}-{cursor}"
        cursor += 1
    existing_ids.add(value)
    return value


def save_series_storylines(db, series_id, storylines, episode_limit=0):
    series = find_series_by_id(db, series_id)
    if not series:
        raise ValueError("剧集不存在")
    existing = series.setdefault("storylines", [])
    existing_ids = {str(item.get("id")) for item in existing if isinstance(item, dict)}
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        clean_limit = int(episode_limit or 0)
    except Exception:
        clean_limit = 0
    saved = []
    for idx, item in enumerate(storylines or [], 1):
        if not isinstance(item, dict):
            continue
        row = copy.deepcopy(item)
        row["modelId"] = str(row.get("id") or "")
        row["id"] = unique_series_storyline_id(existing_ids, idx)
        row["episodeLimit"] = clean_limit
        row["status"] = row.get("status") or "已确认故事线"
        row["createdAt"] = now
        row["updatedAt"] = now
        saved.append(row)
    if saved:
        series["storylines"] = saved + existing
        series["updatedAt"] = now
        save_db(db)
    return saved


def find_series_storyline(series, storyline_id):
    sid = str(storyline_id or "")
    if not sid:
        return None
    for item in series.get("storylines", []) or []:
        if isinstance(item, dict) and str(item.get("id")) == sid:
            return item
    return None


def update_series_storyline_outputs(db, series_id, storyline_id, updates):
    series = find_series_by_id(db, series_id)
    if not series:
        raise ValueError("剧集不存在")
    row = find_series_storyline(series, storyline_id)
    if not row:
        return None
    row.update(copy.deepcopy(updates or {}))
    row["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
    series["updatedAt"] = row["updatedAt"]
    save_db(db)
    return row


def generate_editing_storylines(asset, api_key):
    key = require_api_key(api_key)
    context = build_editing_context(asset)
    prompts = current_prompts()
    prompt = render_prompt_template(prompts["storylineUser"], {
        "source_context": json.dumps(context, ensure_ascii=False, indent=2)[:52000],
    })
    messages = [
        {"role": "system", "content": prompts["storylineSystem"]},
        {"role": "user", "content": prompt},
    ]
    content = call_ai_model(key, messages, temperature=0.35, max_tokens=7000)
    try:
        data = extract_json_object(content)
    except ValueError:
        retry = messages + [
            {"role": "assistant", "content": content or ""},
            {"role": "user", "content": "The previous response was not parseable. Return only valid JSON with shape {\"storylines\":[...]}."},
        ]
        data = extract_json_object(call_ai_model(key, retry, temperature=0, max_tokens=7000))
    return normalize_storylines(data)


def normalize_cut_segments(segments, duration=0):
    normalized = []
    for item in (segments or [])[:32]:
        if not isinstance(item, dict):
            continue
        start = parse_time_to_seconds(item.get("sourceStart") or item.get("start") or item.get("source_start"))
        end = parse_time_to_seconds(item.get("sourceEnd") or item.get("end") or item.get("source_end"))
        if end <= start:
            continue
        if duration and start > duration:
            continue
        if duration:
            end = min(end, duration)
        if end - start < 0.3:
            continue
        normalized.append({
            "index": len(normalized) + 1,
            "sourceStart": seconds_to_stamp(start),
            "sourceEnd": seconds_to_stamp(end),
            "startSeconds": round(start, 3),
            "endSeconds": round(end, 3),
            "role": str(item.get("role") or item.get("title") or "source segment").strip(),
            "caption": str(item.get("caption") or item.get("subtitle") or "").strip(),
            "reason": str(item.get("reason") or item.get("note") or "").strip(),
        })
    return normalized


def generate_editing_cutlist(asset, storyline, api_key):
    key = require_api_key(api_key)
    context = build_editing_context(asset)
    duration = float(context.get("duration_seconds") or 0)
    initial_segments = normalize_cut_segments((storyline or {}).get("suggestedSegments") or (storyline or {}).get("segments") or [], duration)
    prompts = current_prompts()
    prompt = render_prompt_template(prompts["cutlistUser"], {
        "selected_storyline": json.dumps(storyline or {}, ensure_ascii=False, indent=2),
        "source_context": json.dumps(context, ensure_ascii=False, indent=2)[:50000],
    })
    messages = [
        {"role": "system", "content": prompts["cutlistSystem"]},
        {"role": "user", "content": prompt},
    ]
    content = call_ai_model(key, messages, temperature=0.18, max_tokens=7000)
    try:
        data = extract_json_object(content)
    except ValueError:
        retry = messages + [
            {"role": "assistant", "content": content or ""},
            {"role": "user", "content": "The previous response was not parseable. Return only valid JSON with shape {\"title\":\"\",\"segments\":[...]}."},
        ]
        data = extract_json_object(call_ai_model(key, retry, temperature=0, max_tokens=7000))
    segments = normalize_cut_segments(data.get("segments") or initial_segments, duration) or initial_segments
    if not segments:
        for item in load_transcript_segments(asset)[:10]:
            start = parse_time_to_seconds(item.get("start"))
            end = parse_time_to_seconds(item.get("end"))
            if end > start:
                segments.append({"index": len(segments) + 1, "sourceStart": seconds_to_stamp(start), "sourceEnd": seconds_to_stamp(end), "startSeconds": start, "endSeconds": end, "role": "transcript fallback", "caption": item.get("translation_zh") or item.get("text") or "", "reason": "fallback from transcript timecode"})
    if not segments:
        raise ValueError("No usable cut segments were generated.")
    total = sum(seg["endSeconds"] - seg["startSeconds"] for seg in segments)
    return {
        "id": f"cut-{int(time.time())}",
        "title": str(data.get("title") or (storyline or {}).get("title") or "Ad cutlist").strip(),
        "estimatedDuration": str(data.get("estimatedDuration") or f"about {total:.0f}s"),
        "logic": str(data.get("logic") or "").strip(),
        "coverSuggestion": str(data.get("coverSuggestion") or "").strip(),
        "subtitleStyle": str(data.get("subtitleStyle") or "").strip(),
        "segments": segments,
    }


def write_cutlist_files(asset, cutlist):
    out_dir = editing_dir(asset)
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", str(cutlist.get("id") or int(time.time()))).strip("-") or str(int(time.time()))
    cutlist_path = os.path.join(out_dir, f"{safe_id}_cutlist.json")
    with open(cutlist_path, "w", encoding="utf-8") as f:
        json.dump(cutlist, f, ensure_ascii=False, indent=2)
    srt_path = os.path.join(out_dir, f"{safe_id}_captions.srt")
    cursor = 0.0
    blocks = []
    for idx, seg in enumerate(cutlist.get("segments", []), 1):
        duration = max(float(seg.get("endSeconds", 0)) - float(seg.get("startSeconds", 0)), 0.5)
        text = seg.get("caption") or seg.get("role") or f"Segment {idx}"
        blocks.append(f"{idx}\n{srt_time(cursor)} --> {srt_time(cursor + duration)}\n{text}\n")
        cursor += duration
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    return cutlist_path, srt_path


def render_cutlist_preview(asset, cutlist):
    exe = ffmpeg_exe()
    if not exe:
        raise ValueError("ffmpeg was not found, so preview rendering cannot run.")
    video_path = asset.get("videoPath", "")
    if not video_path or not os.path.exists(video_path):
        raise ValueError("Source video does not exist, so preview rendering cannot run.")
    out_dir = editing_dir(asset)
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", str(cutlist.get("id") or int(time.time()))).strip("-") or str(int(time.time()))
    segment_paths = []
    for idx, seg in enumerate(cutlist.get("segments", []), 1):
        start = float(seg.get("startSeconds") or parse_time_to_seconds(seg.get("sourceStart")))
        end = float(seg.get("endSeconds") or parse_time_to_seconds(seg.get("sourceEnd")))
        if end <= start:
            continue
        out_path = os.path.join(out_dir, f"{safe_id}_seg_{idx:02d}.mp4")
        cmd = [exe, "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", video_path, "-map", "0:v:0", "-map", "0:a?", "-vf", "scale=1080:-2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", out_path]
        proc = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"Preview segment render failed: {proc.stderr[-800:]}")
        segment_paths.append(out_path)
    if not segment_paths:
        raise ValueError("The cutlist has no renderable segments.")
    concat_path = os.path.join(out_dir, f"{safe_id}_concat.txt")
    with open(concat_path, "w", encoding="utf-8") as f:
        for path in segment_paths:
            f.write("file '" + path.replace("\\", "/").replace("'", "'\\''") + "'\n")
    preview_path = os.path.join(out_dir, f"{safe_id}_preview.mp4")
    cmd = [exe, "-y", "-f", "concat", "-safe", "0", "-i", concat_path, "-c", "copy", preview_path]
    proc = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"Preview concat failed: {proc.stderr[-800:]}")
    cutlist_path, srt_path = write_cutlist_files(asset, cutlist)
    return preview_path, cutlist_path, srt_path


def load_jianying_json_file(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return None


JY_DRAFTC_EXE = os.environ.get("JY_DRAFTC_EXE") or r"C:\tmp\jy-draftc\jy-draftc-amd64-windows\jy-draftc.exe"


def find_jianying_install_dir():
    configured = os.environ.get("JY_INSTALL_DIR", "").strip()
    if configured and os.path.isfile(os.path.join(configured, "videoeditor.dll")):
        return configured
    apps_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "JianyingPro", "Apps")
    if not os.path.isdir(apps_dir):
        return ""
    candidates = []
    for name in os.listdir(apps_dir):
        full = os.path.join(apps_dir, name)
        if os.path.isdir(full) and os.path.isfile(os.path.join(full, "videoeditor.dll")):
            candidates.append((name, full))
    candidates.sort(reverse=True)
    return candidates[0][1] if candidates else ""


def ensure_jy_draftc_ready():
    exe = os.path.abspath(JY_DRAFTC_EXE)
    if not os.path.isfile(exe):
        raise ValueError("jy-draftc.exe was not found. Please place it at C:/tmp/jy-draftc/jy-draftc-amd64-windows/jy-draftc.exe or set JY_DRAFTC_EXE.")
    install_dir = find_jianying_install_dir()
    if not install_dir:
        raise ValueError("Jianying videoeditor.dll was not found. Please set JY_INSTALL_DIR to the Jianying version folder.")
    env_path = os.path.join(os.path.dirname(exe), ".env")
    with open(env_path, "w", encoding="ascii") as f:
        f.write("JY_INSTALL_DIR=" + install_dir + "\n")
    return exe


def jy_draftc_temp_path(label, suffix=".json"):
    safe = re.sub(r"[^0-9A-Za-z_-]+", "-", str(label or "draftc")).strip("-") or "draftc"
    folder = os.path.join(r"C:\tmp", "jy-draftc-runtime")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{safe}-{uuid.uuid4().hex}{suffix}")


def run_jy_draftc(mode, input_path, output_path):
    exe = ensure_jy_draftc_ready()
    flag = "-d" if mode == "dec" else "-e"
    proc = subprocess.run([exe, flag, input_path, output_path], cwd=os.path.dirname(exe), capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "jy-draftc failed")[-1200:])
    if not os.path.isfile(output_path) or os.path.getsize(output_path) <= 0:
        raise RuntimeError("jy-draftc did not create a valid output file.")
    return output_path


def decrypt_jianying_json_file(path):
    plain = load_jianying_json_file(path)
    if isinstance(plain, dict):
        return plain, path, False
    out_path = jy_draftc_temp_path(os.path.basename(path) + "-dec")
    run_jy_draftc("dec", path, out_path)
    data = load_jianying_json_file(out_path)
    if not isinstance(data, dict):
        raise ValueError("jy-draftc decrypted output is not valid JSON: " + path)
    return data, out_path, True


def encrypt_jianying_json_to_file(data, output_path):
    plain_path = jy_draftc_temp_path(os.path.basename(output_path) + "-plain")
    with open(plain_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    run_jy_draftc("enc", plain_path, output_path)
    return output_path


def find_jianying_content_template(template_path):
    base = os.path.abspath(str(template_path or "").strip())
    if not base or not os.path.isdir(base):
        raise ValueError("A valid Jianying sample draft folder is required for real project export.")
    candidates = []
    preferred = ["draft_content.json", "template-2.tmp", "template.tmp", "draft_content.json.bak"]
    for name in preferred:
        path = os.path.join(base, name)
        if os.path.isfile(path):
            candidates.append(path)
    timeline_root = os.path.join(base, "Timelines")
    if os.path.isdir(timeline_root):
        for root, _, files in os.walk(timeline_root):
            for name in preferred:
                if name in files:
                    candidates.append(os.path.join(root, name))
    backup_dir = os.path.join(base, ".backup")
    if os.path.isdir(backup_dir):
        for root, _, files in os.walk(backup_dir):
            for name in files:
                full = os.path.join(root, name)
                try:
                    if os.path.getsize(full) <= 0 or os.path.getsize(full) > 5_000_000:
                        continue
                    candidates.append(full)
                except Exception:
                    pass
    seen = set()
    best_empty = None
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        try:
            data, source, encrypted = decrypt_jianying_json_file(path)
        except Exception:
            continue
        materials = data.get("materials") or {}
        tracks = data.get("tracks") or []
        if isinstance(materials, dict) and isinstance(tracks, list):
            if tracks and materials.get("videos") is not None and materials.get("texts") is not None:
                return data, path
            best_empty = best_empty or (data, path)
    if best_empty:
        return best_empty
    raise ValueError("No readable or decryptable Jianying draft_content/template JSON was found in the sample draft folder.")


def clone_json(value):
    return copy.deepcopy(value)


def new_jy_id():
    return str(uuid.uuid4()).upper()


def us(seconds):
    return max(int(round(float(seconds or 0) * 1000000)), 0)


def asset_video_info(asset, fallback_video=None):
    analysis_dir = asset.get("analysisDir", "")
    metadata = read_json_file(find_analysis_file(analysis_dir, "metadata.json"), {}) or {}
    prep = read_json_file(find_analysis_file(analysis_dir, "prep_result.json"), {}) or {}
    width = metadata.get("width") or prep.get("width") or (fallback_video or {}).get("width") or 1080
    height = metadata.get("height") or prep.get("height") or (fallback_video or {}).get("height") or 1920
    duration = asset_duration_seconds(asset) or ((fallback_video or {}).get("duration") or 0) / 1000000 or 0
    return int(width or 1080), int(height or 1920), float(duration or 0)


def text_content_payload(text, text_template):
    text = str(text or "").strip() or " "
    try:
        content = json.loads(text_template.get("content", "{}")) if text_template else {}
    except Exception:
        content = {}
    content["text"] = text
    styles = content.get("styles") if isinstance(content.get("styles"), list) else []
    if styles:
        styles[0]["range"] = [0, len(text)]
    else:
        styles = [{"range": [0, len(text)], "size": 6, "useLetterColor": True}]
    content["styles"] = styles
    return json.dumps(content, ensure_ascii=False, separators=(",", ":"))


def make_jianying_draft_content(template, asset, cutlist):
    content = clone_json(template)
    materials = content.setdefault("materials", {})
    for key in ["videos", "texts", "canvases", "material_animations", "placeholder_infos", "speeds", "sound_channel_mappings", "material_colors", "vocal_separations"]:
        materials.setdefault(key, [])

    sample_video = (materials.get("videos") or [{}])[0]
    sample_text = (materials.get("texts") or [{}])[0]
    sample_video_segment = None
    sample_text_segment = None
    for track in content.get("tracks", []) or []:
        if track.get("type") == "video" and track.get("segments"):
            sample_video_segment = track["segments"][0]
        if track.get("type") == "text" and track.get("segments"):
            sample_text_segment = track["segments"][0]
    sample_video_segment = sample_video_segment or {"clip": {"scale": {"x": 1.0, "y": 1.0}, "transform": {"x": 0.0, "y": 0.0}, "flip": {}}, "uniform_scale": {}, "render_timerange": {}, "source": "segmentsourcenormal"}
    sample_text_segment = sample_text_segment or {"clip": {"scale": {"x": 1.0, "y": 1.0}, "transform": {"x": 0.0, "y": -0.7880910683012259}, "flip": {}}, "uniform_scale": {}, "render_timerange": {}, "render_index": 14000, "track_render_index": 1, "source": "segmentsourcenormal"}

    video_id = new_jy_id()
    source_path = os.path.abspath(asset.get("videoPath", "")).replace("\\", "/")
    width, height, source_duration = asset_video_info(asset, sample_video)
    max_end = max([float(seg.get("endSeconds") or parse_time_to_seconds(seg.get("sourceEnd"))) for seg in cutlist.get("segments", [])] or [0])
    source_duration_us = us(max(source_duration, max_end))
    video_material = clone_json(sample_video) if isinstance(sample_video, dict) else {"type": "video"}
    video_material.update({
        "id": video_id,
        "type": "video",
        "duration": source_duration_us,
        "path": source_path,
        "width": width,
        "height": height,
        "category_name": "local",
        "material_name": os.path.basename(source_path),
        "material_id": "",
        "local_material_id": str(uuid.uuid4()),
    })
    materials["videos"] = [video_material]

    video_segments = []
    text_segments = []
    text_materials = []
    animations = []
    speeds = []
    placeholders = []
    sound_maps = []
    colors = []
    vocals = []
    canvases = materials.get("canvases") or [{"id": new_jy_id(), "type": "canvas_color"}]
    cursor = 0
    for index, seg in enumerate(cutlist.get("segments", []), 1):
        start_s = float(seg.get("startSeconds") or parse_time_to_seconds(seg.get("sourceStart")))
        end_s = float(seg.get("endSeconds") or parse_time_to_seconds(seg.get("sourceEnd")))
        if end_s <= start_s:
            continue
        dur = us(end_s - start_s)
        source_start = us(start_s)
        speed_id = new_jy_id()
        placeholder_id = new_jy_id()
        sound_id = new_jy_id()
        color_id = new_jy_id()
        vocal_id = new_jy_id()
        vseg = clone_json(sample_video_segment)
        vseg.update({
            "id": new_jy_id(),
            "material_id": video_id,
            "source_timerange": {"start": source_start, "duration": dur},
            "target_timerange": {"start": cursor, "duration": dur},
            "extra_material_refs": [speed_id, placeholder_id, canvases[0].get("id"), sound_id, color_id, vocal_id],
        })
        video_segments.append(vseg)
        speeds.append({"id": speed_id, "type": "speed"})
        placeholders.append({"id": placeholder_id, "type": "placeholder_info", "meta_type": "none"})
        sound_maps.append({"id": sound_id, "type": "none"})
        colors.append({"id": color_id})
        vocals.append({"id": vocal_id, "type": "vocal_separation"})

        caption = str(seg.get("caption") or seg.get("role") or "").strip()
        if caption:
            text_id = new_jy_id()
            anim_id = new_jy_id()
            tmat = clone_json(sample_text) if isinstance(sample_text, dict) else {"type": "text"}
            tmat.update({"id": text_id, "type": "text", "content": text_content_payload(caption, sample_text)})
            text_materials.append(tmat)
            tseg = clone_json(sample_text_segment)
            tseg.update({
                "id": new_jy_id(),
                "material_id": text_id,
                "target_timerange": {"start": cursor, "duration": dur},
                "extra_material_refs": [anim_id],
                "render_index": 14000 + index,
                "track_render_index": 1,
            })
            text_segments.append(tseg)
            animations.append({"id": anim_id, "type": "sticker_animation"})
        cursor += dur

    if not video_segments:
        raise ValueError("The cutlist has no usable segments for Jianying export.")

    content["id"] = new_jy_id()
    now_us = int(time.time() * 1000000)
    content["duration"] = cursor
    content["create_time"] = content.get("create_time") or now_us
    content["update_time"] = now_us
    content["fps"] = content.get("fps") or 30.0
    content["tracks"] = [
        {"id": new_jy_id(), "type": "video", "segments": video_segments, "is_default_name": True},
        {"id": new_jy_id(), "type": "text", "segments": text_segments, "is_default_name": True},
    ] if text_segments else [{"id": new_jy_id(), "type": "video", "segments": video_segments, "is_default_name": True}]
    materials["texts"] = text_materials
    materials["material_animations"] = animations
    materials["speeds"] = speeds
    materials["placeholder_infos"] = placeholders
    materials["sound_channel_mappings"] = sound_maps
    materials["material_colors"] = colors
    materials["vocal_separations"] = vocals
    materials["canvases"] = canvases
    content["materials"] = materials
    content["path"] = os.path.abspath(asset.get("videoPath", "")).replace("\\", "/")
    return content


def write_jianying_project_files(package_dir, draft_content):
    text = json.dumps(draft_content, ensure_ascii=False, separators=(",", ":"))
    timeline_id = str(draft_content.get("id") or new_jy_id())
    now_us = int(time.time() * 1000000)
    plain_path = os.path.join(package_dir, "ai_draft_content.json")
    with open(plain_path, "w", encoding="utf-8") as f:
        f.write(text)

    for rel in ["draft_content.json", "template-2.tmp"]:
        encrypt_jianying_json_to_file(draft_content, os.path.join(package_dir, rel))
    with open(os.path.join(package_dir, "template.tmp"), "w", encoding="utf-8") as f:
        f.write(text)

    timeline_root = os.path.join(package_dir, "Timelines")
    os.makedirs(timeline_root, exist_ok=True)
    existing_dirs = [os.path.join(timeline_root, name) for name in os.listdir(timeline_root) if os.path.isdir(os.path.join(timeline_root, name))]
    active_dir = existing_dirs[0] if existing_dirs else None
    timeline_dir = os.path.join(timeline_root, timeline_id)
    if active_dir and os.path.abspath(active_dir) != os.path.abspath(timeline_dir):
        if os.path.exists(timeline_dir):
            shutil.rmtree(timeline_dir)
        os.rename(active_dir, timeline_dir)
    else:
        os.makedirs(timeline_dir, exist_ok=True)
    for other in [os.path.join(timeline_root, name) for name in os.listdir(timeline_root) if os.path.isdir(os.path.join(timeline_root, name)) and name != timeline_id]:
        shutil.rmtree(other, ignore_errors=True)

    for rel in ["draft_content.json", "template-2.tmp"]:
        encrypt_jianying_json_to_file(draft_content, os.path.join(timeline_dir, rel))
    with open(os.path.join(timeline_dir, "template.tmp"), "w", encoding="utf-8") as f:
        f.write(text)

    layout = {
        "activeTimeline": timeline_id,
        "dockItems": [{"dockIndex": 0, "ratio": 1, "timelineIds": [timeline_id], "timelineNames": ["timeline 01"]}],
        "layoutOrientation": 1,
    }
    with open(os.path.join(package_dir, "timeline_layout.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f, ensure_ascii=False, separators=(",", ":"))

    project_path = os.path.join(timeline_root, "project.json")
    project = load_jianying_json_file(project_path) or {}
    project.update({
        "id": project.get("id") or new_jy_id(),
        "main_timeline_id": timeline_id,
        "timelines": [{"create_time": now_us, "id": timeline_id, "is_marked_delete": False, "name": "timeline 01", "update_time": now_us}],
        "update_time": now_us,
        "create_time": project.get("create_time") or now_us,
        "version": project.get("version") or 0,
    })
    project.setdefault("config", {"color_space": -1, "render_index_track_mode_on": False, "use_float_render": False})
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, separators=(",", ":"))


def item_by_episode_id(items):
    return {str(item.get("id")): item for item in items}


def render_cutlist_preview_from_items(items, cutlist):
    if not items:
        raise ValueError("No source episodes available for rendering.")
    exe = ffmpeg_exe()
    if not exe:
        raise ValueError("ffmpeg was not found, so preview rendering cannot run.")
    item_map = item_by_episode_id(items)
    first = items[0]
    out_dir = editing_dir(first)
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", str(cutlist.get("id") or int(time.time()))).strip("-") or str(int(time.time()))
    segment_paths = []
    for idx, seg in enumerate(cutlist.get("segments", []), 1):
        source = item_map.get(str(seg.get("episodeId") or "")) or first
        video_path = source.get("videoPath", "")
        if not video_path or not os.path.exists(video_path):
            continue
        start = float(seg.get("startSeconds") or parse_time_to_seconds(seg.get("sourceStart")))
        end = float(seg.get("endSeconds") or parse_time_to_seconds(seg.get("sourceEnd")))
        if end <= start:
            continue
        out_path = os.path.join(out_dir, f"{safe_id}_series_seg_{idx:02d}.mp4")
        cmd = [exe, "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", video_path, "-map", "0:v:0", "-map", "0:a?", "-vf", "scale=1080:-2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", out_path]
        proc = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"Preview segment render failed: {proc.stderr[-800:]}")
        segment_paths.append(out_path)
    if not segment_paths:
        raise ValueError("The cutlist has no renderable segments.")
    concat_path = os.path.join(out_dir, f"{safe_id}_series_concat.txt")
    with open(concat_path, "w", encoding="utf-8") as f:
        for path in segment_paths:
            f.write("file '" + path.replace("\\", "/").replace("'", "'\\''") + "'\n")
    preview_path = os.path.join(out_dir, f"{safe_id}_series_preview.mp4")
    cmd = [exe, "-y", "-f", "concat", "-safe", "0", "-i", concat_path, "-c", "copy", preview_path]
    proc = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"Preview concat failed: {proc.stderr[-800:]}")
    cutlist_path, srt_path = write_cutlist_files(first, cutlist)
    return preview_path, cutlist_path, srt_path


def flatten_cutlist_for_preview_video(cutlist, preview_path):
    cursor = 0.0
    segments = []
    for idx, seg in enumerate(cutlist.get("segments", []), 1):
        duration = max(float(seg.get("endSeconds", 0)) - float(seg.get("startSeconds", 0)), 0.5)
        segments.append({"index": idx, "sourceStart": seconds_to_stamp(cursor), "sourceEnd": seconds_to_stamp(cursor + duration), "startSeconds": cursor, "endSeconds": cursor + duration, "role": seg.get("role") or f"segment {idx}", "caption": seg.get("caption") or seg.get("role") or "", "reason": f"flattened from {seg.get('episodeId') or 'source'}"})
        cursor += duration
    return {"id": str(cutlist.get("id") or f"cut-{int(time.time())}") + "-jianying", "title": cutlist.get("title") or "Series edit", "estimatedDuration": f"about {cursor:.0f}s", "segments": segments}


def safe_jianying_name(value):
    text = str(value or "").strip() or "AI??"
    text = re.sub(r'[\/:*?"<>|]+', "-", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:80] or "AI??"


def unique_child_dir(root, name):
    base = safe_jianying_name(name)
    candidate = os.path.join(root, base)
    if not os.path.exists(candidate):
        return candidate, base
    for index in range(2, 999):
        next_name = f"{base}-{index}"
        candidate = os.path.join(root, next_name)
        if not os.path.exists(candidate):
            return candidate, next_name
    raise ValueError('无法生成唯一的剪映草稿目录名，请清理重复草稿后再试。')


def default_jianying_root_from_template(template_path):
    template_path = os.path.abspath(str(template_path or "").strip())
    if template_path and os.path.isdir(template_path):
        parent = os.path.dirname(template_path)
        if os.path.isfile(os.path.join(parent, "root_meta_info.json")):
            return parent
    return os.path.join(os.path.expanduser("~"), "AppData", "Local", "JianyingPro", "User Data", "Projects", "com.lveditor.draft")


def jy_path(path):
    return os.path.abspath(path).replace("\\", "/")


def folder_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            full = os.path.join(root, name)
            try:
                total += os.path.getsize(full)
            except OSError:
                pass
    return total


def update_jianying_draft_meta(package_dir, draft_root, draft_name, draft_id, duration_us, material_size=None, asset=None):
    now_us = int(time.time() * 1000000)
    meta_path = os.path.join(package_dir, "draft_meta_info.json")
    if os.path.isfile(meta_path):
        try:
            meta, _, _ = decrypt_jianying_json_file(meta_path)
        except Exception:
            meta = load_jianying_json_file(meta_path) or {}
    else:
        meta = {}
    if material_size is None:
        material_size = folder_size(package_dir)
    cover_path = os.path.join(package_dir, "draft_cover.jpg")
    meta.update({
        "draft_id": draft_id,
        "draft_name": draft_name,
        "draft_fold_path": jy_path(package_dir),
        "draft_json_file": jy_path(os.path.join(package_dir, "draft_content.json")),
        "draft_root_path": jy_path(draft_root),
        "draft_timeline_materials_size": int(material_size or 0),
        "draft_timeline_materials_size_": int(material_size or 0),
        "tm_draft_create": now_us,
        "tm_draft_modified": now_us,
        "tm_draft_removed": 0,
        "tm_duration": int(duration_us or 0),
        "streaming_edit_draft_ready": True,
        "draft_cover": jy_path(cover_path) if os.path.isfile(cover_path) else meta.get("draft_cover", "draft_cover.jpg"),
    })
    meta.setdefault("draft_new_version", "")
    meta.setdefault("cloud_draft_cover", False)
    meta.setdefault("cloud_draft_sync", False)
    meta.setdefault("draft_is_invisible", False)
    meta.setdefault("draft_is_ai_shorts", False)
    if asset and asset.get("videoPath"):
        video_path = jy_path(asset.get("videoPath"))
        width, height, source_duration = asset_video_info(asset, {})
        material = {
            "ai_group_type": "",
            "create_time": int(time.time()),
            "duration": int(us(source_duration) or duration_us),
            "enter_from": 0,
            "extra_info": os.path.basename(video_path),
            "file_Path": video_path,
            "height": height,
            "id": str(uuid.uuid4()),
            "import_time": int(time.time()),
            "import_time_ms": now_us,
            "item_source": 1,
            "md5": "",
            "metetype": "video",
            "roughcut_time_range": {"duration": int(us(source_duration) or duration_us), "start": 0},
            "sub_time_range": {"duration": -1, "start": -1},
            "type": 0,
            "width": width,
        }
        meta["draft_materials"] = [{"type": 0, "value": [material]}, {"type": 1, "value": []}, {"type": 2, "value": []}, {"type": 3, "value": []}, {"type": 6, "value": []}, {"type": 7, "value": []}]
    with open(os.path.join(package_dir, "ai_draft_meta_info.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))
    encrypt_jianying_json_to_file(meta, meta_path)
    return meta


def register_jianying_root(draft_root, draft_meta):
    root_path = os.path.abspath(draft_root)
    os.makedirs(root_path, exist_ok=True)
    root_meta_path = os.path.join(root_path, "root_meta_info.json")
    if os.path.isfile(root_meta_path):
        backup = root_meta_path + time.strftime(".bak-%Y%m%d-%H%M%S")
        shutil.copy2(root_meta_path, backup)
        root_meta = load_jianying_json_file(root_meta_path) or {}
    else:
        root_meta = {}
    stores = root_meta.get("all_draft_store") if isinstance(root_meta.get("all_draft_store"), list) else []
    draft_id = draft_meta.get("draft_id")
    stores = [row for row in stores if row.get("draft_id") != draft_id and row.get("draft_fold_path") != draft_meta.get("draft_fold_path")]
    stores.insert(0, draft_meta)
    stores.sort(key=lambda row: int(row.get("tm_draft_modified") or row.get("tm_draft_create") or 0), reverse=True)
    root_meta["all_draft_store"] = stores
    root_meta["draft_ids"] = len(stores)
    root_meta["root_path"] = jy_path(root_path)
    with open(root_meta_path, "w", encoding="utf-8") as f:
        json.dump(root_meta, f, ensure_ascii=False, separators=(",", ":"))
    return root_meta_path


def export_jianying_package_from_items(items, cutlist, template_path="", draft_root="", draft_name=""):
    preview_path, _, _ = render_cutlist_preview_from_items(items, cutlist)
    first = items[0]
    fake_asset = dict(first)
    fake_asset["videoPath"] = preview_path
    fake_asset["title"] = (cutlist.get("title") or first.get("title") or "Series edit") + " - preview"
    flat_cutlist = flatten_cutlist_for_preview_video(cutlist, preview_path)
    return export_jianying_package(fake_asset, flat_cutlist, template_path, draft_root, draft_name)


def export_jianying_package(asset, cutlist, template_path="", draft_root="", draft_name=""):
    out_dir = editing_dir(asset)
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", str(cutlist.get("id") or int(time.time()))).strip("-") or str(int(time.time()))
    template_path = os.path.abspath(str(template_path or "").strip())
    if not template_path or not os.path.isdir(template_path):
        raise ValueError('请填写有效的剪映样例草稿目录，目录内需要包含 draft_content.json 或 template.tmp。')
    draft_root = os.path.abspath(str(draft_root or "").strip() or default_jianying_root_from_template(template_path))
    draft_name = safe_jianying_name(draft_name or f"Ai-{asset.get('title') or asset.get('sourceName') or safe_id}")
    if not os.path.isdir(draft_root):
        raise ValueError("Invalid Jianying draft root directory.")
    if not os.path.isfile(os.path.join(draft_root, "root_meta_info.json")):
        raise ValueError("root_meta_info.json was not found under the Jianying draft root directory.")
    package_dir, actual_name = unique_child_dir(draft_root, draft_name)

    def ignore_template(dirpath, names):
        return {name for name in names if name in {".backup"}}

    shutil.copytree(template_path, package_dir, ignore=ignore_template)
    draft_asset = dict(asset)
    source_video = os.path.abspath(str(draft_asset.get("videoPath") or ""))
    if source_video and os.path.isfile(source_video):
        media_dir = os.path.join(package_dir, "Resources", "AiMaterials")
        os.makedirs(media_dir, exist_ok=True)
        media_name = re.sub(r'[^0-9A-Za-z._-]+', "-", os.path.basename(source_video)).strip("-.") or "ai_preview.mp4"
        copied_video = os.path.join(media_dir, media_name)
        if os.path.abspath(source_video) != os.path.abspath(copied_video):
            shutil.copy2(source_video, copied_video)
        draft_asset["videoPath"] = copied_video
    template, template_source = find_jianying_content_template(template_path)
    draft_content = make_jianying_draft_content(template, draft_asset, cutlist)
    draft_id = str(draft_content.get("id") or new_jy_id())
    draft_content["id"] = draft_id
    duration_us = int(draft_content.get("duration") or 0)
    write_jianying_project_files(package_dir, draft_content)

    cutlist_path, srt_path = write_cutlist_files(asset, cutlist)
    shutil.copy2(cutlist_path, os.path.join(package_dir, "cutlist.json"))
    shutil.copy2(srt_path, os.path.join(package_dir, "captions.srt"))
    draft_meta = update_jianying_draft_meta(package_dir, draft_root, actual_name, draft_id, duration_us, folder_size(package_dir), draft_asset)
    root_meta_path = register_jianying_root(draft_root, draft_meta)
    manifest = {
        "assetId": asset.get("id"),
        "assetTitle": asset.get("title") or asset.get("sourceName"),
        "sourceVideo": asset.get("videoPath"),
        "draftVideo": draft_asset.get("videoPath"),
        "templatePath": template_path,
        "templateSource": template_source,
        "draftRoot": draft_root,
        "draftName": actual_name,
        "rootMetaPath": root_meta_path,
        "status": "jianying_native_draft_registered",
        "note": '已生成并注册到剪映草稿库。若剪映已打开，请重启剪映后查看新草稿。',
        "cutlist": cutlist,
    }
    with open(os.path.join(package_dir, "jianying_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    with open(os.path.join(package_dir, "Jianying_adapter_notes.md"), "w", encoding="utf-8") as f:
        f.write("# Jianying draft adapter notes\n\nThe generated folder has been copied into the Jianying draft root and registered in root_meta_info.json. Restart Jianying if the draft list was already open.\n")
    zip_path = shutil.make_archive(os.path.join(out_dir, f"jianying_draft_{safe_id}"), "zip", package_dir)
    return package_dir, zip_path, cutlist_path, srt_path


def create_asset(title, source_name=""):
    asset_id = time.strftime("%Y%m%d-%H%M%S")
    safe_title = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", title or source_name or "untitled").strip("-")
    if safe_title:
        asset_id = f"{asset_id}-{safe_title[:28]}"
    folder = os.path.join(ASSET_DIR, asset_id)
    os.makedirs(folder, exist_ok=True)
    return asset_id, folder


def run_skill(video_path, out_dir):
    cmd = [sys.executable, SKILL_SCRIPT, "--video", video_path, "--out", out_dir, "--samples", "24", "--skip-transcript"]
    started = time.time()
    proc = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=900)
    return {
        "ok": proc.returncode == 0,
        "command": " ".join(cmd),
        "seconds": round(time.time() - started, 2),
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }

class AppHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path).path
        if parsed == "/":
            return os.path.join(STATIC_DIR, "index.html")
        if parsed.startswith("/static/"):
            return os.path.join(STATIC_DIR, parsed.replace("/static/", "", 1))
        return os.path.join(STATIC_DIR, parsed.lstrip("/"))

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/schema":
                send_json(self, schema_response())
                return
            if parsed.path == "/api/prompts":
                send_json(self, {"prompts": current_prompts(), "defaults": DEFAULT_PROMPTS, "meta": PROMPT_META})
                return
            if parsed.path == "/api/assets":
                send_json(self, enrich_assets(load_db()))
                return
            if parsed.path == "/api/series":
                db = enrich_series(load_db())
                send_json(self, {"series": db.get("series", [])})
                return
            if parsed.path == "/api/tasks":
                send_json(self, {"tasks": task_snapshot()})
                return
            if parsed.path.startswith("/asset-files/"):
                self.handle_asset_file(parsed.path)
                return
            if parsed.path.startswith("/series-files/"):
                self.handle_series_file(parsed.path)
                return
            return super().do_GET()
        except Exception as exc:
            send_json(self, {"error": f"服务端处理失败：{type(exc).__name__}: {exc}"}, 500)


    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/upload":
                self.handle_upload()
                return
            if parsed.path == "/api/series/upload":
                self.handle_series_upload()
                return
            if parsed.path == "/api/series/resume":
                self.handle_series_resume()
                return
            if parsed.path == "/api/schema":
                self.handle_schema_update()
                return
            if parsed.path == "/api/prompts":
                self.handle_prompts_update()
                return
            if parsed.path == "/api/auto-tag":
                self.handle_auto_tag()
                return
            if parsed.path == "/api/generate-report":
                self.handle_generate_report()
                return
            if parsed.path == "/api/transcribe-audio":
                self.handle_transcribe_audio()
                return
            if parsed.path == "/api/confirm":
                self.handle_confirm()
                return
            if parsed.path == "/api/editing/storylines":
                self.handle_editing_storylines()
                return
            if parsed.path == "/api/editing/cutlist":
                self.handle_editing_cutlist()
                return
            if parsed.path == "/api/editing/render-preview":
                self.handle_editing_render_preview()
                return
            if parsed.path == "/api/editing/export-jianying":
                self.handle_editing_export_jianying()
                return
            send_json(self, {"error": "Unknown endpoint"}, 404)
        except Exception as exc:
            send_json(self, {"error": f"服务端处理失败：{type(exc).__name__}: {exc}"}, 500)


    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/assets/"):
            self.handle_update_asset(parsed.path.rsplit("/", 1)[-1])
            return
        send_json(self, {"error": "Unknown endpoint"}, 404)
    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/assets/"):
            self.handle_delete_asset(unquote(parsed.path.rsplit("/", 1)[-1]))
            return
        send_json(self, {"error": "Unknown endpoint"}, 404)

    def handle_asset_file(self, request_path):
        parts = request_path.split("/", 3)
        if len(parts) < 4:
            self.send_error(404)
            return
        asset_id = unquote(parts[2])
        rel = unquote(parts[3]).replace("/", os.sep)
        db = load_db()
        asset = next((item for item in db.get("assets", []) if item.get("id") == asset_id), None)
        if not asset or not asset.get("analysisDir"):
            self.send_error(404)
            return
        base = os.path.abspath(asset["analysisDir"])
        target = os.path.abspath(os.path.join(base, rel))
        if not is_within(base, target) or not os.path.isfile(target):
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        if ctype.startswith("text/") or target.lower().endswith((".md", ".json", ".srt", ".txt")):
            ctype = f"{ctype}; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(os.path.getsize(target)))
        self.end_headers()
        with open(target, "rb") as f:
            shutil.copyfileobj(f, self.wfile)


    def handle_series_file(self, request_path):
        parts = request_path.split("/", 3)
        if len(parts) < 4:
            self.send_error(404)
            return
        episode_id = unquote(parts[2])
        rel = unquote(parts[3]).replace("/", os.sep)
        db = load_db()
        episode = None
        for series in db.get("series", []):
            for ep in series.get("episodes", []):
                if ep.get("id") == episode_id:
                    episode = ep
                    break
            if episode:
                break
        if not episode or not episode.get("analysisDir"):
            self.send_error(404)
            return
        base = os.path.abspath(episode["analysisDir"])
        target = os.path.abspath(os.path.join(base, rel))
        if not is_within(base, target) or not os.path.isfile(target):
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        if ctype.startswith("text/") or target.lower().endswith((".md", ".json", ".srt", ".txt")):
            ctype = f"{ctype}; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(os.path.getsize(target)))
        self.end_headers()
        with open(target, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def read_multipart(self):
        length = int(self.headers.get("Content-Length", "0"))
        content_type = self.headers.get("Content-Type", "")
        body = self.rfile.read(length)
        header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        message = BytesParser(policy=default).parsebytes(header + body)
        fields = {}
        if not message.is_multipart():
            return fields
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if not name:
                continue
            filename = part.get_filename()
            content = part.get_payload(decode=True) or b""
            if filename:
                fields[name] = {"filename": filename, "content": content}
            else:
                charset = part.get_content_charset() or "utf-8"
                fields[name] = {"value": content.decode(charset, errors="replace")}
        return fields



    def editing_source_from_payload(self, payload):
        source_type = str(payload.get("sourceType") or "asset").strip().lower()
        db = enrich_series(enrich_assets(load_db()))
        if source_type == "series" or payload.get("seriesId"):
            series = find_series_by_id(db, payload.get("seriesId", ""))
            if not series:
                raise ValueError("素材或剧集不存在")
            episodes = selected_series_episodes(series, payload.get("episodeLimit") or payload.get("episodeCount") or 0)
            if not episodes:
                raise ValueError("该剧集没有可分析的单集")
            return {"type": "series", "db": db, "series": series, "items": episodes}
        asset = find_asset_by_id(db, payload.get("assetId", ""))
        if not asset:
            raise ValueError("素材或剧集不存在")
        return {"type": "asset", "db": db, "asset": asset, "items": [asset]}

    def handle_editing_storylines(self):
        payload = self.read_json_body()
        api_key = payload.get("apiKey", "")
        try:
            source = self.editing_source_from_payload(payload)
            if source["type"] == "series":
                episode_limit = payload.get("episodeLimit") or payload.get("episodeCount") or 0
                context = build_series_editing_context(source["series"], episode_limit)
                generated = generate_editing_storylines_from_context(context, api_key)
                storylines = save_series_storylines(source["db"], source["series"].get("id"), generated, episode_limit)
                send_json(self, {"sourceType": "series", "seriesId": source["series"].get("id"), "storylines": storylines})
            else:
                storylines = generate_editing_storylines(source["asset"], api_key)
                send_json(self, {"sourceType": "asset", "assetId": source["asset"].get("id"), "storylines": storylines})
        except ValueError as exc:
            send_json(self, {"error": str(exc)}, 400)

    def handle_editing_cutlist(self):
        payload = self.read_json_body()
        api_key = payload.get("apiKey", "")
        storyline = payload.get("storyline") or {}
        storyline_id = str(payload.get("storylineId") or storyline.get("id") or "")
        try:
            source = self.editing_source_from_payload(payload)
            if source["type"] == "series":
                context = build_series_editing_context(source["series"], payload.get("episodeLimit") or payload.get("episodeCount") or 0)
                cutlist = generate_editing_cutlist_from_context(context, storyline, api_key)
                cutlist_path, srt_path = write_cutlist_files(source["items"][0], cutlist)
                first = source["items"][0]
                result = {"sourceType": "series", "seriesId": source["series"].get("id"), "storylineId": storyline_id, "cutlist": cutlist, "cutlistPath": cutlist_path, "srtPath": srt_path, "cutlistUrl": series_episode_url(first.get("id"), os.path.relpath(cutlist_path, first.get("analysisDir"))), "srtUrl": series_episode_url(first.get("id"), os.path.relpath(srt_path, first.get("analysisDir")))}
                saved = update_series_storyline_outputs(source["db"], source["series"].get("id"), storyline_id, {"cutlist": cutlist, "cutlistPath": cutlist_path, "srtPath": srt_path, "cutlistUrl": result["cutlistUrl"], "srtUrl": result["srtUrl"]}) if storyline_id else None
                if saved:
                    result["storyline"] = saved
                send_json(self, result)
            else:
                cutlist = generate_editing_cutlist(source["asset"], storyline, api_key)
                cutlist_path, srt_path = write_cutlist_files(source["asset"], cutlist)
                send_json(self, {"sourceType": "asset", "assetId": source["asset"].get("id"), "cutlist": cutlist, "cutlistUrl": artifact_url_for_path(source["asset"], cutlist_path), "srtUrl": artifact_url_for_path(source["asset"], srt_path)})
        except ValueError as exc:
            send_json(self, {"error": str(exc)}, 400)

    def handle_editing_render_preview(self):
        payload = self.read_json_body()
        cutlist = payload.get("cutlist") or {}
        storyline_id = str(payload.get("storylineId") or "")
        try:
            source = self.editing_source_from_payload(payload)
            if source["type"] == "series":
                preview_path, cutlist_path, srt_path = render_cutlist_preview_from_items(source["items"], cutlist)
                first = source["items"][0]
                result = {"sourceType": "series", "seriesId": source["series"].get("id"), "storylineId": storyline_id, "previewPath": preview_path, "cutlistPath": cutlist_path, "srtPath": srt_path, "previewUrl": series_episode_url(first.get("id"), os.path.relpath(preview_path, first.get("analysisDir"))), "cutlistUrl": series_episode_url(first.get("id"), os.path.relpath(cutlist_path, first.get("analysisDir"))), "srtUrl": series_episode_url(first.get("id"), os.path.relpath(srt_path, first.get("analysisDir")))}
                saved = update_series_storyline_outputs(source["db"], source["series"].get("id"), storyline_id, {"cutlist": cutlist, "previewPath": preview_path, "cutlistPath": cutlist_path, "srtPath": srt_path, "previewUrl": result["previewUrl"], "cutlistUrl": result["cutlistUrl"], "srtUrl": result["srtUrl"]}) if storyline_id else None
                if saved:
                    result["storyline"] = saved
                send_json(self, result)
            else:
                preview_path, cutlist_path, srt_path = render_cutlist_preview(source["asset"], cutlist)
                send_json(self, {"sourceType": "asset", "assetId": source["asset"].get("id"), "previewUrl": artifact_url_for_path(source["asset"], preview_path), "cutlistUrl": artifact_url_for_path(source["asset"], cutlist_path), "srtUrl": artifact_url_for_path(source["asset"], srt_path)})
        except ValueError as exc:
            send_json(self, {"error": str(exc)}, 400)

    def handle_editing_export_jianying(self):
        payload = self.read_json_body()
        cutlist = payload.get("cutlist") or {}
        storyline_id = str(payload.get("storylineId") or "")
        template_path = str(payload.get("templatePath") or "").strip()
        draft_root = str(payload.get("draftRoot") or "").strip()
        try:
            source = self.editing_source_from_payload(payload)
            if source["type"] == "series":
                storylines = source["series"].get("storylines") or []
                story_index = next((idx + 1 for idx, item in enumerate(storylines) if str(item.get("id")) == storyline_id), 1)
                series_name = source["series"].get("title") or '剧集'
                draft_name = str(payload.get("draftName") or f"Ai素材-{series_name}-storyline{story_index}")
                package_dir, zip_path, cutlist_path, srt_path = export_jianying_package_from_items(source["items"], cutlist, template_path, draft_root, draft_name)
                first = source["items"][0]
                result = {"sourceType": "series", "seriesId": source["series"].get("id"), "storylineId": storyline_id, "packageDir": package_dir, "packageUrl": series_episode_url(first.get("id"), os.path.relpath(zip_path, first.get("analysisDir"))), "cutlistUrl": series_episode_url(first.get("id"), os.path.relpath(cutlist_path, first.get("analysisDir"))), "srtUrl": series_episode_url(first.get("id"), os.path.relpath(srt_path, first.get("analysisDir"))), "draftName": os.path.basename(package_dir), "note": '已生成并注册到剪映草稿库。若剪映已打开，请重启剪映后查看新草稿。'}
                saved = update_series_storyline_outputs(source["db"], source["series"].get("id"), storyline_id, {"cutlist": cutlist, "packageDir": package_dir, "packageUrl": result["packageUrl"], "draftName": result["draftName"], "cutlistUrl": result["cutlistUrl"], "srtUrl": result["srtUrl"]}) if storyline_id else None
                if saved:
                    result["storyline"] = saved
                send_json(self, result)
            else:
                asset_name = source["asset"].get("title") or source["asset"].get("sourceName") or '素材'
                draft_name = str(payload.get("draftName") or f"Ai素材-{asset_name}-storyline1")
                package_dir, zip_path, cutlist_path, srt_path = export_jianying_package(source["asset"], cutlist, template_path, draft_root, draft_name)
                send_json(self, {"sourceType": "asset", "assetId": source["asset"].get("id"), "packageDir": package_dir, "packageUrl": artifact_url_for_path(source["asset"], zip_path), "draftName": os.path.basename(package_dir), "cutlistUrl": artifact_url_for_path(source["asset"], cutlist_path), "srtUrl": artifact_url_for_path(source["asset"], srt_path), "note": '已生成并注册到剪映草稿库。若剪映已打开，请重启剪映后查看新草稿。'})
        except ValueError as exc:
            send_json(self, {"error": str(exc)}, 400)


    def handle_prompts_update(self):
        payload = self.read_json_body()
        prompts = save_prompts(payload.get("prompts", {}))
        send_json(self, {"prompts": prompts, "defaults": DEFAULT_PROMPTS, "meta": PROMPT_META})
    def handle_schema_update(self):
        payload = self.read_json_body()
        try:
            if payload.get("action") == "saveLocalization":
                db = set_tag_localization(payload.get("kind", ""), payload.get("category", ""), payload.get("tag", ""), payload.get("locale", "en"), payload.get("name", ""), payload.get("definition", ""))
            elif payload.get("action") == "deleteTag":
                db = delete_schema_tag(payload.get("category", ""), payload.get("tag", ""), payload.get("reason", ""), payload.get("level", 1))
            elif payload.get("action") == "deleteCategory":
                db = delete_schema_category(payload.get("category", ""), payload.get("reason", ""))
            elif payload.get("action") == "moveTag":
                db = move_schema_tag(payload.get("sourceCategory", ""), payload.get("targetCategory", ""), payload.get("tag", ""))
            elif payload.get("action") == "mergeTag":
                db = merge_schema_tag(payload.get("category", ""), payload.get("sourceTag", ""), payload.get("targetTag", ""), payload.get("level", 1), payload.get("reason", ""))
            elif payload.get("action") == "transferTag":
                db = transfer_schema_tag(payload.get("sourceCategory", ""), payload.get("tag", ""), payload.get("sourceLevel", 1), payload.get("targetCategory", ""), payload.get("targetLevel", 1))
            elif payload.get("action") == "saveCategory":
                db = set_category_definition(payload.get("category", ""), payload.get("definition", ""))
            elif payload.get("action") == "setCategoryLevels":
                db = set_category_levels(payload.get("category", ""), payload.get("levels", 1))
            elif payload.get("action") == "setCategoryLevelName":
                db = set_category_level_name(payload.get("category", ""), payload.get("level", 1), payload.get("name", ""))
            elif payload.get("action") == "setCategoryOrder":
                db = set_category_order(payload.get("order", []))
            elif payload.get("action") == "renameCategory":
                db = rename_schema_category(payload.get("category", ""), payload.get("newCategory", ""))
            elif payload.get("action") == "renameTag":
                db = rename_schema_tag(payload.get("category", ""), payload.get("tag", ""), payload.get("newTag", ""), payload.get("level", 1))
            else:
                db = add_schema_tag(payload.get("category", ""), payload.get("tag", ""), payload.get("definition", ""), payload.get("level", 1))
                if payload.get("tag") is not None and "definition" in payload:
                    db = set_tag_definition(payload.get("category", ""), payload.get("tag", ""), payload.get("definition", ""), payload.get("level", 1))
        except ValueError as exc:
            send_json(self, {"error": str(exc)}, 400)
            return
        send_json(self, schema_response(db))

    def handle_series_resume(self):
        payload = self.read_json_body()
        api_key = payload.get("apiKey", "")
        if not str(api_key or "").strip():
            send_json(self, {"error": "请先输入模型 Key，再继续分析剧集。"}, 400)
            return
        series_id = str(payload.get("seriesId") or "").strip()
        episode_id = str(payload.get("episodeId") or "").strip()
        db = enrich_series(load_db())
        target_series = next((item for item in db.get("series", []) if item.get("id") == series_id), None)
        if not target_series:
            send_json(self, {"error": "剧集不存在。"}, 404)
            return
        episodes = target_series.get("episodes", [])
        if episode_id:
            episodes = [ep for ep in episodes if ep.get("id") == episode_id]
        tasks = []
        for ep in episodes:
            if series_episode_complete(ep):
                continue
            tasks.append(create_series_pipeline_task(target_series.get("id"), ep.get("id"), api_key))
        send_json(self, {"seriesId": target_series.get("id"), "tasks": tasks, "count": len(tasks)})
    def handle_series_upload(self):
        ensure_dirs()
        form = self.read_multipart()
        upload = form.get("video")
        api_key = form.get("apiKey", {}).get("value", "")
        series_title = str(form.get("seriesTitle", {}).get("value", "") or "").strip()
        episode_no_raw = str(form.get("episodeNo", {}).get("value", "") or "").strip()
        if not upload or not upload.get("filename"):
            send_json(self, {"error": "请选择要上传的单集视频"}, 400)
            return
        if not series_title:
            series_title = os.path.splitext(os.path.basename(upload["filename"]))[0].split("-")[0] or "未命名剧集"
        try:
            episode_no = int(episode_no_raw or 0)
        except Exception:
            episode_no = 0
        db = load_db()
        series = find_or_create_series(db, series_title)
        if episode_no <= 0:
            episode_no = max([int(ep.get("episodeNo") or 0) for ep in series.get("episodes", [])] or [0]) + 1
        safe_title = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", series_title).strip("-") or "series"
        episode_id = f"episode-{int(time.time() * 1000)}-E{episode_no:02d}"
        folder = os.path.join(series.get("folder") or os.path.join(SERIES_DIR, series.get("id")), f"E{episode_no:02d}-{safe_title[:18]}")
        os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(upload["filename"])[1] or ".mp4"
        video_path = os.path.join(folder, f"source{ext}")
        with open(video_path, "wb") as f:
            f.write(upload["content"])
        analysis_dir = os.path.join(folder, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        episode = {"id": episode_id, "seriesId": series.get("id"), "episodeNo": episode_no, "title": f"{series_title} 第{episode_no}集", "sourceName": upload["filename"], "videoPath": video_path, "analysisDir": analysis_dir, "status": "等待分析", "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"), "skillResult": {"ok": False, "warnings": []}, "artifacts": collect_episode_artifacts({"id": episode_id, "analysisDir": analysis_dir})}
        series.setdefault("episodes", []).append(episode)
        save_db(db)
        task = create_series_pipeline_task(series.get("id"), episode_id, api_key)
        send_json(self, {"series": series, "episode": episode, "task": task})

    def handle_upload(self):
        ensure_dirs()
        form = self.read_multipart()
        upload = form.get("video")
        api_key = form.get("apiKey", {}).get("value", "")
        if not upload or not upload.get("filename"):
            send_json(self, {"error": "请上传视频文件。"}, 400)
            return
        title = os.path.splitext(os.path.basename(upload["filename"]))[0]
        asset_id, folder = create_asset(title, upload["filename"])
        ext = os.path.splitext(upload["filename"])[1] or ".mp4"
        video_path = os.path.join(folder, f"source{ext}")
        with open(video_path, "wb") as f:
            f.write(upload["content"])

        analysis_dir = os.path.join(folder, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        asset = {
            "id": asset_id,
            "title": title,
            "sourceName": upload["filename"],
            "videoPath": video_path,
            "analysisDir": analysis_dir,
            "status": "已加入拉片任务队列",
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "skillResult": {"ok": False, "warnings": []},
            "audioPath": "",
            "storyboardPath": "",
            "tags": {},
            "confirmed": False,
        }
        db = load_db()
        db["assets"].insert(0, asset)
        save_db(db)
        task = create_pipeline_task(asset, api_key)
        send_json(self, {"asset": asset, "task": task})

    def handle_transcribe_audio(self):
        payload = self.read_json_body()
        asset_id = payload.get("assetId", "")
        api_key = payload.get("apiKey", "")
        method = str(payload.get("method", "model") or "model").strip().lower()
        language = str(payload.get("language", "auto") or "auto").strip().lower()
        local_model = str(payload.get("localModel", "") or "").strip()
        if not asset_id:
            send_json(self, {"error": "缺少素材 ID。"}, 400)
            return
        db = load_db()
        for asset in db.get("assets", []):
            if asset.get("id") == asset_id:
                try:
                    if method in ("local", "local_asr", "asr"):
                        transcript_path = transcribe_asset_local_asr(asset, language, local_model, api_key)
                    else:
                        transcript_path = transcribe_asset_audio(asset, api_key)
                except ValueError as exc:
                    send_json(self, {"error": str(exc)}, 400)
                    return
                asset["artifacts"] = collect_artifacts(asset)
                asset["status"] = "音频转写完成，待生成报告"
                asset["transcriptPath"] = transcript_path
                asset["transcriptMethod"] = "本地ASR" if method in ("local", "local_asr", "asr") else "大模型"
                asset["transcriptLanguage"] = language
                asset["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
                save_db(db)
                send_json(self, {"asset": asset, "transcriptPath": transcript_path})
                return
        send_json(self, {"error": "素材不存在。"}, 404)
    def handle_generate_report(self):
        payload = self.read_json_body()
        asset_id = payload.get("assetId", "")
        api_key = payload.get("apiKey", "")
        if not asset_id:
            send_json(self, {"error": "缺少素材 ID。"}, 400)
            return
        db = load_db()
        for asset in db.get("assets", []):
            if asset.get("id") == asset_id:
                try:
                    report_path = generate_ai_report(asset, api_key)
                except ValueError as exc:
                    send_json(self, {"error": str(exc)}, 400)
                    return
                asset["artifacts"] = collect_artifacts(asset)
                asset["status"] = "双语报告已生成，待自动打标"
                asset["sourceReportPath"] = report_path
                asset["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
                save_db(db)
                send_json(self, {"asset": asset, "reportPath": report_path})
                return
        send_json(self, {"error": "素材不存在。"}, 404)

    def handle_auto_tag(self):
        content_type = self.headers.get("Content-Type", "")
        text = ""
        report_path = ""
        asset_id = ""
        db = None
        target_asset = None

        if content_type.startswith("multipart/form-data"):
            form = self.read_multipart()
            asset_id = form.get("assetId", {}).get("value", "")
            api_key = form.get("apiKey", {}).get("value", "")
            upload = form.get("report")
            if not upload or not upload.get("filename"):
                send_json(self, {"error": "请上传 MD 格式拉片报告。"}, 400)
                return
            filename = upload["filename"]
            if not filename.lower().endswith(".md"):
                send_json(self, {"error": "拉片报告仅支持 .md 格式。"}, 400)
                return
            text = upload["content"].decode("utf-8-sig", errors="replace")
            if asset_id:
                db = load_db()
                target_asset = next((item for item in db.get("assets", []) if item.get("id") == asset_id), None)
                if not target_asset:
                    send_json(self, {"error": "绑定素材不存在。"}, 404)
                    return
                analysis_dir = target_asset.get("analysisDir")
                if not analysis_dir or not os.path.isdir(analysis_dir):
                    send_json(self, {"error": "绑定素材还没有可用 analysis 目录。"}, 400)
                    return
                safe_name = filename if re.match(r"ai_video_analysis(_visual)?_bilingual\.md$", filename.lower()) else "AI_video_analysis_bilingual.md"
                report_path = os.path.join(analysis_dir, safe_name)
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(text)
        else:
            payload = self.read_json_body()
            text = payload.get("reportText", "")
            report_path = payload.get("reportPath", "")
            asset_id = payload.get("assetId", "")
            api_key = payload.get("apiKey", "")
            if report_path:
                lower_report = os.path.basename(report_path).lower()
                if not re.match(r"ai_video_analysis(_visual)?_bilingual\.md$", lower_report):
                    send_json(self, {"error": "请选择正式双语拉片报告：AI_video_analysis_bilingual.md 或 AI_video_analysis_visual_bilingual.md。当前文件不能用于自动打标。"}, 400)
                    return
                if not os.path.exists(report_path):
                    send_json(self, {"error": "拉片报告路径不存在。"}, 400)
                    return
                with open(report_path, "r", encoding="utf-8-sig") as f:
                    text = f.read()

        if not text.strip():
            send_json(self, {"error": "请上传或选择拉片报告。"}, 400)
            return

        ai_definitions = {}
        if api_key:
            tags, evidence, summary, ai_definitions = ai_tag_report(text, merged_schema(), api_key)
            merge_ai_tag_definitions(tags, ai_definitions)
        else:
            tags, evidence = auto_tag(text)
            summary = summarize_report(text)
        result = {
            "tags": tags,
            "evidence": evidence,
            "summary": summary,
            "sourceReportPath": report_path,
            "model": AI_MODEL if api_key else "rule-fallback",
            "tagDefinitions": ai_definitions,
        }
        if asset_id:
            if db is None:
                db = load_db()
                target_asset = next((item for item in db.get("assets", []) if item.get("id") == asset_id), None)
            if target_asset:
                target_asset["tags"] = tags
                target_asset["autoTagSummary"] = result["summary"]
                target_asset["sourceReportPath"] = report_path
                target_asset["artifacts"] = collect_artifacts(target_asset)
                if target_asset["artifacts"].get("reports"):
                    target_asset["status"] = "双语报告已上传，待人工确认"
                save_db(db)
        send_json(self, result)

    def handle_confirm(self):
        payload = self.read_json_body()
        tags = normalize_tags(payload.get("tags", {}))
        asset_id = payload.get("assetId")
        db = load_db()
        asset = None
        if asset_id:
            for item in db["assets"]:
                if item["id"] == asset_id:
                    asset = item
                    break
        if not asset:
            title = payload.get("title") or "未命名素材"
            asset_id, folder = create_asset(title)
            asset = {
                "id": asset_id,
                "title": title,
                "sourceName": "",
                "videoPath": "",
                "analysisDir": folder,
                "status": "仅标签入库",
                "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            db["assets"].insert(0, asset)
        merge_ai_tag_definitions(tags, payload.get("tagDefinitions", {}))
        db = load_db()
        if asset_id:
            asset = next((item for item in db.get("assets", []) if item.get("id") == asset_id), asset)
        elif not any(item.get("id") == asset.get("id") for item in db.get("assets", [])):
            db.setdefault("assets", []).insert(0, asset)
        asset["tags"] = tags

        asset["note"] = payload.get("note", "")
        asset["autoTagSummary"] = payload.get("summary", asset.get("autoTagSummary", ""))
        asset["confirmed"] = True
        asset["confirmedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
        asset["status"] = "已入库"
        save_db(db)
        mark_asset_tasks_confirmed(asset.get("id"))
        send_json(self, {"asset": asset, "dbPath": DB_PATH})

    def handle_delete_asset(self, asset_id):
        db = load_db()
        assets = db.get("assets", [])
        target = next((item for item in assets if item.get("id") == asset_id), None)
        if not target:
            send_json(self, {"error": "素材不存在。"}, 404)
            return

        folder = os.path.abspath(os.path.join(ASSET_DIR, asset_id))
        if os.path.exists(folder):
            if not is_within(ASSET_DIR, folder):
                send_json(self, {"error": "删除路径不在素材目录内，已取消。"}, 400)
                return
            shutil.rmtree(folder)

        db["assets"] = [item for item in assets if item.get("id") != asset_id]
        save_db(db)
        send_json(self, {"ok": True, "deletedId": asset_id})
    def handle_update_asset(self, asset_id):
        payload = self.read_json_body()
        db = load_db()
        for asset in db["assets"]:
            if asset["id"] == asset_id:
                if "title" in payload:
                    asset["title"] = payload["title"]
                if "tags" in payload:
                    asset["tags"] = normalize_tags(payload["tags"])
                if "note" in payload:
                    asset["note"] = payload["note"]
                asset["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
                save_db(db)
                send_json(self, {"asset": asset})
                return
        send_json(self, {"error": "素材不存在。"}, 404)


def local_lan_urls(port):
    urls = []
    try:
        import socket
        hostname = socket.gethostname()
        for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = sockaddr[0]
            if ip and not ip.startswith("127.") and ip not in urls:
                urls.append(ip)
    except Exception:
        pass
    return [f"http://{ip}:{port}" for ip in urls]
if __name__ == "__main__":
    ensure_dirs()
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "0.0.0.0")
    server = ThreadingHTTPServer((host, port), AppHandler)
    local_url = f"http://127.0.0.1:{port}"
    lan_urls = local_lan_urls(port)
    print(f"素材打标前端已启动：{local_url}")
    if host in ("0.0.0.0", ""):
        if lan_urls:
            print("局域网访问地址：" + "  ".join(lan_urls))
        else:
            print("局域网访问地址：请查看本机 IPv4 后访问 http://<本机IP>:%s" % port)
    server.serve_forever()

































































































































