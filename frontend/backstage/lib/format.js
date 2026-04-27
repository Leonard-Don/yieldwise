function anchorDecisionLabel(value) {
  return {
    pending: "待确认",
    confirmed: "已确认",
    manual_override: "手工覆盖"
  }[value] ?? "待确认";
}

function mapWaypointSourceLabel(source) {
  return (
    {
      opportunity: "机会榜",
      floor_watchlist: "持续套利楼层榜",
      matrix: "楼栋矩阵",
      search: "全局搜索",
      browser_sampling: "公开页采样台",
      geo_task: "几何补采榜",
      coverage: "采样覆盖看板",
      capture_run: "采样批次回看",
      queue: "运行队列"
    }[source] ?? "研究台"
  );
}

function searchScore(text, query) {
  if (!text || !query) {
    return 0;
  }
  if (text === query) {
    return 120;
  }
  if (text.startsWith(query)) {
    return 96;
  }
  if (text.includes(query)) {
    return 72;
  }
  return 0;
}

function searchTypeLabel(type) {
  return {
    community: "小区",
    building: "楼栋",
    floor: "楼层",
    sampling: "采样"
  }[type] ?? "对象";
}

function metricsRefreshStatusLabel(status) {
  return {
    completed: "已完成",
    partial: "部分完成",
    error: "失败"
  }[String(status ?? "").trim().toLowerCase()] ?? "状态待补";
}

function metricsRefreshModeLabel(mode) {
  return {
    staged: "仅 staged",
    "staged+postgres": "staged + PostgreSQL",
    "postgres-only": "仅 PostgreSQL"
  }[String(mode ?? "").trim().toLowerCase()] ?? "模式待补";
}

function metricsRefreshTriggerLabel(source) {
  return {
    "atlas-ui": "工作台手动",
    "browser-sampling": "公开页采样",
    bootstrap: "本地 Bootstrap"
  }[String(source ?? "").trim().toLowerCase()] ?? "系统触发";
}

function metricsRefreshPostgresLabel(status) {
  return {
    completed: "DB 已同步",
    skipped: "DB 未写入",
    error: "DB 同步失败",
    pending: "DB 等待中"
  }[String(status ?? "").trim().toLowerCase()] ?? "DB 状态待补";
}

function truncate(value, maxLength = 48) {
  const text = String(value ?? "");
  if (!text || text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, Math.max(0, maxLength - 1))}…`;
}

function formatSignedNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "待补";
  }
  const numeric = Number(value);
  const prefix = numeric > 0 ? "+" : "";
  return `${prefix}${numeric.toFixed(digits)}`;
}

function formatSignedDelta(value, { suffix = "", digits = 0, emptyLabel = "上批无样本" } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return emptyLabel;
  }
  return `${formatSignedNumber(value, digits)}${suffix}`;
}

function browserSamplingTaskLabel(task) {
  if (!task) {
    return "当前任务";
  }
  return `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}${task.floorNo != null ? ` · ${task.floorNo}层` : ""}`;
}

function browserSamplingTaskStatusLabel(status) {
  return {
    resolved: "已采够",
    in_progress: "补采中",
    needs_review: "待复核",
    needs_capture: "待采样"
  }[status] ?? "状态待补";
}

function browserSamplingWorkflowActionLabel(action) {
  return {
    review_current_capture: "回看修正",
    advance_next_capture: "自动接力",
    stay_current: "留在当前"
  }[action] ?? "工作流";
}

function browserSamplingWorkflowReasonLabel(reason) {
  return {
    attention_detected: "这次采样出现 attention，优先留在当前任务修正原文。",
    same_district_queue_available: "当前任务已写入成功，继续优先接力同区待采样任务。",
    global_queue_available: "当前区内没有更合适的待采样任务，已退到全局下一条。",
    no_pending_task: "当前没有更多待采样任务，保留在当前任务方便继续检查结果。"
  }[reason] ?? "当前工作流已按默认接力策略处理。";
}

function browserSamplingPostSubmitResolutionLabel(resolution) {
  return {
    workflow_task: "来源 后端指定",
    workflow_task_missing_snapshot: "来源 后端缺快照",
    fallback_queue_task: "来源 前端兜底队列",
    fallback_source_task: "来源 前端留在当前",
  }[resolution] ?? "来源 未知";
}

function browserSamplingProgressLabel(progress) {
  if (!progress) {
    return "进度待补";
  }
  return `进度 ${Number(progress.beforeCount ?? 0)} → ${Number(progress.afterCount ?? 0)}/${Number(progress.targetCount ?? 0)}`;
}

function browserCaptureReviewStatusLabel(status) {
  return {
    pending: "待处理",
    resolved: "已修正",
    waived: "已豁免",
    superseded: "已接力",
  }[status] ?? "状态待补";
}

function browserCaptureReviewActionLabel(action) {
  return {
    review_current_run: "继续本批次",
    review_current_task: "继续当前任务",
    advance_next_review: "接力下一条",
    stay_current: "留在当前",
  }[action] ?? "复核接力";
}

function browserCaptureReviewReasonLabel(reason) {
  return {
    current_run_pending_remaining: "当前批次还有未处理 attention，继续留在本批次逐条处理。",
    current_task_pending_remaining: "当前任务还有其他未清 attention，继续停留在当前任务。",
    same_district_review_available: "当前批次已清空，已优先接力到同区下一条待复核任务。",
    global_review_available: "当前区内没有待复核任务，已退到全局下一条。",
    review_queue_cleared: "当前没有更多待复核任务，保留在当前任务方便继续检查。",
  }[reason] ?? "当前复核动作已按默认接力策略处理。";
}

function browserCaptureReviewResolutionLabel(resolution) {
  return {
    workflow_item: "来源 后端指定",
    workflow_identifiers: "来源 后端标识",
    fallback_current_run: "来源 前端留在本批次",
    fallback_current_task: "来源 前端留在当前任务",
    fallback_next_review: "来源 前端兜底收件箱",
    fallback_source_task: "来源 前端留在当前",
  }[resolution] ?? "来源 未知";
}

function yieldClass(value) {
  if (value >= 2.8) {
    return "high";
  }
  if (value >= 2.45) {
    return "mid";
  }
  return "low";
}

function sizeByScore(score) {
  return Math.max(8, Math.min(18, Math.round(score / 7)));
}

function granularityLabel(value) {
  return {
    community: "小区",
    building: "楼栋",
    floor: "楼层"
  }[value];
}

function providerModeLabel(mode) {
  return {
    self_serve_trial: "自助试用",
    business_contact: "商务合作",
    catalog_apply_or_download: "目录申请 / 下载",
    console_key: "控制台申请 Key",
    internal_staging: "内部 staging",
    manual_sketch: "手工勾绘 staging"
  }[mode] ?? mode;
}

function sourceStatusLabel(status) {
  return {
    credentials_ready: "凭证位已就绪",
    credentials_partial: "部分凭证已就绪",
    offline_ready: "离线可接入",
    connected_live: "在线接通",
    ready_for_integration: "待接入",
    online: "在线",
    partner_negotiation: "洽谈中",
    not_connected: "待接入"
  }[status] ?? status;
}

function queueStatusLabel(status) {
  return {
    resolved: "已归一",
    needs_review: "待复核",
    matching: "匹配中"
  }[status] ?? status;
}

function geoTaskStatusLabel(status) {
  return {
    needs_review: "待复核",
    needs_capture: "待补采",
    scheduled: "已派工",
    resolved: "已复核",
    captured: "已补齐"
  }[status] ?? status;
}

function geoWorkOrderStatusLabel(status) {
  return {
    assigned: "已派单",
    in_progress: "执行中",
    delivered: "待验收",
    closed: "已关闭"
  }[status] ?? status;
}

function geoWorkOrderFilterLabel(status) {
  return {
    all: "全部工单",
    open: "打开工单",
    assigned: "已派单",
    in_progress: "执行中",
    delivered: "待验收",
    closed: "已关闭"
  }[status] ?? status ?? "全部工单";
}

function resolutionStatusLabel(status) {
  return {
    done: "完成",
    review: "复核"
  }[status] ?? status;
}

function slugifyExportName(value, fallback = "latest") {
  return (value ?? fallback)
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9一-龥]+/gi, "-")
    .replace(/^-+|-+$/g, "") || fallback;
}
