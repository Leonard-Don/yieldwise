function currentBrowserCaptureRun() {
  const selectedRunId = state.selectedBrowserCaptureRunId;
  if (!selectedRunId) {
    return null;
  }
  return state.selectedBrowserCaptureRunDetail?.runId === selectedRunId ? state.selectedBrowserCaptureRunDetail : null;
}

function currentBrowserCaptureReviewQueue() {
  return currentBrowserCaptureRun()?.reviewQueue ?? [];
}

function currentPendingBrowserCaptureReviewItems() {
  return currentBrowserCaptureReviewQueue().filter((item) => String(item?.status ?? "pending") === "pending");
}

function syncBrowserCaptureReviewBatchSelection(reviewQueue = currentBrowserCaptureReviewQueue()) {
  const pendingQueueIds = new Set(
    (reviewQueue ?? [])
      .filter((item) => String(item?.status ?? "pending") === "pending")
      .map((item) => item?.queueId)
      .filter(Boolean)
  );
  const nextSelection = (state.selectedBrowserCaptureReviewQueueIds ?? []).filter((queueId) => pendingQueueIds.has(queueId));
  if (nextSelection.length !== (state.selectedBrowserCaptureReviewQueueIds ?? []).length) {
    state.selectedBrowserCaptureReviewQueueIds = nextSelection;
  }
  return nextSelection;
}

function clearBrowserCaptureReviewBatchSelection() {
  state.selectedBrowserCaptureReviewQueueIds = [];
}

function currentBrowserCaptureReviewBatchSelection(reviewQueue = currentBrowserCaptureReviewQueue()) {
  return syncBrowserCaptureReviewBatchSelection(reviewQueue).slice();
}

function toggleBrowserCaptureReviewBatchSelection(queueId, selected = null, reviewQueue = currentBrowserCaptureReviewQueue()) {
  const normalizedQueueId = String(queueId || "").trim();
  if (!normalizedQueueId) {
    return currentBrowserCaptureReviewBatchSelection(reviewQueue);
  }
  const pendingQueueIds = new Set(
    (reviewQueue ?? [])
      .filter((item) => String(item?.status ?? "pending") === "pending")
      .map((item) => item?.queueId)
      .filter(Boolean)
  );
  if (!pendingQueueIds.has(normalizedQueueId)) {
    return currentBrowserCaptureReviewBatchSelection(reviewQueue);
  }
  const selection = new Set(currentBrowserCaptureReviewBatchSelection(reviewQueue));
  const shouldSelect = selected == null ? !selection.has(normalizedQueueId) : Boolean(selected);
  if (shouldSelect) {
    selection.add(normalizedQueueId);
  } else {
    selection.delete(normalizedQueueId);
  }
  state.selectedBrowserCaptureReviewQueueIds = Array.from(selection);
  return state.selectedBrowserCaptureReviewQueueIds.slice();
}

function selectAllBrowserCaptureReviewBatchItems(reviewQueue = currentBrowserCaptureReviewQueue()) {
  state.selectedBrowserCaptureReviewQueueIds = (reviewQueue ?? [])
    .filter((item) => String(item?.status ?? "pending") === "pending")
    .map((item) => item?.queueId)
    .filter(Boolean);
  return state.selectedBrowserCaptureReviewQueueIds.slice();
}

function currentBrowserReviewInboxItemId() {
  const runId = currentBrowserCaptureRun()?.runId ?? null;
  const queueId = state.selectedBrowserCaptureReviewQueueId ?? null;
  return runId && queueId ? `${runId}:${queueId}` : null;
}

function browserReviewInboxSummaryFallback() {
  return {
    pendingQueueCount: 0,
    pendingTaskCount: 0,
    pendingDistrictCount: 0,
    oldestPendingAt: null,
    latestPendingAt: null,
  };
}

function browserReviewInboxItems({ districtId = null, preferDistrict = false } = {}) {
  const items = state.browserReviewInboxItems ?? [];
  if (!districtId || districtId === "all") {
    return items.slice();
  }
  const sameDistrictItems = items.filter((item) => item?.districtId === districtId);
  if (preferDistrict && sameDistrictItems.length) {
    return sameDistrictItems;
  }
  return preferDistrict ? items.slice() : sameDistrictItems;
}

function browserReviewInboxTaskSnapshot(item) {
  if (!item) {
    return null;
  }
  return {
    ...(item.task ?? {}),
    taskId: item.taskId ?? item.task?.taskId ?? null,
    taskType: item.taskType ?? item.task?.taskType ?? null,
    taskTypeLabel: item.taskTypeLabel ?? item.task?.taskTypeLabel ?? "公开页采样",
    targetGranularity: item.targetGranularity ?? item.task?.targetGranularity ?? null,
    focusScope: item.focusScope ?? item.task?.focusScope ?? null,
    priorityScore: item.priorityScore ?? item.task?.priorityScore ?? 0,
    priorityLabel: item.priorityLabel ?? item.task?.priorityLabel ?? "公开页采样",
    districtId: item.districtId ?? item.task?.districtId ?? null,
    districtName: item.districtName ?? item.task?.districtName ?? null,
    communityId: item.communityId ?? item.task?.communityId ?? null,
    communityName: item.communityName ?? item.task?.communityName ?? null,
    buildingId: item.buildingId ?? item.task?.buildingId ?? null,
    buildingName: item.buildingName ?? item.task?.buildingName ?? null,
    floorNo: item.floorNo ?? item.task?.floorNo ?? null,
    pendingReviewRunId: item.runId ?? item.task?.pendingReviewRunId ?? null,
    pendingReviewQueueId: item.queueId ?? item.task?.pendingReviewQueueId ?? null,
    pendingAttentionCount: item.taskPendingAttentionCount ?? item.task?.pendingAttentionCount ?? 1,
    taskLifecycleStatus: "needs_review",
    taskLifecycleLabel: "已采待复核",
  };
}

function browserCaptureReviewSuccessMessage({ reviewMode = "single", reviewStatus = "resolved", affectedCount = 1, skippedCount = 0, outcome = "same_run" } = {}) {
  const baseMessage =
    reviewMode === "batch"
      ? affectedCount > 0
        ? `${reviewStatus === "waived" ? "已批量豁免" : "已批量标记已修正"} ${affectedCount} 条 attention。${skippedCount > 0 ? ` 跳过 ${skippedCount} 条无效或已处理项。` : ""}`
        : `本次没有可更新的 pending 条目。${skippedCount > 0 ? ` 已跳过 ${skippedCount} 条无效或已处理项。` : ""}`
      : reviewStatus === "waived"
        ? "该条 attention 已标记豁免。"
        : "该条 attention 已标记已修正。";
  if (outcome === "current_task") {
    return `${baseMessage} 当前批次已清空，继续处理当前任务的其他待复核 attention。`;
  }
  if (outcome === "next_review") {
    return `${baseMessage} 当前批次已清空，已接力到下一条待复核任务。`;
  }
  if (outcome === "cleared") {
    return `${baseMessage} 当前没有更多待复核 attention。`;
  }
  return baseMessage;
}

function browserCaptureReviewPrimaryQueueId(payload, fallbackQueueId = null) {
  return (
    payload?.queueItem?.queueId ??
    payload?.updatedQueueItems?.[0]?.queueId ??
    payload?.detail?.reviewQueue?.find((item) => String(item?.status ?? "pending") === "pending")?.queueId ??
    fallbackQueueId ??
    null
  );
}
