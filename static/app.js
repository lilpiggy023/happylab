let schema = {};
let tagDefinitions = {};
let tagLocalization = { categories: {}, tags: {} };
let hierarchicalSchema = {};
let categoryLevels = {};
let categoryLevelNames = {};
let categoryOrder = [];
let categoryDefinitions = {};
let tagGraveyard = [];
let graveyardCollapsed = false;
let assets = [];
let seriesLibrary = [];
let editingSourceType = "asset";
let editingSeriesId = "";
let editingEpisodeLimit = 3;
let assetNameSearchQuery = "";
let assetTagSearchQuery = "";
let selectedAssetTagFilter = null;
let assetTagCollapsedCategories = new Set();
let pipelineTasks = [];
let taskPollTimer = null;
let currentTags = {};
let currentTagDefinitions = {};
let currentSummary = "";
let promptConfig = { prompts: {}, defaults: {}, meta: {} };
let editingDefinition = null;
let editingPreviewTag = null;
let tagDragState = null;
let categoryDragState = null;
let pendingTranscribeAssetId = "";
let editingAssetId = "";
let editingStorylines = [];
let selectedStorylineId = "";
let editingCutlist = null;
let activeSeriesId = "";
let activeSeriesStorylineId = "";
let seriesDetailEpisodeLimit = 3;
let currentLocale = localStorage.getItem("materialTaggingLocale") || "zh";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));


const I18N = {
  zh: {
    localeName: "中文",
    appTitle: "素材打标台",
    appSubtitle: "拉片、自动打标、人工确认、入库",
    language: "语言",
    navAssets: "素材库",
    navSeries: "剧集库",
    navAutoTag: "自动打标",
    navLibrary: "标签库",
    navPrompt: "Prompt",
    modelKey: "模型 Key",
    modelKeyPlaceholder: "输入 PocketCity Key",
    needModelKey: "请先输入模型Key",
    model: "模型",
    endpoint: "接口",
    edit: "编辑",
    noPreview: "暂无预览",
    noStoryboard: "暂无 storyboard",
    noFrames: "暂无抽帧",
    noFiles: "暂无文件",
    noSubtitles: "暂无字幕，请先转写音频",
    noEpisodes: "暂无单集",
    noTags: "暂无标签",
    noDeletedTags: "暂无已删除标签。",
    noConfirmedRecords: "还没有确认入库的标签记录。",
    noAssets: "还没有素材。点击右上角“上传素材并分析”开始沉淀第一条。",
    noSeriesEmpty: "还没有剧集，点击右上角上传单集视频",
    enterSeries: "进入剧集",
    resumeAnalysis: "继续分析",
    pendingReview: "待确认",
    hasSubtitles: "有字幕",
    pendingTranscribe: "待转写",
    hasReport: "有报告",
    pendingReport: "待报告",
    report: "报告",
    audio: "音频",
    artifacts: "产物",
    other: "其他",
    frames: "抽帧",
    subtitles: "字幕",
    retranscribe: "重新转写",
    transcribeAudio: "转写音频",
    readingSubtitles: "正在读取字幕...",
    files: "文件",
    uploadMd: "上传 MD",
    unboundNewAsset: "不绑定，作为新素材入库",
    reportPathFilled: "已填入该素材的正式双语拉片报告路径",
    needGenerateReportFromTranscript: "该素材已完成音频转写，请先生成 AI_video_analysis_bilingual.md",
    needTranscribeFirst: "该素材还没有音频转写，请先在素材库页或当前素材区点击音频转写",
    notGenerated: "未生成",
    notTranscribed: "未转写",
    read: "已读取",
    optional: "可选",
    frameCount: "{count} 帧",
    noCategories: "还没有标签，先添加一个一级标签。",
    noDefinition: "暂无定义",
    missingLocalization: "缺少当前语言本地化，当前显示中文",
    missingLocalizationShort: "中文",
    showingFallbackLocalization: "缺少{locale}本地化，当前显示中文",
    currentChinese: "当前展示中文，点击切换原文",
    currentOriginal: "当前展示原文，点击切换中文",
    transcriptEmpty: "字幕文件为空",
    transcriptReadFailed: "字幕预览读取失败",
    assetStatusConfirmed: "已入库",
    assetStatusReportReady: "双语报告已生成，待自动打标",
    assetStatusTranscriptReady: "音频转写完成，待生成报告",
    assetStatusPrepReady: "拉片完成，待音频转写",
    episodeStatusReportReady: "AI 报告已生成",
    episodeStatusTranscriptReady: "字幕转写完成，待生成报告",
    episodeStatusPrepReady: "抽帧与音频完成，待转写字幕",
    waitingAnalysis: "待分析",
    unboundAsset: "未绑定素材",
    assetFallback: "素材",
    analyzingFirstEpisodes: "分析前 {count} 集",
    savedToLibrary: "已入库：{title}",
    levelSetting: "层级",
    changeLevelNameTitle: "点击修改层级名",
    categoryPlaceholder: "例如：叙事节奏",
    tagNamePlaceholder: "例如：前3秒强反转",
    tagDefinitionPlaceholder: "标签定义，例如：前3秒出现足够明确的剧情反转或身份落差",
    processing: "处理中...",
    submitting: "提交中...",
    generating: "生成中...",
    transcribing: "转写中...",
    seriesEyebrow: "剧集库",
    seriesTitle: "短剧剧集管理",
    seriesDesc: "上传多集短剧，供智能剪辑跨集分析使用，不会沉淀到素材库。",
    uploadSeries: "上传剧集单集并分析",
    uploadSeriesTitle: "上传剧集单集",
    uploadSeriesDesc: "填写剧名和集数，系统会解析抽帧、转写字幕并生成 AI 拉片报告。",
    seriesName: "剧名",
    episodeNo: "集数",
    chooseEpisodeVideo: "选择或拖入单集视频",
    seriesDropHint: "上传后进入剧集库，不进入素材库",
    startEpisodeAnalysis: "开始分析单集",
    seriesDetailEyebrow: "剧集库 / 智能剪辑",
    seriesDetailTitle: "剧集详情",
    seriesDetailDesc: "单集、故事线、剪辑清单和导出产物会长期保留在这部剧下。",
    backToSeries: "返回剧集库",
    episodes: "单集",
    episodesDesc: "按集数顺序展示已上传并分析的剧集素材。",
    selectSeries: "请选择剧集",
    storylines: "已确认故事线",
    storylinesDesc: "生成后会永久保留在当前剧集下。",
    episodeLimit: "分析前 N 集",
    generateStoryline: "生成投流故事线",
    noStorylines: "还没有故事线",
    cutlistExport: "剪辑清单与导出",
    cutlistExportDesc: "剪辑清单、预览视频和剪映草稿包会自动保存。",
    generateCutlist: "生成剪辑清单",
    regenerateCutlist: "重新生成剪辑清单",
    selectStoryline: "请选择故事线",
    renderPreview: "渲染预览视频",
    exportJianying: "导出剪映草稿包",
    assetEyebrow: "素材库",
    assetTitle: "统一素材沉淀",
    assetName: "素材名",
    tag: "标签",
    assetNamePlaceholder: "输入素材名",
    tagPlaceholder: "输入或选择标签",
    clear: "清空",
    uploadAnalyze: "上传素材并分析",
    uploadAnalyzeDesc: "点击开始后自动执行解析抽帧拆音频、转写并翻译字幕、AI 拉片和自动打标。",
    chooseVideo: "选择或拖入视频",
    videoHint: "支持 mp4 / mov / mkv 等常见格式",
    startAnalysis: "开始拉片",
    autoTagTitle: "根据拉片信息自动打标",
    autoTagDesc: "可选择本机报告路径，或上传 .md 拉片报告；填写 Key 后会使用模型进行 AI 打标。",
    currentAsset: "当前素材",
    currentAssetDesc: "选择素材后展示缩略图和拉片产物。",
    noBoundAsset: "未绑定素材",
    bindAsset: "绑定素材",
    tagPreview: "标签预览",
    waitingReport: "等待拉片信息",
    confirmLibrary: "确认入库",
    note: "人工备注",
    notePlaceholder: "记录投放观察、修改建议或审核注意点",
    libraryTitle: "标签库",
    libraryDesc: "维护一级、二级标签，并查看人工确认入库后的标签记录。",
    refresh: "刷新",
    schemaTitle: "标签体系维护",
    schemaDesc: "新增标签和定义会同步到自动打标页，并提供给 AI 打标模型。",
    addCategory: "新增一级标签",
    addCategoryBtn: "添加一级",
    addTag: "新增子标签",
    addTagBtn: "添加子标签",
    graveyard: "标签墓地",
    graveyardDesc: "已删除的一级、二级标签会保留在这里，AI 自动打标会参考并避免复用。",
    collapse: "收起",
    libraryRecords: "已入库素材标签",
    libraryRecordsDesc: "人工确认入库后的素材记录会展示在这里。",
    promptTitle: "Skill / Prompt 配置",
    promptDesc: "查看或修改 AI 拉片与 AI 打标使用的模型提示词。",
    resetDefault: "恢复默认",
    saveConfig: "保存配置",
    systemRole: "系统角色",
    userPrompt: "用户 Prompt",
    reportPrompt: "AI 拉片 Prompt",
    reportPromptDesc: "用于生成正式双语 Markdown 拉片报告。可用占位符：{context_json}",
    tagPrompt: "AI 打标 Prompt",
    tagPromptDesc: "用于根据拉片报告输出标签 JSON。可用占位符：{schema_json}、{report_text}",
    storylinePrompt: "投流故事线 Prompt",
    storylinePromptDesc: "用于生成剧集投流故事线。可用占位符：{source_context}",
    cutlistPrompt: "剪辑清单 Prompt",
    cutlistPromptDesc: "用于生成可执行时间线。可用占位符：{selected_storyline}、{source_context}",
    transcribePrompt: "音频转写 Prompt",
    transcribePromptDesc: "用于大模型音频转写。",
    translatePrompt: "字幕翻译 Prompt",
    translatePromptDesc: "用于非中文字幕翻译。可用占位符：{transcript_payload}",
    jsonRepairPrompt: "JSON 修复 Prompt",
    jsonRepairPromptDesc: "用于修复模型返回的转写 JSON。可用占位符：{raw_response}",
    transcribeTitle: "音频转写",
    transcribeDesc: "选择转写方式和语种。本地 ASR 不需要模型 Key。",
    transcribeMethod: "转录方式",
    transcribeLanguage: "转录语种",
    localModel: "本地模型目录 / 模型名",
    localAsrHint: "本地 ASR 使用 faster-whisper；如未下载模型，请填写本机模型目录。",
    cancel: "取消",
    startTranscribe: "开始转写",
    editPreviewTag: "编辑预览标签",
    editPreviewTagDesc: "修改只影响当前素材，确认入库后写入标签库。",
    saveChanges: "保存修改",
    editDefinition: "编辑标签定义",
    tagName: "标签名称",
    tagDefinition: "标签定义",
    mergeTo: "合并到",
    confirmMerge: "确认合并",
    targetCategory: "目标一级",
    targetLevel: "目标层级",
    confirmTransfer: "确认转移",
    merge: "合并",
    transfer: "转移",
    delete: "删除",
    save: "保存",
    localAsr: "本地 ASR",
    modelAsr: "大模型",
    autoDetect: "自动识别",
    chinese: "中文",
    english: "英语",
    indonesian: "印尼语",
    uploadQueued: "已加入全流程拉片任务",
    selectOrDropVideo: "选择或拖入视频",
    chooseVideoFile: "请拖入视频文件",
    videoAdded: "已添加视频，点击开始拉片",
    autoTagDone: "自动打标完成",
    tagsConfirmed: "标签已确认入库",
    generatedTags: "已生成标签",
    tagging: "正在打标...",
    reportSelected: "已选择拉片报告：{name}",
    assetDeleted: "素材已删除",
    deletingAsset: "正在删除素材...",
    transcribeDone: "音频转写已完成",
    reportGenerating: "正在基于字幕、storyboard 和关键帧生成双语拉片报告...",
    reportDone: "双语拉片报告已生成",
    generateReport: "生成报告",
    regenerateReport: "重新生成报告",
    invalidVideoFile: "请选择视频文件",
    episodeUploading: "正在上传单集并加入分析任务...",
    episodeQueued: "单集已加入剧集分析任务",
    resumeSeries: "正在把未完成单集加入继续分析任务...",
    noResumeEpisode: "该剧集没有需要继续分析的单集",
    noResumeEpisodeStatus: "没有需要继续分析的单集",
    noSeries: "剧集不存在",
    storylinesSaving: "AI 正在生成并保存投流故事线...",
    storylinesSaved: "故事线已保存到当前剧集",
    cutlistSaving: "AI 正在生成并保存剪辑清单...",
    cutlistSaved: "剪辑清单已保存",
    regenerateGenerating: "重新生成中...",
    rendering: "渲染中...",
    exporting: "导出中...",
    previewSaved: "预览视频已保存，可直接播放",
    jianyingExported: "剪映草稿包已导出",
    generateCutlistHint: "点击“生成剪辑清单”后展示时间线",
    promptSaving: "正在保存 Prompt...",
    promptSaved: "Prompt 配置已保存",
    resetPromptConfirm: "确定恢复默认 Prompt 吗？当前编辑内容会被覆盖。",
    assetNamePrompt: "素材名称",
    untitledAsset: "未命名素材"
  },
  en: {
    localeName: "English",
    appTitle: "Material Tagging Desk",
    appSubtitle: "Video analysis, auto tagging, review, library",
    language: "Language",
    navAssets: "Assets",
    navSeries: "Series",
    navAutoTag: "Auto Tagging",
    navLibrary: "Tag Library",
    navPrompt: "Prompt",
    modelKey: "Model Key",
    modelKeyPlaceholder: "Enter PocketCity Key",
    needModelKey: "Please enter a model key first",
    model: "Model",
    endpoint: "Endpoint",
    edit: "Edit",
    noPreview: "No preview",
    noStoryboard: "No storyboard",
    noFrames: "No frames yet",
    noFiles: "No files yet",
    noSubtitles: "No subtitles yet. Transcribe audio first.",
    noEpisodes: "No episodes",
    noTags: "No tags",
    noDeletedTags: "No deleted tags yet.",
    noConfirmedRecords: "No confirmed tag records yet.",
    noAssets: "No assets yet. Click Upload Asset & Analyze to add the first one.",
    noSeriesEmpty: "No series yet. Upload an episode from the top right.",
    enterSeries: "Open Series",
    resumeAnalysis: "Resume Analysis",
    pendingReview: "Pending Review",
    hasSubtitles: "Subtitles Ready",
    pendingTranscribe: "Pending Transcription",
    hasReport: "Report Ready",
    pendingReport: "Pending Report",
    report: "Report",
    audio: "Audio",
    artifacts: "Artifacts",
    other: "Other",
    frames: "Frames",
    subtitles: "Subtitles",
    retranscribe: "Retranscribe",
    transcribeAudio: "Transcribe Audio",
    readingSubtitles: "Reading subtitles...",
    files: "Files",
    uploadMd: "Upload MD",
    unboundNewAsset: "Do not bind; save as a new asset",
    reportPathFilled: "The formal bilingual report path has been filled for this asset",
    needGenerateReportFromTranscript: "Audio transcription is complete. Please generate AI_video_analysis_bilingual.md first.",
    needTranscribeFirst: "This asset has not been transcribed yet. Transcribe audio from the Asset Library or Current Asset area first.",
    notGenerated: "Not generated",
    notTranscribed: "Not transcribed",
    read: "Loaded",
    optional: "Optional",
    frameCount: "{count} frames",
    noCategories: "No tags yet. Add a primary tag first.",
    noDefinition: "No definition",
    missingLocalization: "Missing localization for the selected language; showing Chinese",
    missingLocalizationShort: "ZH",
    showingFallbackLocalization: "Missing {locale} localization; showing Chinese",
    currentChinese: "Showing Chinese. Click to switch to original.",
    currentOriginal: "Showing original. Click to switch to Chinese.",
    transcriptEmpty: "Subtitle file is empty",
    transcriptReadFailed: "Failed to read subtitle preview",
    assetStatusConfirmed: "In Library",
    assetStatusReportReady: "Bilingual report ready, pending auto-tagging",
    assetStatusTranscriptReady: "Transcription ready, pending report",
    assetStatusPrepReady: "Analysis assets ready, pending transcription",
    episodeStatusReportReady: "AI report ready",
    episodeStatusTranscriptReady: "Subtitles ready, pending report",
    episodeStatusPrepReady: "Frames and audio ready, pending transcription",
    waitingAnalysis: "Waiting for analysis",
    unboundAsset: "No asset selected",
    assetFallback: "Asset",
    analyzingFirstEpisodes: "Analyzing first {count} episodes",
    savedToLibrary: "Saved to library: {title}",
    levelSetting: "Levels",
    changeLevelNameTitle: "Click to rename level",
    categoryPlaceholder: "e.g. Narrative Pace",
    tagNamePlaceholder: "e.g. Strong reversal in first 3 seconds",
    tagDefinitionPlaceholder: "Tag definition, e.g. a clear plot reversal or identity gap appears in the first 3 seconds",
    processing: "Processing...",
    submitting: "Submitting...",
    generating: "Generating...",
    transcribing: "Transcribing...",
    seriesEyebrow: "Series",
    seriesTitle: "Short Drama Series",
    seriesDesc: "Upload multi-episode dramas for cross-episode AI editing analysis. They will not enter the asset library.",
    uploadSeries: "Upload Episode & Analyze",
    uploadSeriesTitle: "Upload Episode",
    uploadSeriesDesc: "Enter the series title and episode number. The system will extract frames, transcribe subtitles, and generate an AI report.",
    seriesName: "Series Title",
    episodeNo: "Episode No.",
    chooseEpisodeVideo: "Choose or drop episode video",
    seriesDropHint: "Saved to Series Library, not Asset Library",
    startEpisodeAnalysis: "Analyze Episode",
    seriesDetailEyebrow: "Series / Smart Editing",
    seriesDetailTitle: "Series Detail",
    seriesDetailDesc: "Episodes, storylines, cutlists, and exports are kept under this series.",
    backToSeries: "Back to Series",
    episodes: "Episodes",
    episodesDesc: "Uploaded and analyzed episodes are shown in order.",
    selectSeries: "Select a series",
    storylines: "Confirmed Storylines",
    storylinesDesc: "Generated storylines are kept permanently under this series.",
    episodeLimit: "Analyze First N Episodes",
    generateStoryline: "Generate Ad Storylines",
    noStorylines: "No storylines yet",
    cutlistExport: "Cutlist & Export",
    cutlistExportDesc: "Cutlists, preview videos, and Jianying drafts are saved automatically.",
    generateCutlist: "Generate Cutlist",
    regenerateCutlist: "Regenerate Cutlist",
    selectStoryline: "Select a storyline",
    renderPreview: "Render Preview",
    exportJianying: "Export Jianying Draft",
    assetEyebrow: "Assets",
    assetTitle: "Unified Asset Library",
    assetName: "Asset Name",
    tag: "Tag",
    assetNamePlaceholder: "Search asset name",
    tagPlaceholder: "Type or select tags",
    clear: "Clear",
    uploadAnalyze: "Upload Asset & Analyze",
    uploadAnalyzeDesc: "After starting, the system will extract frames/audio, transcribe and translate subtitles, generate an AI report, and auto-tag the asset.",
    chooseVideo: "Choose or drop video",
    videoHint: "Supports mp4 / mov / mkv and common formats",
    startAnalysis: "Start Analysis",
    autoTagTitle: "Auto Tag from Analysis Report",
    autoTagDesc: "Select a local report path or upload a .md report. Enter a key to run AI tagging.",
    currentAsset: "Current Asset",
    currentAssetDesc: "Thumbnails and generated files appear after selecting an asset.",
    noBoundAsset: "No asset selected",
    bindAsset: "Bind Asset",
    tagPreview: "Tag Preview",
    waitingReport: "Waiting for report",
    confirmLibrary: "Confirm to Library",
    note: "Manual Notes",
    notePlaceholder: "Record launch observations, edit suggestions, or review notes",
    libraryTitle: "Tag Library",
    libraryDesc: "Maintain primary and sub-tags, and view confirmed asset records.",
    refresh: "Refresh",
    schemaTitle: "Tag System",
    schemaDesc: "New tags and definitions sync to Auto Tagging and are provided to the AI model.",
    addCategory: "Add Primary Tag",
    addCategoryBtn: "Add Primary",
    addTag: "Add Sub-tag",
    addTagBtn: "Add Sub-tag",
    graveyard: "Tag Graveyard",
    graveyardDesc: "Deleted primary and sub-tags stay here. AI tagging uses it as negative reference.",
    collapse: "Collapse",
    libraryRecords: "Confirmed Asset Tags",
    libraryRecordsDesc: "Assets confirmed into the library are shown here.",
    promptTitle: "Skill / Prompt Settings",
    promptDesc: "View or edit prompts used by AI analysis and AI tagging.",
    resetDefault: "Reset Defaults",
    saveConfig: "Save Settings",
    systemRole: "System Role",
    userPrompt: "User Prompt",
    reportPrompt: "AI Analysis Prompt",
    reportPromptDesc: "Used to generate the formal bilingual Markdown analysis report. Placeholder: {context_json}",
    tagPrompt: "AI Tagging Prompt",
    tagPromptDesc: "Used to output tagging JSON from the report. Placeholders: {schema_json}, {report_text}",
    storylinePrompt: "Ad Storyline Prompt",
    storylinePromptDesc: "Used to generate ad storylines for a series. Placeholder: {source_context}",
    cutlistPrompt: "Cutlist Prompt",
    cutlistPromptDesc: "Used to generate an executable timeline. Placeholders: {selected_storyline}, {source_context}",
    transcribePrompt: "Audio Transcription Prompt",
    transcribePromptDesc: "Used for model-based audio transcription.",
    translatePrompt: "Subtitle Translation Prompt",
    translatePromptDesc: "Used to translate non-Chinese subtitles. Placeholder: {transcript_payload}",
    jsonRepairPrompt: "JSON Repair Prompt",
    jsonRepairPromptDesc: "Used to repair transcription JSON returned by the model. Placeholder: {raw_response}",
    transcribeTitle: "Audio Transcription",
    transcribeDesc: "Choose transcription method and language. Local ASR does not need a model key.",
    transcribeMethod: "Method",
    transcribeLanguage: "Language",
    localModel: "Local Model Path / Name",
    localAsrHint: "Local ASR uses faster-whisper. If the model is not downloaded, enter a local model path.",
    cancel: "Cancel",
    startTranscribe: "Start Transcription",
    editPreviewTag: "Edit Preview Tags",
    editPreviewTagDesc: "Changes only affect the current asset and enter the tag library after confirmation.",
    saveChanges: "Save Changes",
    editDefinition: "Edit Tag Definition",
    tagName: "Tag Name",
    tagDefinition: "Tag Definition",
    mergeTo: "Merge To",
    confirmMerge: "Confirm Merge",
    targetCategory: "Target Primary",
    targetLevel: "Target Level",
    confirmTransfer: "Confirm Transfer",
    merge: "Merge",
    transfer: "Move",
    delete: "Delete",
    save: "Save",
    localAsr: "Local ASR",
    modelAsr: "Model",
    autoDetect: "Auto Detect",
    chinese: "Chinese",
    english: "English",
    indonesian: "Indonesian",
    uploadQueued: "Added to full analysis queue",
    selectOrDropVideo: "Choose or drop video",
    chooseVideoFile: "Please drop a video file",
    videoAdded: "Video added. Click Start Analysis",
    autoTagDone: "Auto tagging completed",
    tagsConfirmed: "Tags confirmed to library",
    generatedTags: "Tags generated",
    tagging: "Tagging...",
    reportSelected: "Report selected: {name}",
    assetDeleted: "Asset deleted",
    deletingAsset: "Deleting asset...",
    transcribeDone: "Audio transcription completed",
    reportGenerating: "Generating bilingual report from subtitles, storyboard, and keyframes...",
    reportDone: "Bilingual analysis report generated",
    generateReport: "Generate Report",
    regenerateReport: "Regenerate Report",
    invalidVideoFile: "Please select a video file",
    episodeUploading: "Uploading episode and adding it to the analysis queue...",
    episodeQueued: "Episode added to analysis queue",
    resumeSeries: "Adding unfinished episodes back to the analysis queue...",
    noResumeEpisode: "No unfinished episodes need analysis",
    noResumeEpisodeStatus: "No episodes need analysis",
    noSeries: "Series does not exist",
    storylinesSaving: "AI is generating and saving ad storylines...",
    storylinesSaved: "Storylines saved to this series",
    cutlistSaving: "AI is generating and saving the cutlist...",
    cutlistSaved: "Cutlist saved",
    regenerateGenerating: "Regenerating...",
    rendering: "Rendering...",
    exporting: "Exporting...",
    previewSaved: "Preview video saved and ready to play",
    jianyingExported: "Jianying draft exported",
    generateCutlistHint: "Timeline appears after generating a cutlist",
    promptSaving: "Saving Prompt...",
    promptSaved: "Prompt settings saved",
    resetPromptConfirm: "Reset to default prompts? Current edits will be overwritten.",
    assetNamePrompt: "Asset Name",
    untitledAsset: "Untitled Asset"
  }
};

function t(key, fallback = "") {
  return key.split(".").reduce((obj, part) => obj?.[part], I18N[currentLocale]) || fallback || key;
}

function formatText(key, values = {}, fallback = "") {
  let text = t(key, fallback);
  Object.entries(values).forEach(([name, value]) => {
    text = text.replaceAll(`{${name}}`, value);
  });
  return text;
}

function countText(count) {
  return currentLocale === "en" ? `${count} item${Number(count) === 1 ? "" : "s"}` : `${count} 条`;
}

function filteredCountText(visible, total) {
  return currentLocale === "en" ? `${visible} / ${total} items` : `${visible} / ${total} 条`;
}

function levelCountText(count) {
  return String(count);
}

function episodeCountText(count) {
  return currentLocale === "en" ? `${count} episode${Number(count) === 1 ? "" : "s"}` : `${count} 集`;
}

function storylineCountText(count) {
  return currentLocale === "en" ? `${count} storyline${Number(count) === 1 ? "" : "s"}` : `${count} 条故事线`;
}

function savedStorylineCountText(count) {
  return currentLocale === "en" ? `${count} saved storyline${Number(count) === 1 ? "" : "s"}` : `${count} 条已保存故事线`;
}

function episodeLabel(no) {
  return currentLocale === "en" ? `Episode ${no || "?"}` : `第 ${no || "?"} 集`;
}

function knownStatusText(status) {
  const map = {
    "已入库": "assetStatusConfirmed",
    "双语报告已生成，待自动打标": "assetStatusReportReady",
    "音频转写完成，待生成报告": "assetStatusTranscriptReady",
    "拉片完成，待音频转写": "assetStatusPrepReady",
    "AI 报告已生成": "episodeStatusReportReady",
    "字幕转写完成，待生成报告": "episodeStatusTranscriptReady",
    "抽帧与音频完成，待转写字幕": "episodeStatusPrepReady",
    "待分析": "waitingAnalysis",
    "等待分析": "waitingAnalysis",
  };
  return map[status] ? t(map[status]) : status;
}

function setText(selector, key) {
  const node = $(selector);
  if (node) node.textContent = t(key, node.textContent);
}

function setPlaceholder(selector, key) {
  const node = $(selector);
  if (node) node.placeholder = t(key, node.placeholder);
}

function setTitle(selector, key) {
  const node = $(selector);
  if (node) node.title = t(key, node.title);
}

function renderI18n() {
  document.documentElement.lang = currentLocale === "en" ? "en" : "zh-CN";
  document.title = t("appTitle");
  setText(".brand h1", "appTitle");
  setText(".brand p", "appSubtitle");
  setText('[data-view="upload"]', "navAssets");
  setText('[data-view="series"]', "navSeries");
  setText('[data-view="tagging"]', "navAutoTag");
  setText('[data-view="library"]', "navLibrary");
  setText('[data-view="prompts"]', "navPrompt");
  setText("#currentLanguageLabel", "localeName");
  setText(".languageIcon", "language");
  setText(".modelBox .field span", "modelKey");
  setPlaceholder("#aiApiKey", "modelKeyPlaceholder");
  $$(".modelKeyMissingHint").forEach((hint) => { hint.textContent = t("needModelKey"); });
  setText("#prompts .promptMeta div:nth-child(2) span", "model");
  setText("#prompts .promptMeta div:nth-child(3) span", "endpoint");
  setPlaceholder("#newCategoryName", "categoryPlaceholder");
  setPlaceholder("#newTagName", "tagNamePlaceholder");
  setPlaceholder("#newTagDefinition", "tagDefinitionPlaceholder");
  setText("#openSeriesUploadBtn", "uploadSeries");
  setText("#series .eyebrow", "seriesEyebrow");
  setText("#series h2", "seriesTitle");
  setText("#series .topline p:not(.eyebrow)", "seriesDesc");
  setText("#seriesUploadModal h3", "uploadSeriesTitle");
  setText("#seriesUploadModal .modalHead p", "uploadSeriesDesc");
  setText('label[for="seriesTitleInput"] span', "seriesName");
  setText("#seriesUploadForm .field:nth-of-type(1) span", "seriesName");
  setText("#seriesUploadForm .field:nth-of-type(2) span", "episodeNo");
  setPlaceholder("#seriesTitleInput", "seriesName");
  setPlaceholder("#episodeNoInput", "episodeNo");
  setText("#seriesDropzone strong", "chooseEpisodeVideo");
  setText("#seriesDropzone small", "seriesDropHint");
  setText('#seriesUploadForm button[type="submit"]', "startEpisodeAnalysis");
  setText("#seriesDetail .eyebrow", "seriesDetailEyebrow");
  setText("#seriesDetailTitle", "seriesDetailTitle");
  setText("#seriesDetailSubtitle", "seriesDetailDesc");
  setText("#backToSeriesBtn", "backToSeries");
  setText("#seriesDetail .editingAssetPanel h3", "episodes");
  setText("#seriesDetail .editingAssetPanel .panelHead p", "episodesDesc");
  setText("#seriesDetailEpisodes.emptyState", "selectSeries");
  setText("#seriesDetail .editingStoryPanel h3", "storylines");
  setText("#seriesDetail .editingStoryPanel .panelHead p", "storylinesDesc");
  setText(".seriesStoryActions .miniField span", "episodeLimit");
  setText("#seriesDetailGenerateStorylinesBtn", "generateStoryline");
  setText("#seriesDetailStorylines.emptyState", "noStorylines");
  setText("#seriesDetail .editingCutPanel h3", "cutlistExport");
  setText("#seriesDetail .editingCutPanel .panelHead p", "cutlistExportDesc");
  setText("#seriesDetailGenerateCutlistBtn", "generateCutlist");
  setText("#seriesDetailCutlistPanel.emptyState", "selectStoryline");
  setText("#seriesDetailRenderPreviewBtn", "renderPreview");
  setText("#seriesDetailExportJianyingBtn", "exportJianying");
  setText("#upload .eyebrow", "assetEyebrow");
  setText("#upload h2", "assetTitle");
  setText(".nameSearchBox span", "assetName");
  setText(".tagSearchBox span", "tag");
  setPlaceholder("#assetNameSearchInput", "assetNamePlaceholder");
  setPlaceholder("#assetTagSearchInput", "tagPlaceholder");
  setTitle(".nameSearchBox", "assetNamePlaceholder");
  setTitle(".tagSearchBox", "tagPlaceholder");
  setText("#clearAssetFiltersBtn", "clear");
  setText("#openUploadBtn", "uploadAnalyze");
  setText("#uploadModal h3", "uploadAnalyze");
  setText("#uploadModal .modalHead p", "uploadAnalyzeDesc");
  setTitle("#closeUploadBtn", "cancel");
  setText("#dropzone strong", "chooseVideo");
  setText("#dropzone small", "videoHint");
  setText('#uploadForm button[type="submit"]', "startAnalysis");
  setText("#tagging .topline h2", "autoTagTitle");
  setText("#tagging .topline p", "autoTagDesc");
  setText(".selectedAssetPanel h3", "currentAsset");
  setText("#selectedAssetHint", "currentAssetDesc");
  setText("#selectedAssetPreview.emptyState", "noBoundAsset");
  setText('#tagging .panel label.field span', "bindAsset");
  setText(".taggingPreviewHead h3", "tagPreview");
  if ($("#summary")?.textContent === "等待拉片信息" || $("#summary")?.textContent === "Waiting for report") setText("#summary", "waitingReport");
  setText("#autoTagBtn", "navAutoTag");
  setText("#confirmBtn", "confirmLibrary");
  setText('#tagging label.field span', "bindAsset");
  setText('#tagging .panel > label.field:last-child span', "note");
  setPlaceholder("#note", "notePlaceholder");
  setText("#library .topline h2", "libraryTitle");
  setText("#library .topline p", "libraryDesc");
  setText(".libraryTools > .panelHead h3", "schemaTitle");
  setText(".libraryTools > .panelHead p", "schemaDesc");
  setText(".libraryForms .field:nth-child(1) > span", "addCategory");
  setText("#addCategoryBtn", "addCategoryBtn");
  setText(".libraryForms .field:nth-child(2) > span", "addTag");
  setText("#addLibraryTagBtn", "addTagBtn");
  setText(".graveyardBlock h3", "graveyard");
  setText(".graveyardBlock .panelHead p", "graveyardDesc");
  setText("#toggleGraveyardBtn", graveyardCollapsed ? "graveyard" : "collapse");
  setText(".libraryRecordHead h3", "libraryRecords");
  setText(".libraryRecordHead p", "libraryRecordsDesc");
  setText("#prompts .topline h2", "promptTitle");
  setText("#prompts .topline p", "promptDesc");
  setText("#resetPromptsBtn", "resetDefault");
  setText("#savePromptsBtn", "saveConfig");
  const promptPanels = [
    ["reportPrompt", "reportPromptDesc"], ["tagPrompt", "tagPromptDesc"], ["storylinePrompt", "storylinePromptDesc"],
    ["cutlistPrompt", "cutlistPromptDesc"], ["transcribePrompt", "transcribePromptDesc"], ["translatePrompt", "translatePromptDesc"], ["jsonRepairPrompt", "jsonRepairPromptDesc"]
  ];
  $$(".promptGrid .panel").forEach((panel, index) => {
    const keys = promptPanels[index];
    if (!keys) return;
    const title = panel.querySelector("h3");
    const desc = panel.querySelector(".panelHead p");
    if (title) title.textContent = t(keys[0], title.textContent);
    if (desc) desc.textContent = t(keys[1], desc.textContent);
    const labels = panel.querySelectorAll("label.field span");
    if (labels[0]) labels[0].textContent = t("systemRole");
    if (labels[1]) labels[1].textContent = t("userPrompt");
  });
  setText("#transcribeModal h3", "transcribeTitle");
  setText("#transcribeModal .modalHead p", "transcribeDesc");
  setText('#transcribeModal label:nth-of-type(1) span', "transcribeMethod");
  setText('#transcribeModal label:nth-of-type(2) span', "transcribeLanguage");
  setText('#transcribeModal label:nth-of-type(3) span', "localModel");
  setText('#transcribeMethod option[value="local"]', "localAsr");
  setText('#transcribeMethod option[value="model"]', "modelAsr");
  setText('#transcribeLanguage option[value="auto"]', "autoDetect");
  setText('#transcribeLanguage option[value="zh"]', "chinese");
  setText('#transcribeLanguage option[value="en"]', "english");
  setText('#transcribeLanguage option[value="id"]', "indonesian");
  setText("#transcribeModalHint", "localAsrHint");
  setText("#cancelTranscribeBtn", "cancel");
  setText("#startTranscribeBtn", "startTranscribe");
  setText("#previewTagModalTitle", "editPreviewTag");
  setText("#previewTagModalMeta", "editPreviewTagDesc");
  setText("#cancelPreviewTagBtn", "cancel");
  setText("#savePreviewTagBtn", "saveChanges");
  setText("#definitionModalTitle", "editDefinition");
  setText('#definitionModal label:nth-of-type(1) span', "tagName");
  setText('#definitionModal label:nth-of-type(2) span', "tagDefinition");
  setPlaceholder("#definitionModalName", "tagName");
  setPlaceholder("#definitionModalText", "tagDefinition");
  setText('#mergeTagPanel span', "mergeTo");
  setText("#confirmMergeTagBtn", "confirmMerge");
  setText('#transferTagPanel label:nth-of-type(1) span', "targetCategory");
  setText('#transferTagPanel label:nth-of-type(2) span', "targetLevel");
  setText("#confirmTransferTagBtn", "confirmTransfer");
  setText("#mergeDefinitionTagBtn", "merge");
  setText("#transferDefinitionTagBtn", "transfer");
  setText("#deleteDefinitionTagBtn", "delete");
  setText("#saveDefinitionModalBtn", "save");
  $$("#languageMenu [data-locale]").forEach((button) => button.classList.toggle("active", button.dataset.locale === currentLocale));
}

function setLocale(locale) {
  if (!I18N[locale]) return;
  currentLocale = locale;
  localStorage.setItem("materialTaggingLocale", locale);
  const menu = $("#languageMenu");
  const toggle = $("#languageToggle");
  if (menu) menu.hidden = true;
  if (toggle) toggle.setAttribute("aria-expanded", "false");
  renderI18n();
  renderUploadAssets();
  renderSeriesLibrary();
  renderSeriesDetail();
  renderTagSystem();
  renderTagGraveyard();
  renderLibrary();
  renderTagEditor(Object.keys(currentTags || {}).length ? undefined : {});
  syncModelKeyGates();
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  let data = {};
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (err) {
      throw new Error(text.slice(0, 240) || "服务端返回内容无法解析");
    }
  }
  if (!res.ok) throw new Error(data.error || "请求失败");
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  }[char]));
}

function setButtonBusy(button, busy, busyText = t("processing")) {
  if (!button) return;
  if (busy) {
    button.dataset.originalText = button.dataset.originalText || button.textContent;
    button.textContent = busyText;
    button.disabled = true;
    button.classList.add("isBusy");
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
    button.classList.remove("isBusy");
  }
}

function setPanelLoading(selector, message) {
  const node = $(selector);
  if (!node) return;
  node.className = node.className.replace(/\s?emptyState/g, "") + " emptyState loadingState";
  node.innerHTML = `<div class="inlineLoading"><i></i><span>${escapeHtml(message)}</span></div>`;
}

function modelKey() {
  return $("#aiApiKey")?.value.trim() || "";
}

function buttonRequiresModelKey(button) {
  if (!button?.dataset?.requiresModelKey) return false;
  if (button.dataset.requiresModelKey === "conditional") {
    if (button.id === "startTranscribeBtn") return ($("#transcribeMethod")?.value || "local") === "model";
    return false;
  }
  return true;
}

function ensureModelKeyHint(button) {
  if (!button) return null;
  let wrapper = button.closest(".modelKeyGate");
  if (!wrapper) {
    wrapper = document.createElement("span");
    wrapper.className = "modelKeyGate";
    button.parentNode.insertBefore(wrapper, button);
    wrapper.appendChild(button);
  }
  let hint = wrapper.querySelector(":scope > .modelKeyMissingHint");
  if (!hint) {
    hint = document.createElement("small");
    hint.className = "modelKeyMissingHint";
    hint.textContent = t("needModelKey");
    wrapper.appendChild(hint);
  }
  button.dataset.modelKeyHintAttached = "1";
  return hint;
}

function setModelKeyAttention(active = true) {
  const input = $("#aiApiKey");
  const box = input?.closest(".modelBox");
  if (!input) return;
  input.classList.toggle("keyAttention", active);
  box?.classList.toggle("keyAttention", active);
  if (active) {
    input.focus({ preventScroll: false });
    window.clearTimeout(setModelKeyAttention.timer);
    setModelKeyAttention.timer = window.setTimeout(() => setModelKeyAttention(false), 2600);
  }
}

function promptForModelKey() {
  showToast(t("needModelKey"), "error");
  setModelKeyAttention(true);
}

function requireModelKey() {
  if (modelKey()) return true;
  promptForModelKey();
  syncModelKeyGates();
  return false;
}

function syncModelKeyGates() {
  const hasKey = Boolean(modelKey());
  $$('[data-requires-model-key]').forEach((button) => {
    const requires = buttonRequiresModelKey(button);
    const missing = requires && !hasKey && !button.disabled;
    const hint = ensureModelKeyHint(button);
    button.classList.toggle("requiresKeyMissing", missing);
    button.setAttribute("aria-disabled", missing ? "true" : "false");
    if (hint) hint.classList.toggle("show", missing);
  });
}

function setView(id) {
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === id));
  $$(".nav").forEach((nav) => nav.classList.toggle("active", nav.dataset.view === id));
}

function getAssetTitle(asset) {
  return asset.title || asset.sourceName || asset.id;
}

function getAssetSubtitle(asset) {
  const title = getAssetTitle(asset);
  return title.replace(/^Task[^@]*@?/, "").replace(/\.mp4$/i, "") || knownStatusText(asset.status) || t("assetFallback");
}

function preferredReportPath(asset) {
  const reports = asset?.artifacts?.reports || [];
  const preferred = reports.find((item) => /^AI_video_analysis(_visual)?_bilingual\.md$/i.test(item.name));
  return preferred?.path || "";
}

function preferredReportLink(asset) {
  const reports = asset?.artifacts?.reports || [];
  return reports.find((item) => /^AI_video_analysis(_visual)?_bilingual\.md$/i.test(item.name));
}

function transcriptLinks(asset) {
  const files = asset?.artifacts?.files || [];
  return {
    txt: files.find((item) => /^transcript\.txt$/i.test(item.name)),
    srt: files.find((item) => /^transcript\.srt$/i.test(item.name)),
    json: files.find((item) => /^transcript\.json$/i.test(item.name)),
    zhTxt: files.find((item) => /^transcript_zh\.txt$/i.test(item.name)),
    zhSrt: files.find((item) => /^transcript_zh\.srt$/i.test(item.name)),
    zhJson: files.find((item) => /^transcript_zh\.json$/i.test(item.name)),
  };
}

function transcriptItemsForDisplay(asset) {
  const links = transcriptLinks(asset);
  return [links.zhTxt, links.zhSrt, links.zhJson, links.txt, links.srt, links.json].filter(Boolean);
}

function preferredTranscriptLink(asset, mode = "zh") {
  const links = transcriptLinks(asset);
  if (mode === "original") return links.txt || links.zhTxt || null;
  return links.zhTxt || links.txt || null;
}

function audioLinks(asset) {
  return (asset?.artifacts?.files || []).filter((item) => /\.(mp3|wav)$/i.test(item.name));
}
function primaryNote(asset) {
  return asset?.artifacts?.artifactNotes?.[0];
}

function previewImage(asset) {
  return asset?.artifacts?.storyboard || null;
}

function assetWorkflowStatus(asset) {
  if (!asset) return t("unboundAsset");
  if (asset.confirmed) return t("assetStatusConfirmed");
  const hasTranscript = Boolean(preferredTranscriptLink(asset));
  const hasReport = Boolean(preferredReportLink(asset));
  const hasAudio = audioLinks(asset).length > 0;
  if (hasReport) return t("assetStatusReportReady");
  if (hasTranscript) return t("assetStatusTranscriptReady");
  if (hasAudio) return t("assetStatusPrepReady");
  return knownStatusText(asset.status) || t("assetStatusPrepReady");
}

function showToast(message, type = "info") {
  let toast = document.querySelector("#toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message || "操作失败";
  toast.className = `toast show ${type}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => {
    toast.className = "toast";
  }, 3600);
}
function artifactLinks(items = [], limit = 6) {
  return (items || []).slice(0, limit).map((item) => `<a href="${item.url}" target="_blank" title="${escapeHtml(item.path || item.name)}">${escapeHtml(item.name)}</a>`).join("");
}

function openFramePreview(url, caption = "") {
  const modal = $("#framePreviewModal");
  const image = $("#framePreviewImage");
  const label = $("#framePreviewCaption");
  if (!modal || !image) return;
  image.src = url;
  image.alt = caption || t("frames");
  if (label) label.textContent = caption || t("frames");
  modal.hidden = false;
}

function closeFramePreview() {
  const modal = $("#framePreviewModal");
  const image = $("#framePreviewImage");
  if (!modal) return;
  modal.hidden = true;
  if (image) image.removeAttribute("src");
}

async function loadTranscriptPreview(asset, mode = "zh") {
  const target = document.querySelector(`[data-transcript-preview="${CSS.escape(asset.id)}"]`);
  const toggle = document.querySelector(`[data-transcript-toggle="${CSS.escape(asset.id)}"]`);
  const transcript = preferredTranscriptLink(asset, mode);
  if (!target || !transcript) return;
  target.dataset.mode = mode;
  if (toggle) {
    toggle.dataset.mode = mode;
    const label = mode === "zh" ? t("chinese") : "Original";
    toggle.innerHTML = `<span class="switchIcon" aria-hidden="true">⇄</span><span class="currentLang">${label}</span>`;
    toggle.title = mode === "zh" ? t("currentChinese") : t("currentOriginal");
  }
  try {
    const res = await fetch(transcript.url);
    const text = await res.text();
    target.textContent = text.trim().slice(0, 3500) || t("transcriptEmpty");
  } catch (err) {
    target.textContent = t("transcriptReadFailed");
  }
}
function renderSelectedAssetPanel(asset = null) {
  const previewWrap = $("#selectedAssetPreview");
  const artifactsWrap = $("#selectedAssetArtifacts");
  const hint = $("#selectedAssetHint");
  if (!previewWrap || !artifactsWrap) return;
  if (!asset) {
    if (hint) hint.textContent = t("currentAssetDesc");
    previewWrap.className = "selectedAssetPreview emptyState compact";
    previewWrap.innerHTML = t("noBoundAsset");
    artifactsWrap.innerHTML = "";
    return;
  }
  const preview = previewImage(asset);
  const artifacts = asset.artifacts || {};
  const reports = artifacts.reports || [];
  const notes = artifacts.artifactNotes || [];
  const files = artifacts.files || [];
  const frames = artifacts.frames || [];
  const transcriptItems = transcriptItemsForDisplay(asset);
  const audioItems = audioLinks(asset);
  const otherFiles = files.filter((item) => !/^transcript\.(txt|srt|json)$/i.test(item.name) && !/\.(mp3|wav)$/i.test(item.name));
  const fileGroups = [
    [t("report"), reports],
    [t("audio"), audioItems],
    [t("artifacts"), notes],
    [t("other"), otherFiles],
  ].filter(([, items]) => items && items.length);
  if (hint) hint.textContent = assetWorkflowStatus(asset);
  previewWrap.className = "selectedAssetPreview";
  previewWrap.innerHTML = `
    <div class="selectedPreviewMedia">
      ${preview ? `<img src="${preview.url}" alt="${escapeHtml(getAssetTitle(asset))}">` : `<span>${t("noStoryboard")}</span>`}
    </div>
    <div class="selectedPreviewMeta">
      <h3 title="${escapeHtml(getAssetTitle(asset))}">${escapeHtml(getAssetTitle(asset))}</h3>
      <p title="${escapeHtml(getAssetSubtitle(asset))}">${escapeHtml(getAssetSubtitle(asset))}</p>
      <div class="materialBadges">
        <span class="badge ${transcriptItems.length ? "ok" : "warn"}">${transcriptItems.length ? t("hasSubtitles") : t("pendingTranscribe")}</span>
        <span class="badge ${reports.length ? "ok" : "warn"}">${reports.length ? t("hasReport") : t("pendingReport")}</span>
        ${asset.confirmed ? `<span class="badge done">${t("assetStatusConfirmed")}</span>` : `<span class="badge">${t("pendingReview")}</span>`}
      </div>
    </div>
  `;
  artifactsWrap.innerHTML = `
    ${frames.length ? `
      <div class="selectedArtifactGroup">
        <strong>${t("frames")}</strong>
        <div class="selectedFrameStrip">
          ${frames.map((frame) => `<button class="frameThumb" type="button" data-frame-url="${escapeHtml(frame.url)}" data-frame-name="${escapeHtml(frame.name)}" title="${escapeHtml(frame.name)}"><img src="${frame.url}" alt="${escapeHtml(frame.name)}"></button>`).join("")}
        </div>
      </div>
    ` : `
      <div class="selectedArtifactGroup">
        <strong>${t("frames")}</strong>
        <span class="artifactEmpty">${t("noFrames")}</span>
      </div>
    `}
    <div class="selectedArtifactGroup">
      <div class="artifactGroupHead">
        <strong>${t("subtitles")}</strong>
        <div class="artifactHeadActions">
          <button class="secondary panelTranscribeBtn" type="button">${transcriptItems.length ? t("retranscribe") : t("transcribeAudio")}</button>
          ${transcriptItems.length ? `<button class="transcriptToggle" type="button" data-transcript-toggle="${escapeHtml(asset.id)}" title="${t("currentChinese")}"><span class="switchIcon" aria-hidden="true">⇄</span><span class="currentLang">${t("chinese")}</span></button>` : ""}
        </div>
      </div>
      ${transcriptItems.length ? `
        <div>${artifactLinks(transcriptItems, 99)}</div>
        <pre class="transcriptPreview" data-transcript-preview="${escapeHtml(asset.id)}">${t("readingSubtitles")}</pre>
      ` : `<span class="artifactEmpty">${t("noSubtitles")}</span>`}
    </div>
    <div class="selectedArtifactGroup">
      <div class="artifactGroupHead">
        <strong>${t("files")}</strong>
        <div class="artifactHeadActions">
          <button class="secondary panelReportBtn" type="button" data-requires-model-key="1" ${transcriptItems.length ? "" : "disabled"}>${reports.length ? t("regenerateReport") : t("generateReport")}</button>
          <label class="secondary fileActionBtn" for="reportFile">${t("uploadMd")}</label>
        </div>
      </div>
      ${fileGroups.length ? `<div class="fileArtifactList">${fileGroups.map(([label, items]) => `
        <div class="fileArtifactGroup">
          <span>${label}</span>
          <div>${artifactLinks(items, 99)}</div>
        </div>
      `).join("")}</div>` : `<span class="artifactEmpty">${t("noFiles")}</span>`}
    </div>
  `;
  artifactsWrap.querySelector(".panelTranscribeBtn")?.addEventListener("click", () => openTranscribeModal(asset.id));
  artifactsWrap.querySelector(".panelReportBtn")?.addEventListener("click", () => generateReport(asset.id));
  artifactsWrap.querySelectorAll(".frameThumb").forEach((button) => button.addEventListener("click", () => openFramePreview(button.dataset.frameUrl, button.dataset.frameName)));
  artifactsWrap.querySelector(".transcriptToggle")?.addEventListener("click", (event) => {
    const nextMode = event.currentTarget.dataset.mode === "zh" ? "original" : "zh";
    loadTranscriptPreview(asset, nextMode);
  });
  if (transcriptItems.length) loadTranscriptPreview(asset, "zh");
  syncModelKeyGates();
}
function renderAssetSelect() {
  const select = $("#assetSelect");
  select.innerHTML = `<option value="">${t("unboundNewAsset")}</option>`;
  assets.forEach((asset) => {
    const option = document.createElement("option");
    option.value = asset.id;
    option.textContent = `${getAssetTitle(asset)} · ${assetWorkflowStatus(asset)}`;
    select.appendChild(option);
  });
}

function openAssetForTagging(assetId) {
  setView("tagging");
  applySelectedAsset(assetId);
}
function applySelectedAsset(assetId) {
  const asset = assets.find((item) => item.id === assetId);
  if (!asset) {
    $("#reportPath").value = "";
    if ($("#reportFile")) $("#reportFile").value = "";
    currentTags = {};
    currentTagDefinitions = {};
    currentSummary = "";
    $("#summary").textContent = t("waitingReport");
    $("#note").value = "";
    renderTagEditor({});
    renderSelectedAssetPanel(null);
    return;
  }
  $("#assetSelect").value = asset.id;
  $("#reportPath").value = preferredReportPath(asset);
  if ($("#reportFile")) $("#reportFile").value = "";
  currentTags = JSON.parse(JSON.stringify(asset.tags || {}));
  seedPreviewDefinitionsFromSchema(currentTags);
  currentSummary = asset.autoTagSummary || "";
  const hasTranscript = Boolean(preferredTranscriptLink(asset));
  $("#summary").textContent = currentSummary || (preferredReportPath(asset) ? t("reportPathFilled") : (hasTranscript ? t("needGenerateReportFromTranscript") : t("needTranscribeFirst")));
  $("#note").value = asset.note || "";
  renderTagEditor();
  renderSelectedAssetPanel(asset);
}



function seriesTitle(series) {
  return series?.title || series?.id || t("untitledAsset");
}

function episodeStatus(ep) {
  const hasReport = (ep?.artifacts?.reports || []).length > 0;
  const hasTranscript = (ep?.artifacts?.files || []).some((item) => /^transcript(_zh)?\.(txt|json)$/i.test(item.name));
  const hasPrep = Boolean(ep?.artifacts?.storyboard || (ep?.artifacts?.frames || []).length || (ep?.artifacts?.files || []).some((item) => /^(audio_for_ai\.mp3|audio_16k_mono\.wav|prep_result\.json)$/i.test(item.name)));
  if (hasReport) return t("episodeStatusReportReady");
  if (hasTranscript) return t("episodeStatusTranscriptReady");
  if (hasPrep) return t("episodeStatusPrepReady");
  return knownStatusText(ep?.status) || t("waitingAnalysis");
}

function seriesNeedsResume(series) {
  return (series?.episodes || []).some((ep) => !(ep?.artifacts?.reports || []).length);
}

function renderSeriesLibrary() {
  const wrap = $("#seriesGrid");
  if (!wrap) return;
  if (!seriesLibrary.length) {
    wrap.innerHTML = `<div class="panel emptyState">${t("noSeriesEmpty")}</div>`;
    return;
  }
  wrap.innerHTML = seriesLibrary.map((series) => {
    const episodes = series.episodes || [];
    const storyCount = (series.storylines || []).length;
    const canResume = seriesNeedsResume(series);
    return `
      <article class="seriesCard" data-series-id="${escapeHtml(series.id)}" role="button" tabindex="0">
        <div class="seriesCardHead">
          <div><h3>${escapeHtml(seriesTitle(series))}</h3><p>${episodeCountText(episodes.length)} · ${storylineCountText(storyCount)}</p></div>
          <div class="seriesCardActions">
            ${canResume ? `<button class="secondary resumeSeriesBtn" type="button" data-requires-model-key="1" data-series-id="${escapeHtml(series.id)}">${t("resumeAnalysis")}</button>` : ""}
            <button class="secondary openSeriesDetailBtn" type="button" data-series-id="${escapeHtml(series.id)}">${t("enterSeries")}</button>
          </div>
        </div>
        <div class="episodeList">
          ${episodes.map((ep) => {
            const preview = ep.artifacts?.storyboard;
            return `<div class="episodeRow"><div class="episodeThumb">${preview ? `<img src="${preview.url}" alt="${escapeHtml(ep.title || "")}">` : `<span>${t("noPreview")}</span>`}</div><div><strong>${episodeLabel(escapeHtml(ep.episodeNo || ""))}</strong><p title="${escapeHtml(ep.sourceName || "")}">${escapeHtml(ep.sourceName || ep.title || "")}</p><small>${escapeHtml(episodeStatus(ep))}</small></div></div>`;
          }).join("") || `<div class="emptyState compact">${t("noEpisodes")}</div>`}
        </div>
      </article>`;
  }).join("");
  wrap.querySelectorAll(".seriesCard").forEach((card) => {
    const open = () => openSeriesDetail(card.dataset.seriesId || "");
    card.addEventListener("click", (event) => {
      if (event.target.closest("button")) return;
      open();
    });
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open();
      }
    });
  });
  wrap.querySelectorAll(".openSeriesDetailBtn").forEach((button) => button.addEventListener("click", () => openSeriesDetail(button.dataset.seriesId || "")));
  wrap.querySelectorAll(".resumeSeriesBtn").forEach((button) => button.addEventListener("click", () => resumeSeriesAnalysis(button.dataset.seriesId || "")));
}

function openSeriesUploadModal() {
  if (!requireModelKey()) return;
  const modal = $("#seriesUploadModal");
  if (modal) modal.hidden = false;
}

function closeSeriesUploadModal() {
  const modal = $("#seriesUploadModal");
  if (modal) modal.hidden = true;
}

function setSeriesUploadFile(file) {
  const input = $("#seriesDropzone input");
  if (!input || !file) return false;
  if (!file.type.startsWith("video/")) return showToast(t("invalidVideoFile"), "error"), false;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  input.files = transfer.files;
  const label = $("#seriesDropzone strong");
  if (label) label.textContent = file.name;
  return true;
}

async function uploadSeriesEpisode(event) {
  event.preventDefault();
  if (!requireModelKey()) return;
  const formEl = event.currentTarget;
  const form = new FormData(formEl);
  form.append("apiKey", modelKey());
  const status = $("#seriesStatus");
  if (status) status.textContent = t("episodeUploading");
  try {
    const data = await api("/api/series/upload", { method: "POST", body: form });
    showToast(t("episodeQueued"), "success");
    if (status) status.textContent = `已加入任务：${data.task?.stage || data.episode?.status || "排队中"}`;
    formEl.reset();
    const label = $("#seriesDropzone strong");
    if (label) label.textContent = t("chooseEpisodeVideo");
    closeSeriesUploadModal();
    await refresh();
    startTaskPolling();
    setView("series");
  } catch (err) {
    showToast(err.message, "error");
    if (status) status.textContent = err.message;
  }
}

async function resumeSeriesAnalysis(seriesId) {
  if (!seriesId) return;
  if (!requireModelKey()) return;
  const status = $("#seriesStatus");
  if (status) status.textContent = t("resumeSeries");
  try {
    const data = await api("/api/series/resume", {
      method: "POST",
      body: JSON.stringify({ seriesId, apiKey: modelKey() }),
    });
    const count = Number(data.count || 0);
    if (count > 0) {
      showToast(`已加入 ${count} 个继续分析任务`, "success");
      if (status) status.textContent = `已加入 ${count} 个继续分析任务`;
      startTaskPolling();
    } else {
      showToast(t("noResumeEpisode"), "success");
      if (status) status.textContent = t("noResumeEpisodeStatus");
    }
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    if (status) status.textContent = err.message;
  }
}
function bindSeriesDropzone() {
  const dropzone = $("#seriesDropzone");
  const input = $("#seriesDropzone input");
  if (!dropzone || !input) return;
  input.addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    if (file) setSeriesUploadFile(file);
  });
  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => {
    stopFileDrag(event);
    dropzone.classList.add("dragOver");
  }));
  ["dragleave", "dragend"].forEach((name) => dropzone.addEventListener(name, () => dropzone.classList.remove("dragOver")));
  dropzone.addEventListener("drop", (event) => {
    stopFileDrag(event);
    dropzone.classList.remove("dragOver");
    const file = Array.from(event.dataTransfer?.files || []).find((item) => item.type.startsWith("video/"));
    setSeriesUploadFile(file);
  });
}


function findSeriesById(id) {
  return seriesLibrary.find((item) => item.id === id) || null;
}

function openSeriesDetail(seriesId) {
  const series = findSeriesById(seriesId);
  if (!series) return showToast("\u5267\u96c6\u4e0d\u5b58\u5728", "error");
  activeSeriesId = series.id;
  editingSourceType = "series";
  editingSeriesId = series.id;
  seriesDetailEpisodeLimit = Math.max(1, Number(seriesDetailEpisodeLimit || 0) || (series.episodes || []).length || 3);
  if (!activeSeriesStorylineId || !(series.storylines || []).some((item) => item.id === activeSeriesStorylineId)) {
    activeSeriesStorylineId = (series.storylines || [])[0]?.id || "";
  }
  setView("seriesDetail");
  renderSeriesDetail();
}

function activeSeries() {
  return findSeriesById(activeSeriesId);
}

function activeSeriesStoryline() {
  const series = activeSeries();
  return (series?.storylines || []).find((item) => item.id === activeSeriesStorylineId) || (series?.storylines || [])[0] || null;
}

function seriesDetailEpisodeLabel(episodeId) {
  const series = activeSeries();
  const episode = (series?.episodes || []).find((item) => String(item.id) === String(episodeId));
  return episode ? episodeLabel(episode.episodeNo || "?") : String(episodeId || "");
}

function cutlistMarkup(cutlist, episodeLabel, fallbackTitle = "\u526a\u8f91\u6e05\u5355") {
  const segments = cutlist?.segments || [];
  if (!segments.length) return "";
  return `
    <div class="cutlistSummary">
      <strong>${escapeHtml(cutlist.title || fallbackTitle)}</strong>
      <span>${segments.length} \u4e2a\u7247\u6bb5 \u00b7 ${escapeHtml(cutlist.estimatedDuration || "30-60 \u79d2")}</span>
    </div>
    <div class="cutSegmentList">
      ${segments.map((seg, index) => {
        const source = `${seg.episodeId ? `${episodeLabel(seg.episodeId)} \u00b7 ` : ""}${seg.sourceStart || "00:00.00"} - ${seg.sourceEnd || "00:00.00"}`;
        const caption = seg.caption ? `<div class="cutSegmentCaption"><span>\u5b57\u5e55</span>${escapeHtml(seg.caption)}</div>` : "";
        const reason = seg.reason ? `<p>${escapeHtml(seg.reason)}</p>` : "";
        return `<article class="cutSegment"><div class="cutSegmentTime"><span>${String(index + 1).padStart(2, "0")}</span>${escapeHtml(source)}</div><div class="cutSegmentRole">${escapeHtml(editingRoleLabel(seg.role || seg.title))}</div>${reason}${caption}</article>`;
      }).join("")}
    </div>`;
}

function renderSeriesDetail() {
  const series = activeSeries();
  const title = $("#seriesDetailTitle");
  const subtitle = $("#seriesDetailSubtitle");
  const episodeWrap = $("#seriesDetailEpisodes");
  const limitInput = $("#seriesDetailEpisodeLimit");
  if (!series || !episodeWrap) return;
  if (title) title.textContent = seriesTitle(series);
  if (subtitle) subtitle.textContent = `${episodeCountText((series.episodes || []).length)} · ${savedStorylineCountText((series.storylines || []).length)}`;
  if (limitInput) {
    const max = Math.max((series.episodes || []).length, 1);
    limitInput.max = String(max);
    if (!seriesDetailEpisodeLimit || seriesDetailEpisodeLimit > max) seriesDetailEpisodeLimit = max;
    limitInput.value = seriesDetailEpisodeLimit;
  }
  const episodes = series.episodes || [];
  episodeWrap.className = episodes.length ? "seriesDetailEpisodes" : "seriesDetailEpisodes emptyState";
  episodeWrap.innerHTML = episodes.length ? episodes.map((ep) => {
    const preview = ep.artifacts?.storyboard;
    return `<article class="seriesDetailEpisode"><div class="episodeThumb large">${preview ? `<img src="${preview.url}" alt="${escapeHtml(ep.sourceName || "")}">` : `<span>${t("noPreview")}</span>`}</div><div><strong>${episodeLabel(escapeHtml(ep.episodeNo || "?"))}</strong><p title="${escapeHtml(ep.sourceName || ep.title || "")}">${escapeHtml(ep.sourceName || ep.title || t("untitledAsset"))}</p><small>${escapeHtml(episodeStatus(ep))}</small></div></article>`;
  }).join("") : t("noEpisodes");
  renderSeriesDetailStorylines();
  renderSeriesDetailCutlist();
}

function renderSeriesDetailStorylines() {
  const list = $("#seriesDetailStorylines");
  const series = activeSeries();
  if (!list || !series) return;
  const rows = series.storylines || [];
  if (!rows.length) {
    list.className = "storylineList emptyState";
    list.innerHTML = currentLocale === "en" ? "No storylines yet. Click the button on the right to generate." : "\u8fd8\u6ca1\u6709\u6545\u4e8b\u7ebf\uff0c\u70b9\u51fb\u53f3\u4e0a\u89d2\u751f\u6210";
    activeSeriesStorylineId = "";
    return;
  }
  list.className = "storylineList";
  if (!activeSeriesStorylineId || !rows.some((item) => item.id === activeSeriesStorylineId)) activeSeriesStorylineId = rows[0].id;
  list.innerHTML = rows.map((item, index) => {
    const selected = item.id === activeSeriesStorylineId;
    const saved = item.cutlist?.segments?.length ? `<span class="storylineBadge">${escapeHtml(currentLocale === "en" ? "Cutlist ready" : "已生成剪辑清单")}</span>` : "";
    return `<button class="storylineCard ${selected ? "active" : ""}" type="button" data-storyline-id="${escapeHtml(item.id)}"><span class="storylineIndex">${String(index + 1).padStart(2, "0")}</span><strong>${escapeHtml(item.title || `${currentLocale === "en" ? "Storyline" : "故事线"} ${index + 1}`)}</strong><small>${escapeHtml(item.hook || item.reason || item.arc || "")}</small><em>${escapeHtml(item.duration || item.targetDuration || (currentLocale === "en" ? "Ad edit" : "投流剪辑"))}</em>${saved}</button>`;
  }).join("");
  list.querySelectorAll(".storylineCard").forEach((button) => button.addEventListener("click", () => {
    activeSeriesStorylineId = button.dataset.storylineId || "";
    renderSeriesDetail();
  }));
}

function renderSeriesDetailOutputs(storyline) {
  const outputs = $("#seriesDetailOutputs");
  if (!outputs) return;
  const links = [];
  if (storyline?.previewUrl) links.push(`<a href="${storyline.previewUrl}" target="_blank">${escapeHtml(currentLocale === "en" ? "Open preview video" : "打开预览视频")}</a>`);
  if (storyline?.cutlistUrl) links.push(`<a href="${storyline.cutlistUrl}" target="_blank">cutlist.json</a>`);
  if (storyline?.srtUrl) links.push(`<a href="${storyline.srtUrl}" target="_blank">${escapeHtml(currentLocale === "en" ? "Subtitles SRT" : "字幕 SRT")}</a>`);
  if (storyline?.packageUrl) links.push(`<a href="${storyline.packageUrl}" target="_blank">${escapeHtml(currentLocale === "en" ? "Jianying draft package" : "剪映草稿包")}</a>`);
  const preview = storyline?.previewUrl ? `<div class="editingPreviewVideo"><video src="${storyline.previewUrl}" controls preload="metadata"></video></div>` : "";
  outputs.innerHTML = links.length || preview ? `${preview}<div class="editingOutputLinks">${links.join("")}</div>` : "";
}

function renderSeriesDetailCutlist() {
  const panel = $("#seriesDetailCutlistPanel");
  const button = $("#seriesDetailGenerateCutlistBtn");
  const storyline = activeSeriesStoryline();
  if (!panel) return;
  if (button) button.textContent = storyline?.cutlist?.segments?.length ? t("regenerateCutlist") : t("generateCutlist");
  if (!storyline) {
    panel.className = "cutlistPanel emptyState";
    panel.innerHTML = t("selectStoryline");
    renderSeriesDetailOutputs(null);
    return;
  }
  if (!storyline.cutlist?.segments?.length) {
    panel.className = "cutlistPanel emptyState";
    panel.innerHTML = t("generateCutlistHint");
    renderSeriesDetailOutputs(storyline);
    return;
  }
  panel.className = "cutlistPanel";
  panel.innerHTML = cutlistMarkup(storyline.cutlist, seriesDetailEpisodeLabel, storyline.title || t("generateCutlist"));
  renderSeriesDetailOutputs(storyline);
}

function seriesDetailPayload(extra = {}) {
  return { sourceType: "series", seriesId: activeSeriesId, episodeLimit: Number(seriesDetailEpisodeLimit || 0), ...extra };
}

async function generateSeriesDetailStorylines() {
  if (!requireModelKey()) return;
  if (!activeSeries()) return showToast(t("noSeries"), "error");
  const button = $("#seriesDetailGenerateStorylinesBtn");
  setButtonBusy(button, true, t("generating"));
  setPanelLoading("#seriesDetailStorylines", t("storylinesSaving"));
  try {
    const data = await api("/api/editing/storylines", { method: "POST", body: JSON.stringify(seriesDetailPayload({ apiKey: modelKey() })) });
    activeSeriesStorylineId = data.storylines?.[0]?.id || activeSeriesStorylineId;
    await refresh();
    setView("seriesDetail");
    renderSeriesDetail();
    showToast(t("storylinesSaved"), "success");
  } catch (err) {
    renderSeriesDetail();
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

async function generateSeriesDetailCutlist() {
  if (!requireModelKey()) return;
  const storyline = activeSeriesStoryline();
  if (!storyline) return showToast(t("selectStoryline"), "error");
  const button = $("#seriesDetailGenerateCutlistBtn");
  setButtonBusy(button, true, storyline.cutlist?.segments?.length ? t("regenerateGenerating") : t("generating"));
  setPanelLoading("#seriesDetailCutlistPanel", t("cutlistSaving"));
  try {
    const data = await api("/api/editing/cutlist", { method: "POST", body: JSON.stringify(seriesDetailPayload({ storyline, storylineId: storyline.id, apiKey: modelKey() })) });
    activeSeriesStorylineId = data.storylineId || storyline.id;
    await refresh();
    setView("seriesDetail");
    renderSeriesDetail();
    showToast(t("cutlistSaved"), "success");
  } catch (err) {
    renderSeriesDetail();
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

async function renderSeriesDetailPreviewVideo() {
  const storyline = activeSeriesStoryline();
  if (!storyline?.cutlist?.segments?.length) return showToast(t("generateCutlistHint"), "error");
  const button = $("#seriesDetailRenderPreviewBtn");
  setButtonBusy(button, true, t("rendering"));
  try {
    const data = await api("/api/editing/render-preview", { method: "POST", body: JSON.stringify(seriesDetailPayload({ cutlist: storyline.cutlist, storylineId: storyline.id })) });
    activeSeriesStorylineId = data.storylineId || storyline.id;
    await refresh();
    setView("seriesDetail");
    renderSeriesDetail();
    showToast(t("previewSaved"), "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

async function exportSeriesDetailJianyingDraft() {
  const storyline = activeSeriesStoryline();
  if (!storyline?.cutlist?.segments?.length) return showToast(t("generateCutlistHint"), "error");
  const button = $("#seriesDetailExportJianyingBtn");
  setButtonBusy(button, true, t("exporting"));
  try {
    const data = await api("/api/editing/export-jianying", { method: "POST", body: JSON.stringify(seriesDetailPayload({ cutlist: storyline.cutlist, storylineId: storyline.id, templatePath: $("#seriesDetailTemplatePath")?.value.trim() || "", draftRoot: $("#seriesDetailDraftRootPath")?.value.trim() || "" })) });
    activeSeriesStorylineId = data.storylineId || storyline.id;
    await refresh();
    setView("seriesDetail");
    renderSeriesDetail();
    showToast(t("jianyingExported"), "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

function selectedSeries() {
  return seriesLibrary.find((item) => item.id === editingSeriesId) || seriesLibrary[0] || null;
}

function editingRequestPayload(extra = {}) {
  if (editingSourceType === "series") {
    return { sourceType: "series", seriesId: editingSeriesId, episodeLimit: Number(editingEpisodeLimit || 0), ...extra };
  }
  return { sourceType: "asset", assetId: editingAssetId, ...extra };
}
function renderEditingAssetSelect() {
  const sourceSelect = $("#editingSourceType");
  if (sourceSelect) {
    sourceSelect.value = editingSourceType;
    editingSourceType = sourceSelect.value || "asset";
  }
  const assetControls = $("#editingAssetControls");
  const seriesControls = $("#editingSeriesControls");
  if (assetControls) assetControls.hidden = editingSourceType !== "asset";
  if (seriesControls) seriesControls.hidden = editingSourceType !== "series";

  const assetSelect = $("#editingAssetSelect");
  if (assetSelect) {
    const previous = editingAssetId || assetSelect.value || assets[0]?.id || "";
    assetSelect.innerHTML = assets.map((asset) => `<option value="${escapeHtml(asset.id)}">${escapeHtml(getAssetTitle(asset))} · ${escapeHtml(assetWorkflowStatus(asset))}</option>`).join("");
    editingAssetId = assets.some((asset) => asset.id === previous) ? previous : (assets[0]?.id || "");
    assetSelect.value = editingAssetId;
  }

  const seriesSelect = $("#editingSeriesSelect");
  if (seriesSelect) {
    const previous = editingSeriesId || seriesSelect.value || seriesLibrary[0]?.id || "";
    seriesSelect.innerHTML = seriesLibrary.map((series) => `<option value="${escapeHtml(series.id)}">${escapeHtml(seriesTitle(series))} · 共 ${(series.episodes || []).length} 集</option>`).join("");
    editingSeriesId = seriesLibrary.some((series) => series.id === previous) ? previous : (seriesLibrary[0]?.id || "");
    seriesSelect.value = editingSeriesId;
  }
  const limitInput = $("#editingEpisodeLimit");
  if (limitInput) {
    limitInput.value = editingEpisodeLimit || 3;
  }
  renderEditingCurrentSource();
}

function renderEditingCurrentSource() {
  if (editingSourceType === "series") return renderEditingSeries();
  return renderEditingAsset(editingAssetId);
}

function renderEditingSeries() {
  const series = selectedSeries();
  const previewWrap = $("#editingAssetPreview");
  const checklist = $("#editingInputChecklist");
  if (!previewWrap || !checklist) return;
  if (!series) {
    previewWrap.className = "editingAssetPreview emptyState";
    previewWrap.innerHTML = "请选择剧集";
    checklist.innerHTML = "";
    editingStorylines = [];
    selectedStorylineId = "";
    editingCutlist = null;
    renderEditingStorylines();
    renderEditingCutlist();
    return;
  }
  const episodes = (series.episodes || []).slice(0, Number(editingEpisodeLimit || 0) || undefined);
  const firstPreview = episodes.find((ep) => ep.artifacts?.storyboard)?.artifacts?.storyboard;
  const readyReports = episodes.filter((ep) => (ep.artifacts?.reports || []).length).length;
  const readyTranscripts = episodes.filter((ep) => (ep.artifacts?.files || []).some((item) => /^transcript(_zh)?\.txt$/i.test(item.name))).length;
  previewWrap.className = "editingAssetPreview";
  previewWrap.innerHTML = `
    <div class="editingPreviewMedia">${firstPreview ? `<img src="${firstPreview.url}" alt="${escapeHtml(seriesTitle(series))}">` : `<span>${t("noStoryboard")}</span>`}</div>
    <div class="editingPreviewMeta"><strong>${escapeHtml(seriesTitle(series))}</strong><small>${formatText("analyzingFirstEpisodes", { count: episodes.length })}</small></div>
  `;
  checklist.innerHTML = `
    <div class="editingCheck ${episodes.length ? "ready" : "missing"}"><span>集数</span>${episodes.length} 集</div>
    <div class="editingCheck ${readyReports ? "ready" : "missing"}"><span>报告</span>${readyReports}/${episodes.length} 集已生成</div>
    <div class="editingCheck ${readyTranscripts ? "ready" : "missing"}"><span>字幕</span>${readyTranscripts}/${episodes.length} 集已转写</div>
    <div class="editingCheck ready"><span>跨集</span>剪辑清单会保留集数来源</div>
  `;
  renderEditingStorylines();
  renderEditingCutlist();
}

function editingFileLink(item) {
  if (!item) return "";
  return `<a href="${item.url}" target="_blank" title="${escapeHtml(item.path || item.name)}">${escapeHtml(item.name)}</a>`;
}

function renderEditingAsset(assetId) {
  editingAssetId = assetId || "";
  const asset = assets.find((item) => item.id === editingAssetId);
  const previewWrap = $("#editingAssetPreview");
  const checklist = $("#editingInputChecklist");
  if (!previewWrap || !checklist) return;
  if (!asset) {
    previewWrap.className = "editingAssetPreview emptyState";
    previewWrap.innerHTML = "请选择素材";
    checklist.innerHTML = "";
    editingStorylines = [];
    selectedStorylineId = "";
    editingCutlist = null;
    renderEditingStorylines();
    renderEditingCutlist();
    return;
  }
  const preview = previewImage(asset);
  const report = preferredReportLink(asset);
  const transcript = preferredTranscriptLink(asset, "zh") || preferredTranscriptLink(asset, "original");
  const frames = asset.artifacts?.frames || [];
  previewWrap.className = "editingAssetPreview";
  previewWrap.innerHTML = `
    <div class="editingPreviewMedia">${preview ? `<img src="${preview.url}" alt="${escapeHtml(getAssetTitle(asset))}">` : `<span>${t("noStoryboard")}</span>`}</div>
    <div class="editingPreviewMeta"><strong title="${escapeHtml(getAssetTitle(asset))}">${escapeHtml(getAssetTitle(asset))}</strong><small>${escapeHtml(assetWorkflowStatus(asset))}</small></div>
  `;
  checklist.innerHTML = `
    <div class="editingCheck ${report ? "ready" : "missing"}"><span>${t("report")}</span>${report ? editingFileLink(report) : t("notGenerated")}</div>
    <div class="editingCheck ${transcript ? "ready" : "missing"}"><span>${t("subtitles")}</span>${transcript ? editingFileLink(transcript) : t("notTranscribed")}</div>
    <div class="editingCheck ${frames.length ? "ready" : "missing"}"><span>${t("frames")}</span>${frames.length ? formatText("frameCount", { count: frames.length }) : t("noFrames")}</div>
    <div class="editingCheck ready"><span>${t("tag")}</span>${Object.keys(asset.tags || {}).length ? t("read") : t("optional")}</div>
  `;
  renderEditingStorylines();
  renderEditingCutlist();
}

function setEditingStatus(message, type = "info") {
  const outputs = $("#editingOutputs");
  if (!outputs) return;
  outputs.innerHTML = `<div class="editingStatus ${type}">${escapeHtml(message || "")}</div>`;
}

function selectedStoryline() {
  return editingStorylines.find((item, index) => (item.id || `story-${index + 1}`) === selectedStorylineId) || editingStorylines[0] || null;
}

function renderEditingStorylines() {
  const list = $("#storylineList");
  if (!list) return;
  if (!editingStorylines.length) {
    list.className = "storylineList emptyState";
    list.innerHTML = "等待生成故事线";
    selectedStorylineId = "";
    return;
  }
  list.className = "storylineList";
  list.innerHTML = editingStorylines.map((item, index) => {
    const id = item.id || `story-${index + 1}`;
    const selected = selectedStorylineId === id || (!selectedStorylineId && index === 0);
    if (selected) selectedStorylineId = id;
    return `<button class="storylineCard ${selected ? "active" : ""}" type="button" data-storyline-id="${escapeHtml(id)}"><span class="storylineIndex">${String(index + 1).padStart(2, "0")}</span><strong>${escapeHtml(item.title || `故事线 ${index + 1}`)}</strong><small>${escapeHtml(item.hook || item.reason || "")}</small><em>${escapeHtml(item.duration || item.targetDuration || "投流剪辑")}</em></button>`;
  }).join("");
  list.querySelectorAll(".storylineCard").forEach((button) => {
    button.addEventListener("click", () => {
      selectedStorylineId = button.dataset.storylineId || "";
      editingCutlist = null;
      renderEditingStorylines();
      renderEditingCutlist();
    });
  });
}

function editingEpisodeLabel(episodeId) {
  if (!episodeId) return "";
  const series = selectedSeries();
  const episode = (series?.episodes || []).find((item) => String(item.id) === String(episodeId));
  if (episode) return `第 ${episode.episodeNo || "?"} 集`;
  return String(episodeId);
}

function editingRoleLabel(role) {
  const map = {
    hook: "钩子",
    conflict: "冲突",
    twist: "反转",
    payoff: "爽点/回收",
    promise: "承诺",
    CTA: "转化引导",
    cta: "转化引导",
  };
  return map[String(role || "").trim()] || String(role || "片段");
}

function renderEditingCutlist() {
  const panel = $("#cutlistPanel");
  if (!panel) return;
  if (!editingCutlist?.segments?.length) {
    panel.className = "cutlistPanel emptyState";
    panel.innerHTML = selectedStoryline() ? "点击“生成剪辑清单”后展示时间线" : "请选择故事线";
    return;
  }
  panel.className = "cutlistPanel";
  const segments = editingCutlist.segments || [];
  panel.innerHTML = `
    <div class="cutlistSummary">
      <strong>${escapeHtml(editingCutlist.title || selectedStoryline()?.title || "剪辑清单")}</strong>
      <span>${segments.length} 个片段 · ${escapeHtml(editingCutlist.estimatedDuration || "30-60 秒")}</span>
    </div>
    <div class="cutSegmentList">
      ${segments.map((seg, index) => {
        const source = `${seg.episodeId ? `${editingEpisodeLabel(seg.episodeId)} · ` : ""}${seg.sourceStart || "00:00.00"} - ${seg.sourceEnd || "00:00.00"}`;
        const caption = seg.caption ? `<div class="cutSegmentCaption"><span>字幕</span>${escapeHtml(seg.caption)}</div>` : "";
        const reason = seg.reason ? `<p>${escapeHtml(seg.reason)}</p>` : "";
        return `<article class="cutSegment"><div class="cutSegmentTime"><span>${String(index + 1).padStart(2, "0")}</span>${escapeHtml(source)}</div><div class="cutSegmentRole">${escapeHtml(editingRoleLabel(seg.role || seg.title))}</div>${reason}${caption}</article>`;
      }).join("")}
    </div>`;
}

function hasEditingSource() {
  if (editingSourceType === "series") return Boolean(editingSeriesId);
  return Boolean(editingAssetId);
}

async function generateEditingStorylines() {
  if (!requireModelKey()) return;
  if (!hasEditingSource()) return showToast("请选择素材或剧集", "error");
  const button = $("#generateStorylinesBtn");
  setButtonBusy(button, true, t("generating"));
  editingStorylines = [];
  selectedStorylineId = "";
  editingCutlist = null;
  setPanelLoading("#storylineList", "AI 正在生成投流故事线，通常需要几十秒...");
  renderEditingCutlist();
  setEditingStatus("正在生成投流故事线...");
  showToast("正在生成投流故事线...", "info");
  try {
    const data = await api("/api/editing/storylines", { method: "POST", body: JSON.stringify(editingRequestPayload({ apiKey: modelKey() })) });
    editingStorylines = data.storylines || [];
    selectedStorylineId = editingStorylines[0]?.id || "";
    editingCutlist = null;
    renderEditingStorylines();
    renderEditingCutlist();
    setEditingStatus("故事线已生成", "success");
    showToast("故事线已生成", "success");
  } catch (err) {
    renderEditingStorylines();
    setEditingStatus(err.message, "error");
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

async function generateEditingCutlist() {
  if (!requireModelKey()) return;
  if (!hasEditingSource()) return showToast("请选择素材或剧集", "error");
  const storyline = selectedStoryline();
  if (!storyline) return showToast(t("selectStoryline"), "error");
  const button = $("#generateCutlistBtn");
  setButtonBusy(button, true, t("generating"));
  setPanelLoading("#cutlistPanel", "AI 正在生成剪辑清单...");
  setEditingStatus("正在生成剪辑清单...");
  try {
    const data = await api("/api/editing/cutlist", { method: "POST", body: JSON.stringify(editingRequestPayload({ storyline, apiKey: modelKey() })) });
    editingCutlist = data.cutlist || data;
    renderEditingCutlist();
    setEditingStatus("剪辑清单已生成", "success");
    showToast("剪辑清单已生成", "success");
  } catch (err) {
    renderEditingCutlist();
    setEditingStatus(err.message, "error");
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

function renderEditingOutputLinks(data) {
  const outputs = $("#editingOutputs");
  if (!outputs) return;
  const links = [];
  if (data.previewUrl) links.push(`<a href="${data.previewUrl}" target="_blank">打开预览视频</a>`);
  if (data.cutlistUrl) links.push(`<a href="${data.cutlistUrl}" target="_blank">cutlist.json</a>`);
  if (data.srtUrl) links.push(`<a href="${data.srtUrl}" target="_blank">字幕 SRT</a>`);
  if (data.packageUrl) links.push(`<a href="${data.packageUrl}" target="_blank">剪映草稿包</a>`);
  const preview = data.previewUrl ? `<div class="editingPreviewVideo"><video src="${data.previewUrl}" controls preload="metadata"></video></div>` : "";
  outputs.innerHTML = `${preview}<div class="editingOutputLinks">${links.join("")}</div>${data.note ? `<p class="editingNote">${escapeHtml(data.note)}</p>` : ""}`;
}

async function renderEditingPreviewVideo() {
  if (!hasEditingSource() || !editingCutlist?.segments?.length) return showToast(t("generateCutlistHint"), "error");
  const button = $("#renderPreviewBtn");
  setButtonBusy(button, true, t("rendering"));
  setEditingStatus("正在渲染预览视频...");
  try {
    const data = await api("/api/editing/render-preview", { method: "POST", body: JSON.stringify(editingRequestPayload({ cutlist: editingCutlist })) });
    renderEditingOutputLinks(data);
    showToast("预览视频已生成，可直接播放", "success");
  } catch (err) {
    setEditingStatus(err.message, "error");
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

async function exportJianyingDraft() {
  if (!hasEditingSource() || !editingCutlist?.segments?.length) return showToast(t("generateCutlistHint"), "error");
  const button = $("#exportJianyingBtn");
  setButtonBusy(button, true, t("exporting"));
  setEditingStatus("正在导出剪映草稿包...");
  try {
    const data = await api("/api/editing/export-jianying", { method: "POST", body: JSON.stringify(editingRequestPayload({ cutlist: editingCutlist, storylineId: selectedStorylineId, templatePath: $("#jianyingTemplatePath")?.value.trim() || "", draftRoot: $("#jianyingDraftRootPath")?.value.trim() || "" })) });
    renderEditingOutputLinks(data);
    showToast("剪映草稿包已导出", "success");
  } catch (err) {
    setEditingStatus(err.message, "error");
    showToast(err.message, "error");
  } finally {
    setButtonBusy(button, false);
  }
}

function splitTagPath(value) {
  const parts = Array.isArray(value) ? value : String(value || "").split(/\s*-\s*/);
  return parts.map((part) => String(part || "").trim()).filter(Boolean).slice(0, 5);
}

function tagPathKey(value) {
  return splitTagPath(value).join("-");
}

function normalizeTagDefinitionsInput(definitions = {}) {
  const out = {};
  Object.entries(definitions || {}).forEach(([category, values]) => {
    const cleanCategory = String(category || "").trim();
    if (!cleanCategory || !values || typeof values !== "object") return;
    out[cleanCategory] = {};
    Object.entries(values).forEach(([tag, definition]) => {
      const cleanTag = String(tag || "").trim();
      if (!cleanTag) return;
      out[cleanCategory][cleanTag] = String(definition || "").trim();
    });
  });
  return out;
}

function previewTagDefinition(category, tag) {
  return currentTagDefinitions?.[category]?.[tag] || "";
}

function setPreviewTagDefinition(category, tag, definition) {
  const cleanCategory = String(category || "").trim();
  const cleanTag = String(tag || "").trim();
  if (!cleanCategory || !cleanTag) return;
  currentTagDefinitions[cleanCategory] ||= {};
  currentTagDefinitions[cleanCategory][cleanTag] = String(definition || "").trim();
}

function removePreviewTagDefinition(category, tag) {
  if (!currentTagDefinitions?.[category]) return;
  delete currentTagDefinitions[category][tag];
  if (!Object.keys(currentTagDefinitions[category]).length) delete currentTagDefinitions[category];
}

function seedPreviewDefinitionsFromSchema(tags = currentTags) {
  const defs = {};
  Object.entries(tags || {}).forEach(([category, values]) => {
    (values || []).forEach((value) => {
      const path = splitTagPath(value);
      const flat = tagPathKey(path);
      path.forEach((part) => {
        const existing = tagDefinitions?.[category]?.[part] || "";
        if (existing) {
          defs[category] ||= {};
          defs[category][part] = existing;
        }
      });
      const whole = tagDefinitions?.[category]?.[flat] || "";
      if (whole) {
        defs[category] ||= {};
        defs[category][flat] = whole;
      }
    });
  });
  currentTagDefinitions = defs;
}
function levelLabel(level) {
  return ({ 1: "二级", 2: "三级", 3: "四级", 4: "五级", 5: "六级" })[Number(level)] || `${Number(level) + 1}级`;
}

function categoryLevelLabel(category, level) {
  return hierarchicalSchema?.[category]?.levelLabels?.[String(level)] || categoryLevelNames?.[category]?.[String(level)] || levelLabel(level);
}

function uniqueTags(tags) {
  const out = {};
  Object.entries(tags || {}).forEach(([category, values]) => {
    const seen = new Set();
    const clean = [];
    (values || []).forEach((value) => {
      const path = splitTagPath(value);
      const key = path.join("-");
      if (key && !seen.has(key)) {
        seen.add(key);
        clean.push(path);
      }
    });
    if (clean.length) out[category] = clean;
  });
  return out;
}

function renderTagEditor(tags = currentTags) {
  currentTags = uniqueTags(tags);
  const wrap = $("#tagEditor");
  wrap.innerHTML = "";
  const categories = Array.from(new Set([...Object.keys(schema), ...Object.keys(currentTags)]));
  categories.forEach((category) => {
    const tpl = $("#categoryTemplate").content.cloneNode(true);
    tpl.querySelector("h4").textContent = displayCategory(category);
    const chips = tpl.querySelector(".chips");
    (currentTags[category] || []).forEach((tag) => chips.appendChild(createChip(category, tag)));
    tpl.querySelector(".addTag").addEventListener("click", () => {
      const tag = prompt(`添加到「${category}」的标签路径，用 - 连接各层标签`);
      if (!tag) return;
      const path = splitTagPath(tag);
      const key = tagPathKey(path);
      currentTags[category] ||= [];
      if (!currentTags[category].some((item) => tagPathKey(item) === key)) currentTags[category].push(path);
      renderTagEditor();
    });
    wrap.appendChild(tpl);
  });
}

function createChip(category, tag) {
  const path = splitTagPath(tag);
  const key = tagPathKey(path);
  const chip = document.createElement("span");
  chip.className = "chip tagChainChip";
  chip.innerHTML = `
    <span class="tagChain" title="点击编辑整条标签路径">${path.map((part, index) => { const definition = tagPathNodeDefinition(category, part, path, index); return `<span class="tagChainNode editable" data-index="${index}" data-definition="${escapeHtml(definition)}" title="${escapeHtml(definition)}">${escapeHtml(displayTag(category, part))}</span>`; }).join(`<span class="tagChainLine"></span>`)}</span>
    <button title="删除">×</button>
  `;
  chip.querySelector("button").addEventListener("click", (event) => {
    event.stopPropagation();
    currentTags[category] = (currentTags[category] || []).filter((item) => tagPathKey(item) !== key);
    renderTagEditor();
  });
  chip.querySelector(".tagChain").addEventListener("click", () => openPreviewTagModal(category, key, null));
  chip.querySelectorAll(".tagChainNode").forEach((node) => {
    node.addEventListener("click", (event) => {
      event.stopPropagation();
      openPreviewTagModal(category, key, Number(node.dataset.index || 0));
    });
  });
  return chip;
}

function currentPreviewTagPath(category, key) {
  return splitTagPath((currentTags[category] || []).find((item) => tagPathKey(item) === key) || key);
}

function closePreviewTagModal() {
  editingPreviewTag = null;
  const modal = $("#previewTagModal");
  if (modal) modal.hidden = true;
}

function openPreviewTagModal(category, key, focusIndex = null) {
  const path = currentPreviewTagPath(category, key);
  if (!path.length) return;
  editingPreviewTag = { category, key, focusIndex };
  const single = Number.isInteger(focusIndex);
  $("#previewTagModalTitle").textContent = single ? "编辑单个标签" : "编辑标签路径";
  $("#previewTagModalMeta").textContent = single ? `${category} / ${categoryLevelLabel(category, focusIndex + 1)}` : `${category} / 完整标签链`;
  const rows = single ? [{ part: path[focusIndex], index: focusIndex }] : path.map((part, index) => ({ part, index }));
  $("#previewTagRows").innerHTML = rows.map(({ part, index }) => {
    const definition = tagPathNodeDefinition(category, part, path, index).replace(/^暂无定义：[^「]+「[^」]+」$/, "");
    return `
      <div class="previewTagRow" data-index="${index}">
        <div class="previewTagRowHead">
          <strong>${escapeHtml(categoryLevelLabel(category, index + 1))}</strong>
          <span>${escapeHtml(category)}</span>
        </div>
        <label class="field compactField">
          <span>标签名称</span>
          <input class="previewTagName" value="${escapeHtml(part)}" placeholder="填写标签名称">
        </label>
        <label class="field compactField">
          <span>标签定义</span>
          <textarea class="previewTagDefinition" rows="3" placeholder="填写这个层级标签的判定标准、适用场景或边界">${escapeHtml(definition)}</textarea>
        </label>
      </div>
    `;
  }).join("");
  $("#previewTagModal").hidden = false;
}

function savePreviewTagModal() {
  if (!editingPreviewTag) return;
  const { category, key, focusIndex } = editingPreviewTag;
  const oldPath = currentPreviewTagPath(category, key);
  const nextPath = [...oldPath];
  const rows = Array.from(document.querySelectorAll("#previewTagRows .previewTagRow"));
  rows.forEach((row) => {
    const index = Number(row.dataset.index || 0);
    const oldName = oldPath[index] || "";
    const name = row.querySelector(".previewTagName")?.value.trim() || oldName;
    const definition = row.querySelector(".previewTagDefinition")?.value.trim() || "";
    nextPath[index] = name;
    if (oldName && oldName !== name && previewTagDefinition(category, oldName)) removePreviewTagDefinition(category, oldName);
    setPreviewTagDefinition(category, name, definition || tagDefinition(category, name));
  });
  const nextKey = tagPathKey(nextPath);
  if (!nextKey) {
    showToast("请至少保留一个标签名称", "error");
    return;
  }
  currentTags[category] = (currentTags[category] || []).map((item) => tagPathKey(item) === key ? nextPath : item);
  currentTags = uniqueTags(currentTags);
  closePreviewTagModal();
  renderTagEditor();
  showToast(Number.isInteger(focusIndex) ? "已更新标签" : "已更新标签路径", "success");
}
function renderAssetCard(asset) {
  const preview = previewImage(asset);
  const card = document.createElement("article");
  card.className = "materialCard materialCardLink";
  card.id = `asset-${asset.id}`;
  card.tabIndex = 0;
  card.setAttribute("role", "button");
  card.setAttribute("aria-label", `打开素材：${getAssetTitle(asset)}`);
  card.innerHTML = `
    <div class="materialPreview storyboardPreview">
      ${preview ? `<img src="${preview.url}" alt="${escapeHtml(getAssetTitle(asset))}">` : `<span>${t("noStoryboard")}</span>`}
    </div>
    <div class="materialBody compactMaterialBody">
      <h3 title="${escapeHtml(getAssetTitle(asset))}">${escapeHtml(getAssetTitle(asset))}</h3>
      <p class="materialStatus" title="${escapeHtml(assetWorkflowStatus(asset))}">${escapeHtml(assetWorkflowStatus(asset))}</p>
    </div>
  `;
  card.addEventListener("click", () => openAssetForTagging(asset.id));
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openAssetForTagging(asset.id);
    }
  });
  return card;
}
function renderTaskQueue() {
  const wrap = $("#taskQueue");
  if (!wrap) return;
  const visible = (pipelineTasks || []).filter((task) => ["排队中", "处理中", "失败", "完成"].includes(task.status)).slice(0, 8);
  wrap.hidden = !visible.length;
  if (!visible.length) {
    wrap.innerHTML = "";
    return;
  }
  wrap.innerHTML = `
    <div class="taskQueueHead">
      <div>
        <p class="eyebrow">拉片任务</p>
        <h3>排期拉片中</h3>
      </div>
      <span>${visible.length} 个任务</span>
    </div>
    <div class="taskList">
      ${visible.map((task) => `
        <div class="taskItem ${task.status === "失败" ? "failed" : task.status === "完成" ? "done" : ""}">
          <div class="taskItemHead">
            <strong title="${escapeHtml(task.title || task.assetId)}">${escapeHtml(task.title || task.assetId || "未命名任务")}</strong>
            <span>${escapeHtml(task.status || "排队中")}</span>
          </div>
          <div class="taskStage">${escapeHtml(task.stage || "等待中")}</div>
          <div class="taskProgress"><i style="width:${Math.min(Math.max(Number(task.progress || 0), 0), 100)}%"></i></div>
          ${task.error ? `<div class="taskError">${escapeHtml(task.error)}</div>` : ""}
        </div>
      `).join("")}
    </div>
  `;
}

async function loadTasks() {
  try {
    const data = await api("/api/tasks");
    pipelineTasks = data.tasks || [];
    renderTaskQueue();
    return pipelineTasks;
  } catch (err) {
    return pipelineTasks;
  }
}

function startTaskPolling() {
  if (taskPollTimer) return;
  taskPollTimer = window.setInterval(async () => {
    const tasks = await loadTasks();
    const active = tasks.some((task) => ["排队中", "处理中"].includes(task.status));
    if (tasks.length) {
      const db = await api("/api/assets");
      assets = db.assets || [];
      const seriesData = await api("/api/series");
      seriesLibrary = seriesData.series || [];
      renderAssetSelect();
      renderEditingAssetSelect();
      renderUploadAssets();
      renderSeriesLibrary();
      const selected = $("#assetSelect")?.value;
      if (selected && tasks.some((task) => task.assetId === selected)) {
        applySelectedAsset(selected);
      } else if (selected) {
        renderSelectedAssetPanel(assets.find((item) => item.id === selected) || null);
      }
    }
    if (!active) {
      window.clearInterval(taskPollTimer);
      taskPollTimer = null;
    }
  }, 2500);
}
function assetTitleSearchText(asset) {
  return [
    asset.id,
    getAssetTitle(asset),
    getAssetSubtitle(asset),
    asset.sourceName || "",
  ].join(" ").toLowerCase();
}

function assetTagEntries(asset) {
  return Object.entries(asset.tags || {}).flatMap(([category, tags]) => {
    const paths = Array.isArray(tags) ? tags : [];
    return paths.map((tag) => {
      const path = splitTagPath(tag);
      return {
        category,
        path,
        key: tagPathKey(path),
        text: `${category} ${displayCategory(category)} ${path.join(" ")} ${path.map((part) => displayTag(category, part)).join(" ")} ${path.join("-")}`.toLowerCase(),
      };
    });
  });
}

function tagFilterOptions() {
  const categories = categoryOrder.length ? categoryOrder.filter((category) => hierarchicalSchema?.[category] || schema?.[category]) : Object.keys({ ...(schema || {}), ...(hierarchicalSchema || {}) });
  return categories.flatMap((category) => {
    const info = hierarchicalSchema?.[category] || { levels: Number(categoryLevels?.[category] || 1), tagsByLevel: { "1": schema?.[category] || [] } };
    const levels = Math.min(Math.max(Number(info.levels || categoryLevels?.[category] || 1), 1), 5);
    const rows = [];
    for (let level = 1; level <= levels; level += 1) {
      const tags = Array.from(new Set(info.tagsByLevel?.[String(level)] || []));
      tags.forEach((tag) => {
        rows.push({
          category,
          level,
          levelName: categoryLevelLabel(category, level),
          tag,
          searchText: `${category} ${displayCategory(category)} ${categoryLevelLabel(category, level)} ${tag} ${displayTag(category, tag)}`.toLowerCase(),
        });
      });
    }
    return rows;
  });
}

function renderAssetTagDropdown(forceOpen = false) {
  const dropdown = $("#assetTagDropdown");
  if (!dropdown) return;
  const query = (assetTagSearchQuery || "").trim().toLowerCase();
  const terms = query.split(/[\s/]+/).filter(Boolean);
  const matchingOptions = tagFilterOptions().filter((item) => terms.every((term) => item.searchText.includes(term))).slice(0, 260);
  if (!forceOpen && dropdown.hidden) return;
  dropdown.hidden = false;
  if (!matchingOptions.length) {
    dropdown.innerHTML = `<div class="tagFilterEmpty">没有匹配的标签</div>`;
    return;
  }
  const grouped = new Map();
  matchingOptions.forEach((item) => {
    if (!grouped.has(item.category)) grouped.set(item.category, []);
    grouped.get(item.category).push(item);
  });
  const orderedCategories = (categoryOrder.length ? categoryOrder : Array.from(grouped.keys())).filter((category) => grouped.has(category));
  const isSearching = terms.length > 0;
  dropdown.innerHTML = orderedCategories.map((category) => {
    const items = grouped.get(category) || [];
    const collapsed = !isSearching && assetTagCollapsedCategories.has(category);
    const byLevel = new Map();
    items.forEach((item) => {
      if (!byLevel.has(item.level)) byLevel.set(item.level, []);
      byLevel.get(item.level).push(item);
    });
    const levelsHtml = Array.from(byLevel.entries()).sort((a, b) => Number(a[0]) - Number(b[0])).map(([level, levelItems]) => `
      <div class="tagFilterLevelBlock">
        <div class="tagFilterLevelName">${escapeHtml(categoryLevelLabel(category, Number(level)))}</div>
        <div class="tagFilterPillList">
          ${levelItems.map((item) => {
            const active = selectedAssetTagFilter && selectedAssetTagFilter.category === item.category && Number(selectedAssetTagFilter.level) === Number(item.level) && selectedAssetTagFilter.tag === item.tag;
            return `<button class="tagFilterPill ${active ? "active" : ""}" type="button" data-category="${escapeHtml(item.category)}" data-level="${item.level}" data-tag="${escapeHtml(item.tag)}" title="${escapeHtml(item.category)} / ${escapeHtml(item.levelName)} / ${escapeHtml(item.tag)}">${escapeHtml(displayTag(item.category, item.tag))}</button>`;
          }).join("")}
        </div>
      </div>
    `).join("");
    return `
      <section class="tagFilterCategory ${collapsed ? "collapsed" : ""}" data-category="${escapeHtml(category)}">
        <button class="tagFilterCategoryHead" type="button" data-category="${escapeHtml(category)}" aria-expanded="${String(!collapsed)}">
          <span class="tagFilterChevron" aria-hidden="true"></span>
          <strong>${escapeHtml(displayCategory(category))}</strong>
          <small>${countText(items.length)}</small>
        </button>
        ${collapsed ? "" : `<div class="tagFilterCategoryBody">${levelsHtml}</div>`}
      </section>
    `;
  }).join("");
  dropdown.querySelectorAll(".tagFilterCategoryHead").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const category = button.dataset.category || "";
      if (assetTagCollapsedCategories.has(category)) assetTagCollapsedCategories.delete(category);
      else assetTagCollapsedCategories.add(category);
      renderAssetTagDropdown(true);
    });
  });
  dropdown.querySelectorAll(".tagFilterPill").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      selectAssetTagFilter(button.dataset.category, Number(button.dataset.level || 1), button.dataset.tag);
    });
  });
}

function openAssetTagDropdown() {
  renderAssetTagDropdown(true);
}

function closeAssetTagDropdown() {
  const dropdown = $("#assetTagDropdown");
  if (dropdown) dropdown.hidden = true;
}

function selectAssetTagFilter(category, level, tag) {
  selectedAssetTagFilter = { category, level, tag };
  assetTagSearchQuery = `${displayCategory(category)} / ${categoryLevelLabel(category, level)} / ${displayTag(category, tag)}`;
  const input = $("#assetTagSearchInput");
  if (input) input.value = assetTagSearchQuery;
  closeAssetTagDropdown();
  renderUploadAssets();
}

function clearAssetFilters() {
  assetNameSearchQuery = "";
  assetTagSearchQuery = "";
  selectedAssetTagFilter = null;
  if ($("#assetNameSearchInput")) $("#assetNameSearchInput").value = "";
  if ($("#assetTagSearchInput")) $("#assetTagSearchInput").value = "";
  closeAssetTagDropdown();
  renderUploadAssets();
}

function assetMatchesSelectedTag(asset) {
  if (!selectedAssetTagFilter) return true;
  const { category, level, tag } = selectedAssetTagFilter;
  return assetTagEntries(asset).some((entry) => entry.category === category && entry.path[Number(level) - 1] === tag);
}

function assetMatchesTypedTag(asset) {
  const query = (assetTagSearchQuery || "").trim().toLowerCase();
  if (!query || selectedAssetTagFilter) return true;
  const terms = query.split(/[\s/]+/).filter(Boolean);
  return assetTagEntries(asset).some((entry) => terms.every((term) => entry.text.includes(term)));
}

function filteredUploadAssets() {
  const nameQuery = (assetNameSearchQuery || "").trim().toLowerCase();
  const nameTerms = nameQuery.split(/\s+/).filter(Boolean);
  return assets.filter((asset) => {
    const nameOk = !nameTerms.length || nameTerms.every((term) => assetTitleSearchText(asset).includes(term));
    return nameOk && assetMatchesSelectedTag(asset) && assetMatchesTypedTag(asset);
  });
}

function renderUploadAssets() {
  const grid = $("#assetGrid");
  if (!grid) return;
  const visibleAssets = filteredUploadAssets();
  const filtered = Boolean((assetNameSearchQuery || "").trim() || (assetTagSearchQuery || "").trim() || selectedAssetTagFilter);
  $("#assetCount").textContent = filtered ? filteredCountText(visibleAssets.length, assets.length) : countText(assets.length);
  grid.innerHTML = "";
  if (!assets.length) {
    grid.innerHTML = `<div class="emptyState">${t("noAssets")}</div>`;
    return;
  }
  if (!visibleAssets.length) {
    grid.innerHTML = `<div class="emptyState">没有找到匹配的素材。换个素材名或标签试试。</div>`;
    return;
  }
  visibleAssets.forEach((asset) => grid.appendChild(renderAssetCard(asset)));
}
const PROMPT_FIELD_IDS = [
  "reportSystem",
  "reportUser",
  "tagSystem",
  "tagUser",
  "storylineSystem",
  "storylineUser",
  "cutlistSystem",
  "cutlistUser",
  "transcribeSystem",
  "transcribeUser",
  "translateSystem",
  "translateUser",
  "transcriptRepairSystem",
  "transcriptRepairUser",
];

function fillPromptForm(data = promptConfig) {
  promptConfig = data || promptConfig;
  const prompts = promptConfig.prompts || {};
  const meta = promptConfig.meta || {};
  if (!$("#reportSystemPrompt")) return;
  $("#promptSkillName").textContent = meta.skillName || "Video AI Analysis Skill V1";
  $("#promptModelName").textContent = meta.model || "gemini-3.1-pro-preview";
  $("#promptEndpoint").textContent = meta.endpoint || "https://ai.pocketcity.com/v1/chat/completions";
  PROMPT_FIELD_IDS.forEach((key) => {
    const field = $(`#${key}Prompt`);
    if (field) field.value = prompts[key] || "";
  });
}

function readPromptForm() {
  return PROMPT_FIELD_IDS.reduce((result, key) => {
    const field = $(`#${key}Prompt`);
    result[key] = field ? field.value : "";
    return result;
  }, {});
}

async function loadPrompts() {
  const data = await api("/api/prompts");
  fillPromptForm(data);
}

async function savePrompts() {
  $("#promptStatus").textContent = t("promptSaving");
  try {
    const data = await api("/api/prompts", {
      method: "POST",
      body: JSON.stringify({ prompts: readPromptForm() }),
    });
    fillPromptForm(data);
    $("#promptStatus").textContent = t("promptSaved");
  } catch (err) {
    showToast(err.message, "error");
    $("#promptStatus").textContent = err.message;
  }
}

async function resetPrompts() {
  const ok = window.confirm(t("resetPromptConfirm"));
  if (!ok) return;
  const defaults = promptConfig.defaults || {};
  fillPromptForm({ ...promptConfig, prompts: defaults });
  await savePrompts();
}
function localizationLocale() {
  return currentLocale === "en" ? "en" : "zh";
}

function categoryLocalization(category) {
  return tagLocalization?.categories?.[category] || {};
}

function tagLocalizationEntry(category, tag) {
  return tagLocalization?.tags?.[category]?.[tag] || {};
}

function localizedName(entry, fallback) {
  const names = entry?.names || {};
  return names[localizationLocale()] || names.zh || fallback || "";
}

function localizedDefinition(entry, fallback = "") {
  const defs = entry?.definitions || {};
  return defs[localizationLocale()] || defs.zh || fallback || "";
}
function isLocalizationFallback(entry, field = "names") {
  const locale = localizationLocale();
  if (locale === "zh") return false;
  const values = entry?.[field] || {};
  return !String(values[locale] || "").trim() && Boolean(String(values.zh || "").trim());
}

function localizationFallbackBadge(entry, fields = ["names"]) {
  if (!fields.some((field) => isLocalizationFallback(entry, field))) return "";
  return `<span class="localizationFallbackBadge" title="${escapeHtml(t("missingLocalization"))}">${escapeHtml(t("missingLocalizationShort"))}</span>`;
}

function localizationFallbackTitle(entry, baseTitle = "", fields = ["names"]) {
  if (!fields.some((field) => isLocalizationFallback(entry, field))) return baseTitle;
  const hint = t("missingLocalization");
  return baseTitle ? `${baseTitle}\n${hint}` : hint;
}

function displayCategory(category) {
  return localizedName(categoryLocalization(category), category);
}

function displayTag(category, tag) {
  return localizedName(tagLocalizationEntry(category, tag), tag);
}

function displayTagPath(category, value) {
  return splitTagPath(value).map((part) => displayTag(category, part)).join("-");
}

function tagDefinition(category, tag) {
  return previewTagDefinition(category, tag) || localizedDefinition(tagLocalizationEntry(category, tag), tagDefinitions?.[category]?.[tag] || "") || tagDefinitions?.[category]?.[tag] || "";
}

function tagPathNodeDefinition(category, part, path, index) {
  const direct = tagDefinition(category, part);
  if (direct) return direct;
  const whole = tagDefinition(category, tagPathKey(path));
  if (whole) return whole;
  const levelName = categoryLevelLabel(category, index + 1);
  return `暂无定义：${levelName}「${part}」`;
}

function categoryDefinition(category) {
  return localizedDefinition(categoryLocalization(category), categoryDefinitions?.[category] || "") || categoryDefinitions?.[category] || "";
}

function openCategoryModal(category) {
  const localization = categoryLocalization(category);
  editingDefinition = { type: "category", category };
  hideMergePanel();
  $("#definitionModalTitle").textContent = "编辑一级标签";
  $("#definitionModalMeta").textContent = isLocalizationFallback(localization, "names") || isLocalizationFallback(localization, "definitions")
    ? `${displayCategory(category)} · ${t("showingFallbackLocalization", { locale: t("localeName") })}`
    : displayCategory(category);
  $("#definitionModalName").value = displayCategory(category);
  $("#definitionModalText").value = categoryDefinition(category);
  $("#deleteDefinitionTagBtn").textContent = "删除";
  $("#mergeDefinitionTagBtn").hidden = true;
  $("#transferDefinitionTagBtn").hidden = true;
  $("#definitionModal").hidden = false;
}

function openDefinitionModal(category, tag, level = 1) {
  const localization = tagLocalizationEntry(category, tag);
  editingDefinition = { type: "tag", category, tag, level: Number(level || 1) };
  hideMergePanel();
  $("#definitionModalTitle").textContent = "编辑子标签";
  $("#definitionModalMeta").textContent = isLocalizationFallback(localization, "names") || isLocalizationFallback(localization, "definitions")
    ? `${displayCategory(category)} · ${t("showingFallbackLocalization", { locale: t("localeName") })}`
    : displayCategory(category);
  $("#definitionModalName").value = displayTag(category, tag);
  $("#definitionModalText").value = tagDefinition(category, tag);
  $("#deleteDefinitionTagBtn").textContent = "删除";
  $("#mergeDefinitionTagBtn").hidden = false;
  $("#transferDefinitionTagBtn").hidden = false;
  $("#definitionModal").hidden = false;
}

function closeDefinitionModal() {
  $("#definitionModal").hidden = true;
  editingDefinition = null;
  hideMergePanel();
}

function bindBackdropClose(modalSelector, closeFn) {
  const modal = $(modalSelector);
  if (!modal) return;
  let startedOnBackdrop = false;
  modal.addEventListener("pointerdown", (event) => {
    startedOnBackdrop = event.target === modal;
  });
  modal.addEventListener("click", (event) => {
    if (startedOnBackdrop && event.target === modal) closeFn();
    startedOnBackdrop = false;
  });
}

function tagLevelsFor(category, tag) {
  const byLevel = hierarchicalSchema?.[category]?.tagsByLevel || {};
  return Object.entries(byLevel)
    .filter(([, values]) => (values || []).includes(tag))
    .map(([level]) => Number(level))
    .filter(Boolean)
    .sort((a, b) => a - b);
}

function effectiveTagLevel(category, tag, preferred = 1) {
  const levels = tagLevelsFor(category, tag);
  const numeric = Number(preferred || 1);
  if (levels.includes(numeric)) return numeric;
  return levels[0] || numeric;
}

function sameLevelMergeTargets(category, tag, level) {
  const actualLevel = effectiveTagLevel(category, tag, level);
  if (editingDefinition?.category === category && editingDefinition?.tag === tag) editingDefinition.level = actualLevel;
  const values = hierarchicalSchema?.[category]?.tagsByLevel?.[String(actualLevel)] || [];
  return values.filter((item) => item && item !== tag);
}

function hideMergePanel() {
  const mergePanel = $("#mergeTagPanel");
  const transferPanel = $("#transferTagPanel");
  if (mergePanel) mergePanel.hidden = true;
  if (transferPanel) transferPanel.hidden = true;
}

function toggleMergePanel() {
  if (!editingDefinition || editingDefinition.type !== "tag") return;
  const panel = $("#mergeTagPanel");
  const select = $("#mergeTagTarget");
  if (!panel || !select) return;
  const { category, tag, level } = editingDefinition;
  const targets = sameLevelMergeTargets(category, tag, level);
  if (!targets.length) {
    showToast("当前层级没有可合并的目标标签。", "error");
    return;
  }
  select.innerHTML = targets.map((target) => `<option value="${escapeHtml(target)}">${escapeHtml(target)}</option>`).join("");
  panel.hidden = !panel.hidden;
}

function renderTransferLevelOptions() {
  const category = $("#transferTagCategory")?.value || "";
  const levelSelect = $("#transferTagLevel");
  if (!levelSelect) return;
  const levels = Math.min(Math.max(Number(hierarchicalSchema?.[category]?.levels || categoryLevels?.[category] || 1), 1), 5);
  levelSelect.innerHTML = Array.from({ length: levels }, (_, index) => {
    const level = index + 1;
    return `<option value="${level}">${escapeHtml(categoryLevelLabel(category, level))}</option>`;
  }).join("");
}

function toggleTransferPanel() {
  if (!editingDefinition || editingDefinition.type !== "tag") return;
  const panel = $("#transferTagPanel");
  const categorySelect = $("#transferTagCategory");
  if (!panel || !categorySelect) return;
  const categories = categoryOrder.length ? categoryOrder.filter((category) => schema?.[category]) : Object.keys(schema || {});
  categorySelect.innerHTML = categories.map((category) => `<option value="${escapeHtml(category)}" ${category === editingDefinition.category ? "selected" : ""}>${escapeHtml(displayCategory(category))}</option>`).join("");
  renderTransferLevelOptions();
  const currentLevel = effectiveTagLevel(editingDefinition.category, editingDefinition.tag, editingDefinition.level);
  const levelSelect = $("#transferTagLevel");
  if (categorySelect.value === editingDefinition.category && levelSelect?.querySelector(`option[value="${currentLevel}"]`)) levelSelect.value = String(currentLevel);
  $("#mergeTagPanel").hidden = true;
  panel.hidden = !panel.hidden;
}

async function transferTagFromModal() {
  if (!editingDefinition || editingDefinition.type !== "tag") return;
  const targetCategory = $("#transferTagCategory")?.value || "";
  const targetLevel = Number($("#transferTagLevel")?.value || 1);
  const sourceLevel = effectiveTagLevel(editingDefinition.category, editingDefinition.tag, editingDefinition.level);
  if (!targetCategory || !targetLevel) {
    showToast("请选择目标一级标签和目标层级。", "error");
    return;
  }
  if (targetCategory === editingDefinition.category && targetLevel === sourceLevel) {
    showToast("目标位置和当前位置相同。", "error");
    return;
  }
  const ok = window.confirm(`确认将「${editingDefinition.tag}」转移到「${targetCategory} / ${categoryLevelLabel(targetCategory, targetLevel)}」吗？`);
  if (!ok) return;
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "transferTag", sourceCategory: editingDefinition.category, tag: editingDefinition.tag, sourceLevel, targetCategory, targetLevel }),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    categoryDefinitions = data.categoryDefinitions || {};
    tagDefinitions = data.tagDefinitions || {};
    tagGraveyard = data.tagGraveyard || [];
    tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
    $("#schemaStatus").textContent = `已转移标签：${editingDefinition.tag} → ${targetCategory} / ${categoryLevelLabel(targetCategory, targetLevel)}`;
    closeDefinitionModal();
    renderTagSystem();
    renderTagEditor();
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
async function mergeTagFromModal() {
  if (!editingDefinition || editingDefinition.type !== "tag") return;
  const target = $("#mergeTagTarget")?.value || "";
  if (!target) {
    showToast("请选择合并目标。", "error");
    return;
  }
  const { category, tag, level } = editingDefinition;
  if (target === tag) return;
  const ok = window.confirm(`确认将「${tag}」合并到「${target}」吗？合并后内容和定义以目标标签为准。`);
  if (!ok) return;
  const reasonInput = window.prompt("请填写合并原因，例如：含义重复、口径收敛、并入更准确标签", `合并到「${target}」`);
  if (reasonInput === null) return;
  const reason = reasonInput.trim() || `合并到「${target}」`;
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "mergeTag", category, sourceTag: tag, targetTag: target, level, reason }),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    categoryDefinitions = data.categoryDefinitions || {};
    tagDefinitions = data.tagDefinitions || {};
    tagGraveyard = data.tagGraveyard || [];
    tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
    $("#schemaStatus").textContent = `已合并标签：${tag} → ${target}`;
    closeDefinitionModal();
    renderTagSystem();
    renderTagEditor();
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
async function saveDefinitionFromModal() {
  if (!editingDefinition) return;
  const name = $("#definitionModalName").value.trim();
  const definition = $("#definitionModalText").value.trim();
  if (!name) {
    $("#schemaStatus").textContent = "请填写标签名称。";
    return;
  }
  try {
    let data;
    const locale = localizationLocale();
    if (locale !== "zh") {
      const payload = editingDefinition.type === "category"
        ? { action: "saveLocalization", kind: "category", category: editingDefinition.category, locale, name, definition }
        : { action: "saveLocalization", kind: "tag", category: editingDefinition.category, tag: editingDefinition.tag, locale, name, definition };
      data = await api("/api/schema", { method: "POST", body: JSON.stringify(payload) });
      schema = data.schema || {};
      hierarchicalSchema = data.hierarchicalSchema || {};
      categoryLevels = data.categoryLevels || {};
      categoryLevelNames = data.categoryLevelNames || {};
      categoryOrder = data.categoryOrder || Object.keys(schema || {});
      categoryDefinitions = data.categoryDefinitions || {};
      tagDefinitions = data.tagDefinitions || {};
      tagGraveyard = data.tagGraveyard || [];
      tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
      $("#schemaStatus").textContent = `已保存${t("english")}本地化：${name}`;
    } else if (editingDefinition.type === "category") {
      const { category } = editingDefinition;
      if (name !== category) {
        data = await api("/api/schema", {
          method: "POST",
          body: JSON.stringify({ action: "renameCategory", category, newCategory: name }),
        });
        categoryDefinitions = data.categoryDefinitions || {};
      }
      data = await api("/api/schema", {
        method: "POST",
        body: JSON.stringify({ action: "saveCategory", category: name, definition }),
      });
      schema = data.schema || {};
      categoryDefinitions = data.categoryDefinitions || {};
      tagDefinitions = data.tagDefinitions || {};
      tagGraveyard = data.tagGraveyard || [];
      tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
      $("#schemaStatus").textContent = `已保存一级标签：${name}`;
    } else {
      const { category, tag } = editingDefinition;
      let nextTag = tag;
      if (name !== tag) {
        data = await api("/api/schema", {
          method: "POST",
          body: JSON.stringify({ action: "renameTag", category, tag, newTag: name, level: editingDefinition.level || 1 }),
        });
        nextTag = name;
      }
      data = await api("/api/schema", {
        method: "POST",
        body: JSON.stringify({ category, tag: nextTag, definition, level: editingDefinition.level || 1 }),
      });
      schema = data.schema || {};
      categoryDefinitions = data.categoryDefinitions || {};
      tagDefinitions = data.tagDefinitions || {};
      tagGraveyard = data.tagGraveyard || [];
      tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
      $("#schemaStatus").textContent = `已保存子标签：${category} / ${nextTag}`;
    }
    closeDefinitionModal();
    renderTagSystem();
    renderTagGraveyard();
    renderTagEditor();
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}

function requestDeleteReason(label) {
  const ok = window.confirm(`确定删除「${label}」吗？删除后会进入标签墓地，自动打标会避免再次生成相同或相似标签。`);
  if (!ok) return "";
  const reason = window.prompt("请填写删除原因，例如：含义重复、口径不清、长期不用、合并到某标签");
  return String(reason || "").trim();
}

async function deleteTagFromModal() {
  if (!editingDefinition) return;
  const isCategory = editingDefinition.type === "category";
  const label = isCategory ? editingDefinition.category : `${editingDefinition.category} / ${editingDefinition.tag}`;
  const reason = requestDeleteReason(label);
  if (!reason) {
    $("#schemaStatus").textContent = "已取消删除：需要填写删除原因。";
    return;
  }
  try {
    const body = isCategory
      ? { action: "deleteCategory", category: editingDefinition.category, reason }
      : { action: "deleteTag", category: editingDefinition.category, tag: editingDefinition.tag, level: editingDefinition.level || 1, reason };
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify(body),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    categoryDefinitions = data.categoryDefinitions || {};
    tagDefinitions = data.tagDefinitions || {};
    tagGraveyard = data.tagGraveyard || [];
    tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
    $("#schemaStatus").textContent = `已删除标签：${label}`;
    closeDefinitionModal();
    renderTagSystem();
    renderTagGraveyard();
    renderTagEditor();
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}

function renderTagSystem() {
  const list = $("#tagSystemList");
  const select = $("#tagCategory");
  const levelSelect = $("#newTagLevel");
  if (!list || !select) return;
  const selected = select.value;
  const categories = categoryOrder.length ? categoryOrder.filter((category) => schema?.[category]) : Object.keys(schema || {});
  select.innerHTML = categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`).join("");
  if (selected && categories.includes(selected)) select.value = selected;
  renderNewTagLevelOptions();
  if (!categories.length) {
    list.innerHTML = `<div class="emptyState compact">${t("noCategories")}</div>`;
    return;
  }
  list.innerHTML = "";
  categories.forEach((category) => {
    const categoryLoc = categoryLocalization(category);
    const info = hierarchicalSchema[category] || { levels: Number(categoryLevels[category] || 1), tagsByLevel: { "1": schema[category] || [] } };
    const levels = Math.min(Math.max(Number(info.levels || categoryLevels[category] || 1), 1), 5);
    const categoryDef = categoryDefinition(category) || t("noDefinition");
    const categoryTitle = localizationFallbackTitle(categoryLoc, categoryDef, ["names", "definitions"]);
    const item = document.createElement("section");
    item.className = "schemaCategory schemaCategoryLayered";
    item.dataset.category = category;
    item.innerHTML = `
      <div class="schemaCategoryHead layeredHead">
        <div class="schemaCategoryTitle">
          <button class="categoryPill ${isLocalizationFallback(categoryLoc, "names") ? "hasLocalizationFallback" : ""}" type="button" data-definition="${escapeHtml(categoryDef)}" title="${escapeHtml(categoryTitle)}">${escapeHtml(displayCategory(category))}${localizationFallbackBadge(categoryLoc, ["names"])}</button>
        </div>
        <label class="levelSetting"><span>${t("levelSetting")}</span><select data-level-category="${escapeHtml(category)}">
          ${[1, 2, 3, 4, 5].map((level) => `<option value="${level}" ${level === levels ? "selected" : ""}>${levelCountText(level)}</option>`).join("")}
        </select></label>
      </div>
      <div class="layeredTagLevels">
        ${Array.from({ length: levels }, (_, index) => {
          const level = index + 1;
          const tags = info.tagsByLevel?.[String(level)] || [];
          return `<div class="tagLevelRow" data-category="${escapeHtml(category)}" data-level="${level}">
            <div class="tagLevelTitle"><button class="levelNameBtn" type="button" data-category="${escapeHtml(category)}" data-level="${level}" title="${t("changeLevelNameTitle")}">${escapeHtml(categoryLevelLabel(category, level))}</button><i></i></div>
            <div class="tagPillList levelTagPillList">
              ${tags.map((tag) => {
                const tagLoc = tagLocalizationEntry(category, tag);
                const definition = tagDefinition(category, tag) || t("noDefinition");
                const title = localizationFallbackTitle(tagLoc, definition, ["names", "definitions"]);
                return `<button class="tagPill ${isLocalizationFallback(tagLoc, "names") ? "hasLocalizationFallback" : ""}" type="button" data-category="${escapeHtml(category)}" data-tag="${escapeHtml(tag)}" data-level="${level}" data-definition="${escapeHtml(definition)}" title="${escapeHtml(title)}">${escapeHtml(displayTag(category, tag))}${localizationFallbackBadge(tagLoc, ["names"])}</button>`;
              }).join("") || `<div class="miniTag muted">${t("noTags")}</div>`}
            </div>
          </div>`;
        }).join("")}
      </div>
    `;
    item.querySelector(".categoryPill")?.addEventListener("click", () => openCategoryModal(category));
    item.querySelector("[data-level-category]")?.addEventListener("change", (event) => setCategoryLevels(category, event.target.value));
    item.querySelectorAll(".levelNameBtn").forEach((button) => button.addEventListener("click", () => editCategoryLevelName(category, button.dataset.level)));
    item.querySelectorAll(".tagPill").forEach((button) => bindTagDrag(button, category, button.dataset.tag, button.dataset.level));
    bindCategorySortDrag(item, category);
    list.appendChild(item);
  });
}

function renderNewTagLevelOptions() {
  const select = $("#tagCategory");
  const levelSelect = $("#newTagLevel");
  if (!select || !levelSelect) return;
  const category = select.value;
  const levels = Math.min(Math.max(Number(hierarchicalSchema?.[category]?.levels || categoryLevels?.[category] || 1), 1), 5);
  levelSelect.innerHTML = Array.from({ length: levels }, (_, index) => {
    const level = index + 1;
    return `<option value="${level}">${categoryLevelLabel(category, level)}</option>`;
  }).join("");
}


async function editCategoryLevelName(category, level) {
  const current = categoryLevelLabel(category, level);
  const next = window.prompt(`修改「${category}」的${levelLabel(level)}层级名`, current);
  if (next === null) return;
  const name = next.trim();
  if (!name) return;
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "setCategoryLevelName", category, level, name }),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    tagDefinitions = data.tagDefinitions || {};
    renderTagSystem();
    renderTagEditor();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
async function setCategoryLevels(category, levels) {
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "setCategoryLevels", category, levels }),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    tagDefinitions = data.tagDefinitions || {};
    renderTagSystem();
    renderTagEditor();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}

function clearCategorySortTargets() {
  $$(".schemaCategoryLayered").forEach((item) => item.classList.remove("categoryDropBefore", "categoryDropAfter", "categoryDragSource"));
}

function categoryInsertionFromPoint(clientX, clientY, state = categoryDragState) {
  const cards = $$(".schemaCategoryLayered").filter((card) => card.dataset.category && card.dataset.category !== state?.category);
  if (!cards.length) return { targetCategory: "", position: "after" };
  const ranked = cards.map((card) => {
    const rect = card.getBoundingClientRect();
    return {
      card,
      category: card.dataset.category,
      rect,
      centerX: rect.left + rect.width / 2,
      centerY: rect.top + rect.height / 2,
    };
  }).sort((a, b) => (a.centerY - b.centerY) || (a.centerX - b.centerX));
  const before = ranked.find((item) => clientY < item.centerY || (Math.abs(clientY - item.centerY) < item.rect.height / 2 && clientX < item.centerX));
  if (before) return { targetCategory: before.category, position: "before" };
  return { targetCategory: ranked[ranked.length - 1].category, position: "after" };
}

function paintCategorySortDrag() {
  if (!categoryDragState?.active || !categoryDragState.ghost || !categoryDragState.lastPoint) return;
  const { clientX, clientY } = categoryDragState.lastPoint;
  categoryDragState.ghost.style.left = `${clientX}px`;
  categoryDragState.ghost.style.top = `${clientY}px`;
  clearCategorySortTargets();
  categoryDragState.card?.classList.add("categoryDragSource");
  const insertion = categoryInsertionFromPoint(clientX, clientY, categoryDragState);
  categoryDragState.targetCategory = insertion.targetCategory;
  categoryDragState.position = insertion.position;
  const target = $$(".schemaCategoryLayered").find((card) => card.dataset.category === insertion.targetCategory);
  if (target) target.classList.add(insertion.position === "before" ? "categoryDropBefore" : "categoryDropAfter");
}

function updateCategorySortPosition(event) {
  if (!categoryDragState) return;
  const point = eventPoint(event);
  if (!point) return;
  categoryDragState.lastPoint = point;
  if (!categoryDragState.active) return;
  event.preventDefault?.();
  window.requestAnimationFrame(paintCategorySortDrag);
}

function startCategorySortDrag(card, category) {
  const rect = card.getBoundingClientRect();
  const ghost = card.cloneNode(true);
  ghost.classList.add("categorySortGhost");
  ghost.style.width = `${rect.width}px`;
  document.body.appendChild(ghost);
  categoryDragState.active = true;
  categoryDragState.ghost = ghost;
  card.classList.add("categoryDragSource");
  categoryDragState.lastPoint ||= { clientX: rect.left + rect.width / 2, clientY: rect.top + 24 };
  paintCategorySortDrag();
}

async function finishCategorySortDrag(event) {
  if (!categoryDragState) return;
  updateCategorySortPosition(event || categoryDragState.lastPoint || {});
  const state = categoryDragState;
  const wasActive = state.active;
  const insertion = wasActive && state.lastPoint
    ? categoryInsertionFromPoint(state.lastPoint.clientX, state.lastPoint.clientY, state)
    : { targetCategory: state.targetCategory, position: state.position };
  if (state.timer) clearTimeout(state.timer);
  categoryDragState = null;
  window.removeEventListener("pointermove", updateCategorySortPosition);
  window.removeEventListener("pointerup", finishCategorySortDrag);
  window.removeEventListener("pointercancel", cancelCategorySortDrag);
  state.ghost?.remove();
  clearCategorySortTargets();
  if (!wasActive || !insertion.targetCategory || insertion.targetCategory === state.category) return;
  const current = categoryOrder.length ? [...categoryOrder] : Object.keys(schema || {});
  const without = current.filter((item) => item !== state.category);
  const targetIndex = without.indexOf(insertion.targetCategory);
  const insertAt = targetIndex < 0 ? without.length : targetIndex + (insertion.position === "after" ? 1 : 0);
  without.splice(insertAt, 0, state.category);
  await saveCategoryOrder(without);
}

function cancelCategorySortDrag() {
  if (!categoryDragState) return;
  if (categoryDragState.timer) clearTimeout(categoryDragState.timer);
  categoryDragState.ghost?.remove();
  categoryDragState = null;
  clearCategorySortTargets();
  window.removeEventListener("pointermove", updateCategorySortPosition);
  window.removeEventListener("pointerup", finishCategorySortDrag);
  window.removeEventListener("pointercancel", cancelCategorySortDrag);
}

function bindCategorySortDrag(card, category) {
  card.addEventListener("pointerdown", (event) => {
    if (event.button !== undefined && event.button !== 0) return;
    if (event.target.closest("button, select, input, textarea, a, .tagPill, .levelSetting, .tagPillList")) return;
    const point = eventPoint(event);
    categoryDragState = { active: false, card, category, lastPoint: point, targetCategory: "", position: "after" };
    categoryDragState.timer = window.setTimeout(() => {
      if (!categoryDragState || categoryDragState.card !== card) return;
      startCategorySortDrag(card, category);
    }, 360);
    window.addEventListener("pointermove", updateCategorySortPosition, { passive: false });
    window.addEventListener("pointerup", finishCategorySortDrag, { once: true });
    window.addEventListener("pointercancel", cancelCategorySortDrag, { once: true });
  });
}

async function saveCategoryOrder(order) {
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "setCategoryOrder", order }),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    tagDefinitions = data.tagDefinitions || {};
    renderTagSystem();
    renderTagEditor();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
function clearTagDropTargets() {
  document.querySelectorAll(".schemaCategory").forEach((item) => item.classList.remove("dropReady", "dropBlocked"));
  document.querySelectorAll(".tagLevelRow").forEach((item) => item.classList.remove("dropReady", "dropBlocked"));
}

function tagDropFromPoint(x, y) {
  const levelRow = document.elementFromPoint(x, y)?.closest(".tagLevelRow");
  if (levelRow?.dataset.category && levelRow?.dataset.level) {
    return { category: levelRow.dataset.category, level: Number(levelRow.dataset.level || 1), row: levelRow };
  }
  const category = document.elementFromPoint(x, y)?.closest(".schemaCategory")?.dataset.category || "";
  if (!category) return { category: "", level: 0, row: null };
  const fallbackLevel = Math.min(Math.max(Number(hierarchicalSchema?.[category]?.levels || categoryLevels?.[category] || 1), 1), 5);
  return { category, level: fallbackLevel, row: null };
}

function eventPoint(event) {
  const point = event.touches?.[0] || event.changedTouches?.[0] || event;
  if (typeof point.clientX !== "number" || typeof point.clientY !== "number") return null;
  return { clientX: point.clientX, clientY: point.clientY };
}

function paintTagDrag() {
  if (!tagDragState?.active || !tagDragState.ghost || !tagDragState.lastPoint) return;
  const { clientX, clientY } = tagDragState.lastPoint;
  tagDragState.ghost.style.left = `${clientX}px`;
  tagDragState.ghost.style.top = `${clientY}px`;
  const target = tagDropFromPoint(clientX, clientY);
  tagDragState.targetCategory = target.category;
  tagDragState.targetLevel = target.level;
  clearTagDropTargets();
  if (!target.category) return;
  const sameSpot = target.category === tagDragState.sourceCategory && Number(target.level) === Number(tagDragState.sourceLevel);
  const card = Array.from(document.querySelectorAll(".schemaCategory")).find((item) => item.dataset.category === target.category);
  card?.classList.add(sameSpot ? "dropBlocked" : "dropReady");
  if (target.row) target.row.classList.add(sameSpot ? "dropBlocked" : "dropReady");
}

function queueTagDragPaint() {
  if (!tagDragState?.active || tagDragState.raf) return;
  tagDragState.raf = window.requestAnimationFrame(() => {
    if (!tagDragState) return;
    tagDragState.raf = 0;
    paintTagDrag();
  });
}

function updateTagDragPosition(event) {
  if (!tagDragState) return;
  const point = eventPoint(event);
  if (!point) return;
  tagDragState.lastPoint = point;
  if (!tagDragState.active) return;
  event.preventDefault?.();
  queueTagDragPaint();
}

function startTagDrag(button, category, tag, level = 1) {
  const rect = button.getBoundingClientRect();
  const ghost = button.cloneNode(true);
  ghost.classList.add("tagDragGhost");
  ghost.style.width = `${rect.width}px`;
  document.body.appendChild(ghost);
  tagDragState.active = true;
  tagDragState.ghost = ghost;
  tagDragState.sourceLevel = Number(level || tagDragState.sourceLevel || 1);
  tagDragState.targetCategory = "";
  tagDragState.targetLevel = 0;
  tagDragState.lastPoint ||= { clientX: rect.left + rect.width / 2, clientY: rect.top + rect.height / 2 };
  button.classList.add("dragSource");
  paintTagDrag();
}

async function finishTagDrag(event) {
  if (!tagDragState) return;
  updateTagDragPosition(event || tagDragState.lastPoint || {});
  const state = tagDragState;
  const wasActive = state.active;
  if (state.timer) clearTimeout(state.timer);
  if (state.raf) cancelAnimationFrame(state.raf);
  tagDragState = null;
  window.removeEventListener("pointermove", updateTagDragPosition);
  window.removeEventListener("mousemove", updateTagDragPosition);
  window.removeEventListener("touchmove", updateTagDragPosition);
  window.removeEventListener("pointerup", finishTagDrag);
  window.removeEventListener("mouseup", finishTagDrag);
  window.removeEventListener("touchend", finishTagDrag);
  window.removeEventListener("pointercancel", cancelTagDrag);
  window.removeEventListener("touchcancel", cancelTagDrag);
  state.button?.classList.remove("dragSource");
  state.ghost?.remove();
  clearTagDropTargets();
  if (!wasActive) return;
  event?.preventDefault?.();
  const targetCategory = state.targetCategory;
  const targetLevel = Number(state.targetLevel || 0);
  const sourceLevel = Number(state.sourceLevel || effectiveTagLevel(state.sourceCategory, state.tag, 1));
  if (!targetCategory || !targetLevel) return;
  if (targetCategory === state.sourceCategory && targetLevel === sourceLevel) return;
  const targetLabel = categoryLevelLabel(targetCategory, targetLevel);
  const ok = window.confirm(`确认将「${state.tag}」从「${state.sourceCategory} / ${categoryLevelLabel(state.sourceCategory, sourceLevel)}」转移到「${targetCategory} / ${targetLabel}」吗？`);
  if (!ok) return;
  await transferTagByDrag(state.sourceCategory, state.tag, sourceLevel, targetCategory, targetLevel);
}

function cancelTagDrag() {
  if (!tagDragState) return;
  if (tagDragState.timer) clearTimeout(tagDragState.timer);
  if (tagDragState.raf) cancelAnimationFrame(tagDragState.raf);
  tagDragState.button?.classList.remove("dragSource");
  tagDragState.ghost?.remove();
  tagDragState = null;
  clearTagDropTargets();
  window.removeEventListener("pointermove", updateTagDragPosition);
  window.removeEventListener("mousemove", updateTagDragPosition);
  window.removeEventListener("touchmove", updateTagDragPosition);
  window.removeEventListener("pointerup", finishTagDrag);
  window.removeEventListener("mouseup", finishTagDrag);
  window.removeEventListener("touchend", finishTagDrag);
  window.removeEventListener("pointercancel", cancelTagDrag);
  window.removeEventListener("touchcancel", cancelTagDrag);
}

function bindTagDrag(button, category, tag, level = 1) {
  button.addEventListener("click", (event) => {
    if (button.dataset.justDragged === "1") {
      event.preventDefault();
      button.dataset.justDragged = "";
      return;
    }
    openDefinitionModal(category, tag, button.dataset.level);
  });
  button.addEventListener("pointerdown", (event) => {
    if (event.button !== undefined && event.button !== 0) return;
    const point = eventPoint(event);
    tagDragState = { active: false, button, sourceCategory: category, sourceLevel: Number(level || button.dataset.level || 1), tag, lastPoint: point };
    tagDragState.timer = window.setTimeout(() => {
      if (!tagDragState || tagDragState.button !== button) return;
      startTagDrag(button, category, tag, level || button.dataset.level || 1);
      button.dataset.justDragged = "1";
    }, 350);
    window.addEventListener("pointermove", updateTagDragPosition, { passive: false });
    window.addEventListener("mousemove", updateTagDragPosition, { passive: false });
    window.addEventListener("touchmove", updateTagDragPosition, { passive: false });
    window.addEventListener("pointerup", finishTagDrag, { once: true });
    window.addEventListener("mouseup", finishTagDrag, { once: true });
    window.addEventListener("touchend", finishTagDrag, { once: true });
    window.addEventListener("pointercancel", cancelTagDrag, { once: true });
    window.addEventListener("touchcancel", cancelTagDrag, { once: true });
  });
}
async function transferTagByDrag(sourceCategory, tag, sourceLevel, targetCategory, targetLevel) {
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "transferTag", sourceCategory, tag, sourceLevel, targetCategory, targetLevel }),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    categoryDefinitions = data.categoryDefinitions || {};
    tagDefinitions = data.tagDefinitions || {};
    tagGraveyard = data.tagGraveyard || [];
    tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
    $("#schemaStatus").textContent = `已转移标签：${tag} → ${targetCategory} / ${categoryLevelLabel(targetCategory, targetLevel)}`;
    renderTagSystem();
    renderTagEditor();
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
async function moveTag(sourceCategory, targetCategory, tag) {
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "moveTag", sourceCategory, targetCategory, tag }),
    });
    schema = data.schema || {};
    tagDefinitions = data.tagDefinitions || {};
    tagGraveyard = data.tagGraveyard || [];
    tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
    $("#schemaStatus").textContent = `已转移标签：${tag} → ${targetCategory}`;
    renderTagSystem();
    renderTagEditor();
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
async function deleteCategory(category) {
  const tags = schema?.[category] || [];
  const reason = requestDeleteReason(`${category}（含 ${tags.length} 个二级标签）`);
  if (!reason) {
    $("#schemaStatus").textContent = "已取消删除：需要填写删除原因。";
    return;
  }
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ action: "deleteCategory", category, reason }),
    });
    schema = data.schema || {};
    tagDefinitions = data.tagDefinitions || {};
    tagGraveyard = data.tagGraveyard || [];
    tagLocalization = data.tagLocalization || tagLocalization || { categories: {}, tags: {} };
    if ($("#tagCategory") && !Object.keys(schema).includes($("#tagCategory").value)) {
      $("#tagCategory").value = Object.keys(schema)[0] || "";
    }
    $("#schemaStatus").textContent = `已删除一级标签：${category}`;
    renderTagSystem();
    renderTagGraveyard();
    renderTagEditor();
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
function renderTagGraveyard() {
  const list = $("#tagGraveyardList");
  const count = $("#tagGraveyardCount");
  const block = $(".graveyardBlock");
  const toggle = $("#toggleGraveyardBtn");
  if (!list) return;
  const entries = tagGraveyard || [];
  if (count) count.textContent = countText(entries.length);
  block?.classList.toggle("collapsed", graveyardCollapsed);
  if (toggle) {
    toggle.textContent = graveyardCollapsed ? (currentLocale === "en" ? "Expand" : "展开") : t("collapse");
    toggle.setAttribute("aria-expanded", String(!graveyardCollapsed));
  }
  if (graveyardCollapsed) {
    list.innerHTML = "";
    return;
  }
  if (!entries.length) {
    list.innerHTML = `<div class="emptyState compact">${t("noDeletedTags")}</div>`;
    return;
  }
  list.innerHTML = entries.map((entry) => {
    const isCategory = entry.type === "category";
    const title = isCategory ? entry.category : `${entry.category} / ${entry.tag}`;
    const type = isCategory ? "一级标签" : "二级标签";
    const definition = entry.definition ? `<p>${escapeHtml(entry.definition)}</p>` : "";
    const deletedWith = entry.deletedWithCategory ? `<span class="graveMeta">随一级标签删除</span>` : "";
    const mergedInto = entry.mergedInto ? `<span class="graveMeta">已合并到：${escapeHtml(entry.mergedInto)}</span>` : "";
    return `
      <article class="graveyardItem">
        <div class="graveyardItemHead">
          <strong>${escapeHtml(title)}</strong>
          <span>${type}</span>
        </div>
        ${definition}
        <div class="graveReason">${escapeHtml(entry.reason || "未记录原因")}</div>
        <div class="graveyardMeta">
          <span>${escapeHtml(entry.deletedAt || "")}</span>
          ${deletedWith}
          ${mergedInto}
        </div>
      </article>
    `;
  }).join("");
}
function toggleGraveyard() {
  graveyardCollapsed = !graveyardCollapsed;
  renderTagGraveyard();
}
async function addLibraryCategory() {
  const input = $("#newCategoryName");
  const category = input.value.trim();
  if (!category) {
    $("#schemaStatus").textContent = "请先填写一级标签。";
    return;
  }
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ category }),
    });
    schema = data.schema || {};
    categoryDefinitions = data.categoryDefinitions || {};
    tagDefinitions = data.tagDefinitions || {};
    input.value = "";
    $("#schemaStatus").textContent = `已添加一级标签：${category}`;
    renderTagSystem();
    renderTagEditor();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}

async function addLibraryTag() {
  const category = $("#tagCategory").value;
  const input = $("#newTagName");
  const tag = input.value.trim();
  const level = Number($("#newTagLevel")?.value || 1);
  const definition = $("#newTagDefinition").value.trim();
  if (!category || !tag) {
    $("#schemaStatus").textContent = "请选择一级标签并填写二级标签。";
    return;
  }
  try {
    const data = await api("/api/schema", {
      method: "POST",
      body: JSON.stringify({ category, tag, level, definition }),
    });
    schema = data.schema || {};
    hierarchicalSchema = data.hierarchicalSchema || {};
    categoryLevels = data.categoryLevels || {};
    categoryLevelNames = data.categoryLevelNames || {};
    categoryOrder = data.categoryOrder || Object.keys(schema || {});
    categoryDefinitions = data.categoryDefinitions || {};
    tagDefinitions = data.tagDefinitions || {};
    input.value = "";
    $("#newTagDefinition").value = "";
    $("#schemaStatus").textContent = `已添加${levelLabel(level)}标签：${category} / ${tag}`;
    renderTagSystem();
    renderTagEditor();
  } catch (err) {
    showToast(err.message, "error");
    $("#schemaStatus").textContent = err.message;
  }
}
function renderLibrary() {
  renderTagSystem();
  const wrap = $("#libraryList");
  const confirmedAssets = assets.filter((asset) => asset.confirmed);
  if (!confirmedAssets.length) {
    wrap.innerHTML = `<div class="panel">${t("noConfirmedRecords")}</div>`;
    return;
  }
  wrap.innerHTML = "";
  confirmedAssets.forEach((asset) => {
    const row = document.createElement("article");
    row.className = "tagRecord";
    const flatTags = Object.entries(asset.tags || {}).flatMap(([category, tags]) => tags.map((tag) => {
      const path = splitTagPath(tag);
      const hasFallback = isLocalizationFallback(categoryLocalization(category), "names") || path.some((part) => isLocalizationFallback(tagLocalizationEntry(category, part), "names"));
      const label = `${displayCategory(category)} / ${path.map((part) => displayTag(category, part)).join("-")}`;
      return { label, hasFallback };
    }));
    row.innerHTML = `
      <div>
        <h3>${escapeHtml(getAssetTitle(asset))}</h3>
        <p>${escapeHtml(asset.confirmedAt || asset.createdAt || "")}</p>
      </div>
      <div class="miniTags">${flatTags.map((tag) => `<span class="miniTag ${tag.hasFallback ? "hasLocalizationFallback" : ""}" title="${tag.hasFallback ? escapeHtml(t("missingLocalization")) : ""}">${escapeHtml(tag.label)}${tag.hasFallback ? `<span class="localizationFallbackBadge" title="${escapeHtml(t("missingLocalization"))}">${escapeHtml(t("missingLocalizationShort"))}</span>` : ""}</span>`).join("") || `<span class="miniTag">${t("noTags")}</span>`}</div>
      <button class="secondary" type="button">${t("edit")}</button>
    `;
    row.querySelector("button").addEventListener("click", () => {
      setView("tagging");
      applySelectedAsset(asset.id);
    });
    wrap.appendChild(row);
  });
}

function openTranscribeModal(assetId) {
  pendingTranscribeAssetId = assetId;
  const modal = $("#transcribeModal");
  if (!modal) return transcribeAudio(assetId, { method: "local", language: "auto" });
  $("#transcribeMethod").value = "local";
  $("#transcribeLanguage").value = "auto";
  if ($("#localAsrModel")) $("#localAsrModel").value = "";
  modal.hidden = false;
}

function closeTranscribeModal() {
  pendingTranscribeAssetId = "";
  const modal = $("#transcribeModal");
  if (modal) modal.hidden = true;
}

async function startTranscribeFromModal() {
  if (!pendingTranscribeAssetId) return;
  const method = $("#transcribeMethod")?.value || "local";
  if (method === "model" && !requireModelKey()) return;
  const language = $("#transcribeLanguage")?.value || "auto";
  const localModel = $("#localAsrModel")?.value.trim() || "";
  const assetId = pendingTranscribeAssetId;
  closeTranscribeModal();
  await transcribeAudio(assetId, { method, language, localModel });
}

async function transcribeAudio(assetId, options = {}) {
  const method = options.method || "local";
  if (method === "model" && !requireModelKey()) return;
  const language = options.language || "auto";
  const localModel = options.localModel || "";
  const buttons = Array.from(document.querySelectorAll(`#asset-${CSS.escape(assetId)} .transcribeBtn, .panelTranscribeBtn`));
  buttons.forEach((button) => {
    button.disabled = true;
    button.textContent = t("transcribing");
  });
  const methodText = method === "local" ? t("localAsr") : t("modelAsr");
  showToast(currentLocale === "en" ? `Transcribing with ${methodText}...` : `正在使用${methodText}进行音频转写...`);
  const status = $("#uploadStatus");
  if (status) status.textContent = currentLocale === "en" ? `Transcribing with ${methodText}...` : `正在使用${methodText}进行音频转写...`;
  try {
    const data = await api("/api/transcribe-audio", {
      method: "POST",
      body: JSON.stringify({ assetId, apiKey: modelKey(), method, language, localModel }),
    });
    showToast(t("transcribeDone"), "success");
    if (status) status.textContent = `音频转写已完成：${data.transcriptPath}`;
    await refresh();
    applySelectedAsset(assetId);
  } catch (err) {
    showToast(err.message, "error");
    if (status) status.textContent = err.message;
    buttons.forEach((button) => {
      button.disabled = false;
      button.textContent = t("startTranscribe");
    });
  }
}

async function generateReport(assetId) {
  if (!requireModelKey()) return;
  const buttons = Array.from(document.querySelectorAll(`#asset-${CSS.escape(assetId)} .genReportBtn, .panelReportBtn`));
  buttons.forEach((button) => {
    button.disabled = true;
    button.textContent = t("generating");
  });
  showToast(t("reportGenerating"));
  const status = $("#uploadStatus");
  if (status) status.textContent = t("reportGenerating");
  try {
    const data = await api("/api/generate-report", {
      method: "POST",
      body: JSON.stringify({ assetId, apiKey: modelKey() }),
    });
    showToast(t("reportDone"), "success");
    if (status) status.textContent = `双语拉片报告已生成：${data.reportPath}`;
    await refresh();
    applySelectedAsset(assetId);
  } catch (err) {
    showToast(err.message, "error");
    if (status) status.textContent = err.message;
    buttons.forEach((button) => {
      button.disabled = false;
      button.textContent = t("generateReport");
    });
  }
}
async function deleteAsset(assetId) {
  const asset = assets.find((item) => item.id === assetId);
  if (!asset) return;
  const ok = window.confirm(`确定删除「${getAssetTitle(asset)}」吗？\n这会移除素材记录，并清理该素材的本地素材包。`);
  if (!ok) return;
  $("#uploadStatus").textContent = t("deletingAsset");
  try {
    await api(`/api/assets/${encodeURIComponent(assetId)}`, { method: "DELETE" });
    if ($("#assetSelect").value === assetId) {
      $("#assetSelect").value = "";
      applySelectedAsset("");
    }
    $("#uploadStatus").textContent = t("assetDeleted");
    showToast(t("assetDeleted"), "success");
    await refresh();
  } catch (err) {
    showToast(err.message, "error");
    $("#uploadStatus").textContent = err.message;
  }
}
async function refresh() {
  const schemaData = await api("/api/schema");
  schema = schemaData.schema;
  hierarchicalSchema = schemaData.hierarchicalSchema || {};
  categoryLevels = schemaData.categoryLevels || {};
  categoryLevelNames = schemaData.categoryLevelNames || {};
  categoryOrder = schemaData.categoryOrder || Object.keys(schema || {});
  categoryDefinitions = schemaData.categoryDefinitions || {};
  tagDefinitions = schemaData.tagDefinitions || {};
  tagGraveyard = schemaData.tagGraveyard || [];
  tagLocalization = schemaData.tagLocalization || { categories: {}, tags: {} };
  renderTagSystem();
  renderTagGraveyard();
  const promptsData = await api("/api/prompts");
  fillPromptForm(promptsData);
  const db = await api("/api/assets");
  assets = db.assets || [];
  const seriesData = await api("/api/series");
  seriesLibrary = seriesData.series || [];
  renderAssetSelect();
  renderEditingAssetSelect();
  renderSelectedAssetPanel(assets.find((item) => item.id === $("#assetSelect")?.value) || null);
  await loadTasks();
  renderUploadAssets();
  renderSeriesLibrary();
  renderSeriesDetail();
  renderLibrary();
  if (!Object.keys(currentTags).length) renderTagEditor({});
  syncModelKeyGates();
  renderI18n();
}

function openUploadModal() {
  if (!requireModelKey()) return;
  $("#uploadModal").hidden = false;
  syncModelKeyGates();
}

function closeUploadModal() {
  $("#uploadModal").hidden = true;
}

async function uploadVideo(event) {
  event.preventDefault();
  if (!requireModelKey()) return;
  const formEl = event.currentTarget;
  const submit = formEl.querySelector('button[type="submit"]');
  const form = new FormData(formEl);
  form.append("apiKey", modelKey());
  $("#uploadStatus").textContent = currentLocale === "en" ? "Uploading video and adding it to the full analysis queue..." : "正在上传视频并加入全流程拉片任务...";
  if (submit) {
    submit.disabled = true;
    submit.textContent = t("submitting");
  }
  try {
    const data = await api("/api/upload", { method: "POST", body: form });
    $("#uploadStatus").textContent = `已加入拉片任务：${data.task?.stage || data.asset.status}`;
    showToast(t("uploadQueued"), "success");
    formEl.reset();
    $("#dropzone strong").textContent = t("selectOrDropVideo");
    closeUploadModal();
    await refresh();
    startTaskPolling();
    setView("upload");
    setTimeout(() => document.getElementById(`asset-${data.asset.id}`)?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
  } catch (err) {
    showToast(err.message, "error");
    $("#uploadStatus").textContent = err.message;
  } finally {
    if (submit) {
      submit.disabled = false;
      submit.textContent = t("startAnalysis");
    }
  }
}

async function autoTag() {
  if (!requireModelKey()) return;
  const assetId = $("#assetSelect").value;
  const reportPath = $("#reportPath").value.trim();
  const reportFile = $("#reportFile").files[0];
  $("#summary").textContent = t("tagging");
  try {
    let data;
    if (reportFile) {
      const form = new FormData();
      form.append("assetId", assetId);
      form.append("apiKey", modelKey());
      form.append("report", reportFile);
      data = await api("/api/auto-tag", { method: "POST", body: form });
    } else {
      data = await api("/api/auto-tag", {
        method: "POST",
        body: JSON.stringify({ assetId, reportPath, apiKey: modelKey() }),
      });
    }
    currentTags = data.tags;
    currentTagDefinitions = normalizeTagDefinitionsInput(data.tagDefinitions || {});
    currentSummary = data.summary || "";
    $("#summary").textContent = currentSummary || t("generatedTags");
    showToast(t("autoTagDone"), "success");
    renderTagEditor();
    await refresh();
    if (assetId) {
      applySelectedAsset(assetId);
      currentTagDefinitions = normalizeTagDefinitionsInput(data.tagDefinitions || currentTagDefinitions || {});
      renderTagEditor();
    }
  } catch (err) {
    showToast(err.message, "error");
    $("#summary").textContent = err.message;
  }
}

async function confirmTags() {
  const assetId = $("#assetSelect").value;
  const title = assetId ? "" : prompt(t("assetNamePrompt"), t("untitledAsset"));
  try {
    const data = await api("/api/confirm", {
      method: "POST",
      body: JSON.stringify({
        assetId,
        title,
        tags: currentTags,
        tagDefinitions: currentTagDefinitions,
        summary: currentSummary,
        note: $("#note").value.trim(),
      }),
    });
    $("#summary").textContent = formatText("savedToLibrary", { title: data.asset.title || data.asset.id });
    showToast(t("tagsConfirmed"), "success");
    await refresh();
    setView("library");
  } catch (err) {
    showToast(err.message, "error");
    $("#summary").textContent = err.message;
  }
}

function setUploadFile(file) {
  const input = $("#dropzone input");
  if (!input || !file) return false;
  if (!file.type.startsWith("video/")) {
    showToast(t("chooseVideoFile"), "error");
    return false;
  }
  const transfer = new DataTransfer();
  transfer.items.add(file);
  input.files = transfer.files;
  $("#dropzone strong").textContent = file.name;
  showToast(t("videoAdded"), "success");
  return true;
}

function bindUploadDropzone() {
  const dropzone = $("#dropzone");
  const input = $("#dropzone input");
  if (!dropzone || !input) return;
  const stopFileDrag = (event) => {
    if (!Array.from(event.dataTransfer?.types || []).includes("Files")) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
  };
  ["dragenter", "dragover"].forEach((name) => {
    dropzone.addEventListener(name, (event) => {
      stopFileDrag(event);
      dropzone.classList.add("dragOver");
    });
  });
  ["dragleave", "dragend"].forEach((name) => {
    dropzone.addEventListener(name, () => dropzone.classList.remove("dragOver"));
  });
  dropzone.addEventListener("drop", (event) => {
    stopFileDrag(event);
    dropzone.classList.remove("dragOver");
    const file = Array.from(event.dataTransfer?.files || []).find((item) => item.type.startsWith("video/"));
    setUploadFile(file);
  });
  document.addEventListener("dragover", stopFileDrag);
  document.addEventListener("drop", (event) => {
    if (!Array.from(event.dataTransfer?.types || []).includes("Files")) return;
    if (event.target.closest("#dropzone")) return;
    event.preventDefault();
    event.stopPropagation();
  });
}
function bind() {
  document.addEventListener("click", (event) => {
    if (event.target.closest("#toggleGraveyardBtn")) toggleGraveyard();
  });
  $$(".nav").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  $("#languageToggle")?.addEventListener("click", (event) => {
    event.stopPropagation();
    const menu = $("#languageMenu");
    const toggle = $("#languageToggle");
    if (!menu || !toggle) return;
    menu.hidden = !menu.hidden;
    toggle.setAttribute("aria-expanded", menu.hidden ? "false" : "true");
  });
  $$("#languageMenu [data-locale]").forEach((button) => button.addEventListener("click", (event) => {
    event.stopPropagation();
    setLocale(button.dataset.locale);
  }));
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".languageBox")) {
      const menu = $("#languageMenu");
      const toggle = $("#languageToggle");
      if (menu) menu.hidden = true;
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    }
  });
  $("#openUploadBtn").addEventListener("click", openUploadModal);
  $("#aiApiKey")?.addEventListener("input", () => {
    setModelKeyAttention(false);
    syncModelKeyGates();
  });
  $("#assetNameSearchInput")?.addEventListener("input", (event) => {
    assetNameSearchQuery = event.target.value || "";
    renderUploadAssets();
  });
  $("#assetTagSearchInput")?.addEventListener("focus", openAssetTagDropdown);
  $("#assetTagSearchInput")?.addEventListener("input", (event) => {
    selectedAssetTagFilter = null;
    assetTagSearchQuery = event.target.value || "";
    renderAssetTagDropdown(true);
    renderUploadAssets();
  });
  $("#assetTagDropdownBtn")?.addEventListener("click", (event) => {
    event.stopPropagation();
    const dropdown = $("#assetTagDropdown");
    if (dropdown?.hidden) openAssetTagDropdown(); else closeAssetTagDropdown();
  });
  $("#clearAssetFiltersBtn")?.addEventListener("click", clearAssetFilters);
  document.addEventListener("click", (event) => {
    if (!event.target.closest("#assetTagFilter")) closeAssetTagDropdown();
  });
  $("#closePreviewTagBtn")?.addEventListener("click", closePreviewTagModal);
  $("#cancelPreviewTagBtn")?.addEventListener("click", closePreviewTagModal);
  $("#savePreviewTagBtn")?.addEventListener("click", savePreviewTagModal);
  $("#previewTagModal")?.addEventListener("click", (event) => { if (event.target.id === "previewTagModal") closePreviewTagModal(); });  $("#closeUploadBtn").addEventListener("click", closeUploadModal);
  $("#uploadModal").addEventListener("click", (event) => {
    if (event.target.id === "uploadModal") closeUploadModal();
  });
  $("#framePreviewModal")?.addEventListener("click", (event) => {
    if (event.target.id === "framePreviewModal") closeFramePreview();
  });
  $("#closeFramePreviewBtn")?.addEventListener("click", closeFramePreview);
  $("#uploadForm").addEventListener("submit", uploadVideo);
  bindUploadDropzone();
  $("#openSeriesUploadBtn")?.addEventListener("click", openSeriesUploadModal);
  $("#closeSeriesUploadBtn")?.addEventListener("click", closeSeriesUploadModal);
  $("#seriesUploadModal")?.addEventListener("click", (event) => {
    if (event.target.id === "seriesUploadModal") closeSeriesUploadModal();
  });
  $("#seriesUploadForm")?.addEventListener("submit", uploadSeriesEpisode);
  bindSeriesDropzone();
  $("#backToSeriesBtn")?.addEventListener("click", () => setView("series"));
  $("#seriesDetailEpisodeLimit")?.addEventListener("input", (event) => {
    seriesDetailEpisodeLimit = Number(event.target.value || 0);
    renderSeriesDetail();
  });
  $("#seriesDetailGenerateStorylinesBtn")?.addEventListener("click", generateSeriesDetailStorylines);
  $("#seriesDetailGenerateCutlistBtn")?.addEventListener("click", generateSeriesDetailCutlist);
  $("#seriesDetailRenderPreviewBtn")?.addEventListener("click", renderSeriesDetailPreviewVideo);
  $("#seriesDetailExportJianyingBtn")?.addEventListener("click", exportSeriesDetailJianyingDraft);
  $("#autoTagBtn").addEventListener("click", autoTag);
  $("#confirmBtn").addEventListener("click", confirmTags);
  $("#toggleGraveyardBtn")?.addEventListener("click", (event) => { event.stopPropagation(); toggleGraveyard(); });
  $("#addCategoryBtn").addEventListener("click", addLibraryCategory);
  $("#addLibraryTagBtn").addEventListener("click", addLibraryTag);
  $("#tagCategory")?.addEventListener("change", renderNewTagLevelOptions);
  $("#savePromptsBtn").addEventListener("click", savePrompts);
  $("#resetPromptsBtn").addEventListener("click", resetPrompts);
  $("#closeTranscribeBtn")?.addEventListener("click", closeTranscribeModal);
  $("#cancelTranscribeBtn")?.addEventListener("click", closeTranscribeModal);
  $("#startTranscribeBtn")?.addEventListener("click", startTranscribeFromModal);
  $("#transcribeMethod")?.addEventListener("change", syncModelKeyGates);
  $("#transcribeModal")?.addEventListener("click", (event) => { if (event.target.id === "transcribeModal") closeTranscribeModal(); });  $("#closeDefinitionBtn").addEventListener("click", closeDefinitionModal);
  bindBackdropClose("#definitionModal", closeDefinitionModal);
  $("#saveDefinitionModalBtn").addEventListener("click", saveDefinitionFromModal);
  $("#deleteDefinitionTagBtn").addEventListener("click", deleteTagFromModal);
  $("#mergeDefinitionTagBtn")?.addEventListener("click", toggleMergePanel);
  $("#confirmMergeTagBtn")?.addEventListener("click", mergeTagFromModal);
  $("#transferDefinitionTagBtn")?.addEventListener("click", toggleTransferPanel);
  $("#confirmTransferTagBtn")?.addEventListener("click", transferTagFromModal);
  $("#transferTagCategory")?.addEventListener("change", renderTransferLevelOptions);
  $("#assetSelect").addEventListener("change", (event) => applySelectedAsset(event.target.value));
  $("#editingSourceType")?.addEventListener("change", (event) => {
    editingSourceType = event.target.value || "asset";
    editingStorylines = [];
    selectedStorylineId = "";
    editingCutlist = null;
    renderEditingAssetSelect();
  });
  $("#editingAssetSelect")?.addEventListener("change", (event) => {
    editingStorylines = [];
    selectedStorylineId = "";
    editingCutlist = null;
    renderEditingAsset(event.target.value);
  });
  $("#editingSeriesSelect")?.addEventListener("change", (event) => {
    editingSeriesId = event.target.value || "";
    editingStorylines = [];
    selectedStorylineId = "";
    editingCutlist = null;
    renderEditingSeries();
  });
  $("#editingEpisodeLimit")?.addEventListener("input", (event) => {
    editingEpisodeLimit = Number(event.target.value || 0);
    editingStorylines = [];
    selectedStorylineId = "";
    editingCutlist = null;
    renderEditingSeries();
  });
  $("#generateStorylinesBtn")?.addEventListener("click", generateEditingStorylines);
  $("#generateCutlistBtn")?.addEventListener("click", generateEditingCutlist);
  $("#renderPreviewBtn")?.addEventListener("click", renderEditingPreviewVideo);
  $("#exportJianyingBtn")?.addEventListener("click", exportJianyingDraft);
  $("#reportFile")?.addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    if (file) showToast(formatText("reportSelected", { name: file.name }), "success");
  });
  $("#dropzone input").addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) setUploadFile(file);
  });
}

bind();
renderI18n();
refresh().then(startTaskPolling).catch((err) => {
  document.body.innerHTML = `<main><div class="panel">${escapeHtml(err.message)}</div></main>`;
});


