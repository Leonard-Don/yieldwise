function currentBrowserSamplingTask() {
  const tasks = state.browserSamplingPackItems ?? [];
  return tasks.find((task) => task.taskId === state.selectedBrowserSamplingTaskId) ?? tasks[0] ?? null;
}

function getBrowserCaptureRunItems(limit = 6, { taskId = null, districtId = null } = {}) {
  const runs = (effectiveOperationsOverview().browserCaptureRuns ?? [])
    .filter((run) => !districtId || districtId === "all" || run.districtId === districtId)
    .filter((run) => !taskId || run.taskId === taskId)
    .slice()
    .sort(compareCreatedAtDesc);
  return runs.slice(0, limit);
}

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

function getBrowserReviewInboxQueue(task = currentBrowserSamplingTask(), { excludeCurrent = false } = {}) {
  const districtId = task?.districtId ?? (state.districtFilter !== "all" ? state.districtFilter : null);
  const allItems = state.browserReviewInboxItems ?? [];
  const districtItems = browserReviewInboxItems({ districtId });
  let preferredItems = browserReviewInboxItems({ districtId, preferDistrict: true });
  const currentInboxItemId = currentBrowserReviewInboxItemId();
  if (excludeCurrent && currentInboxItemId) {
    preferredItems = preferredItems.filter((item) => item.inboxItemId !== currentInboxItemId);
  }
  if (!preferredItems.length && excludeCurrent && currentInboxItemId) {
    preferredItems = allItems.filter((item) => item.inboxItemId !== currentInboxItemId);
  }
  if (!preferredItems.length) {
    preferredItems = excludeCurrent && currentInboxItemId ? allItems.filter((item) => item.inboxItemId !== currentInboxItemId) : allItems.slice();
  }
  return {
    allItems,
    districtItems,
    previewItems: browserReviewInboxItems({ districtId, preferDistrict: true }).slice(0, 4),
    nextItem: preferredItems[0] ?? null,
  };
}

async function navigateToBrowserReviewInboxItem(item) {
  if (!item?.taskId) {
    return;
  }
  const task = browserReviewInboxTaskSnapshot(item);
  await navigateToBrowserSamplingTask(task, {
    revealLatestCaptureRun: true,
    preferredReviewRunId: item.runId ?? null,
    preferredReviewQueueId: item.queueId ?? null,
    syncDistrictScope: true,
  });
}

function currentBrowserCaptureSubmission() {
  const submission = state.lastBrowserCaptureSubmission;
  if (!submission?.taskId || submission.status !== "success") {
    return null;
  }
  return submission;
}

function currentBrowserCaptureReviewAction() {
  const action = state.lastBrowserCaptureReviewAction;
  if (!action?.runId || action.status !== "success") {
    return null;
  }
  return action;
}

function browserSamplingCaptureCandidateState(task) {
  return ["needs_capture", "in_progress"].includes(browserSamplingCoverageState(task));
}

function getBrowserSamplingWorkbenchQueue(task = currentBrowserSamplingTask()) {
  const openTasks = (state.browserSamplingPackItems ?? [])
    .filter((item) => item.taskId !== task?.taskId)
    .filter((item) => browserSamplingCoverageState(item) !== "resolved")
    .slice()
    .sort(compareBrowserSamplingMapTask);
  const sameDistrictOpenTasks = task?.districtId
    ? openTasks.filter((item) => item.districtId === task.districtId)
    : [];
  const captureTasks = openTasks.filter((item) => browserSamplingCaptureCandidateState(item));
  const sameDistrictCaptureTasks = sameDistrictOpenTasks.filter((item) => browserSamplingCaptureCandidateState(item));
  const previewTasks = (sameDistrictOpenTasks.length ? sameDistrictOpenTasks : openTasks).slice(0, 4);
  const taskPool = sameDistrictOpenTasks.length ? sameDistrictOpenTasks : openTasks;
  const reviewInbox = getBrowserReviewInboxQueue(task, { excludeCurrent: true });
  const nextReviewItem = reviewInbox.nextItem ?? null;
  const nextReviewTask = nextReviewItem ? browserReviewInboxTaskSnapshot(nextReviewItem) : null;
  return {
    districtTasks: taskPool,
    nextDistrictTask: sameDistrictCaptureTasks[0] ?? captureTasks[0] ?? sameDistrictOpenTasks[0] ?? openTasks[0] ?? null,
    nextReviewTask,
    nextReviewItem,
    nextCaptureTask: sameDistrictCaptureTasks[0] ?? captureTasks[0] ?? null,
    previewTasks,
    reviewPreviewItems: reviewInbox.previewItems,
    reviewDistrictCount: reviewInbox.districtItems.length,
    reviewTotalCount: reviewInbox.allItems.length,
  };
}

function findPostSubmitBrowserSamplingTask(sourceTask) {
  const sourceTaskId = sourceTask?.taskId ?? null;
  const sourceDistrictId = sourceTask?.districtId ?? null;
  const candidateTasks = (state.browserSamplingPackItems ?? [])
    .filter((item) => item?.taskId && item.taskId !== sourceTaskId && browserSamplingCaptureCandidateState(item))
    .slice()
    .sort(compareBrowserSamplingMapTask);
  const sameDistrictTasks = sourceDistrictId
    ? candidateTasks.filter((item) => item.districtId === sourceDistrictId)
    : [];
  return sameDistrictTasks[0] ?? candidateTasks[0] ?? null;
}

function browserSamplingTaskById(taskId) {
  if (!taskId) {
    return null;
  }
  return (state.browserSamplingPackItems ?? []).find((item) => item.taskId === taskId) ?? null;
}

function browserReviewInboxItemByTarget({ inboxItemId = null, runId = null, queueId = null, taskId = null } = {}) {
  const items = state.browserReviewInboxItems ?? [];
  if (inboxItemId) {
    const directMatch = items.find((item) => item?.inboxItemId === inboxItemId);
    if (directMatch) {
      return directMatch;
    }
  }
  if (runId && queueId) {
    const runQueueMatch = items.find((item) => item?.runId === runId && item?.queueId === queueId);
    if (runQueueMatch) {
      return runQueueMatch;
    }
  }
  if (taskId) {
    return items.find((item) => item?.taskId === taskId) ?? null;
  }
  return null;
}

function buildBrowserCaptureReviewWorkflowLocalItem(runId, queueItem, task) {
  if (!runId || !queueItem?.queueId || !task?.taskId) {
    return null;
  }
  return {
    inboxItemId: `${runId}:${queueItem.queueId}`,
    runId,
    queueId: queueItem.queueId,
    taskId: task.taskId,
    task: task,
    taskLabel: browserSamplingTaskLabel(task),
    districtId: task.districtId ?? null,
    districtName: task.districtName ?? null,
    communityId: task.communityId ?? null,
    communityName: task.communityName ?? null,
    buildingId: task.buildingId ?? null,
    buildingName: task.buildingName ?? null,
    floorNo: task.floorNo ?? null,
    taskPendingAttentionCount: browserCapturePendingAttentionCount(task),
    businessType: queueItem.businessType ?? null,
    businessTypeLabel: queueItem.businessTypeLabel ?? null,
    sourceListingId: queueItem.sourceListingId ?? null,
    attention: Array.isArray(queueItem.attention) ? queueItem.attention : [],
  };
}

function resolveBrowserCaptureReviewWorkflowTarget(
  {
    workflow = {},
    workflowAction = "stay_current",
    runId = null,
    sourceTask = null,
    refreshedSourceTask = null,
    refreshedCurrentRun = null,
  } = {}
) {
  const workflowItem = workflow?.item ?? null;
  const workflowRunId = workflow?.runId ?? workflowItem?.runId ?? null;
  const workflowQueueId = workflow?.queueId ?? workflowItem?.queueId ?? null;
  const workflowTaskId = workflow?.taskId ?? workflowItem?.taskId ?? workflow?.task?.taskId ?? null;
  const matchedWorkflowItem = browserReviewInboxItemByTarget({
    inboxItemId: workflowItem?.inboxItemId ?? null,
    runId: workflowRunId,
    queueId: workflowQueueId,
    taskId: workflowTaskId,
  });
  const resolvedWorkflowItem = matchedWorkflowItem ?? (workflowItem?.taskId ? workflowItem : null);
  const resolvedWorkflowTask =
    browserReviewInboxTaskSnapshot(resolvedWorkflowItem) ??
    browserSamplingTaskById(workflowTaskId) ??
    workflow?.task ??
    refreshedSourceTask ??
    sourceTask ??
    null;
  if (resolvedWorkflowItem?.taskId) {
    return {
      item: resolvedWorkflowItem,
      task: resolvedWorkflowTask,
      workflowRunId: workflowRunId ?? resolvedWorkflowItem.runId ?? null,
      workflowQueueId: workflowQueueId ?? resolvedWorkflowItem.queueId ?? null,
      workflowTaskId: workflowTaskId ?? resolvedWorkflowItem.taskId ?? resolvedWorkflowTask?.taskId ?? null,
      workflowItemProvided: Boolean(workflowItem),
      resolution: "workflow_item",
    };
  }
  if ((workflowRunId || workflowQueueId || workflowTaskId) && resolvedWorkflowTask?.taskId) {
    return {
      item: {
        inboxItemId:
          workflowRunId && workflowQueueId
            ? `${workflowRunId}:${workflowQueueId}`
            : `${resolvedWorkflowTask.taskId}:${workflowQueueId ?? "review-target"}`,
        runId: workflowRunId ?? resolvedWorkflowTask.pendingReviewRunId ?? null,
        queueId: workflowQueueId ?? resolvedWorkflowTask.pendingReviewQueueId ?? null,
        taskId: resolvedWorkflowTask.taskId,
        task: resolvedWorkflowTask,
        taskLabel: browserSamplingTaskLabel(resolvedWorkflowTask),
      },
      task: resolvedWorkflowTask,
      workflowRunId: workflowRunId ?? resolvedWorkflowTask.pendingReviewRunId ?? null,
      workflowQueueId: workflowQueueId ?? resolvedWorkflowTask.pendingReviewQueueId ?? null,
      workflowTaskId: workflowTaskId ?? resolvedWorkflowTask.taskId ?? null,
      workflowItemProvided: Boolean(workflowItem),
      resolution: "workflow_identifiers",
    };
  }
  if (workflowAction === "review_current_run") {
    const pendingQueueItem = (refreshedCurrentRun?.reviewQueue ?? []).find((item) => String(item?.status ?? "pending") === "pending");
    const localItem = buildBrowserCaptureReviewWorkflowLocalItem(runId, pendingQueueItem, refreshedSourceTask ?? sourceTask);
    if (localItem) {
      return {
        item: localItem,
        task: browserReviewInboxTaskSnapshot(localItem),
        workflowRunId: localItem.runId,
        workflowQueueId: localItem.queueId,
        workflowTaskId: localItem.taskId,
        workflowItemProvided: false,
        resolution: "fallback_current_run",
      };
    }
  }
  if (workflowAction === "review_current_task") {
    const currentTaskItem = browserReviewInboxItemByTarget({
      runId: refreshedSourceTask?.pendingReviewRunId ?? null,
      queueId: refreshedSourceTask?.pendingReviewQueueId ?? null,
      taskId: refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
    });
    if (currentTaskItem?.taskId) {
      return {
        item: currentTaskItem,
        task: browserReviewInboxTaskSnapshot(currentTaskItem),
        workflowRunId: currentTaskItem.runId ?? null,
        workflowQueueId: currentTaskItem.queueId ?? null,
        workflowTaskId: currentTaskItem.taskId ?? null,
        workflowItemProvided: false,
        resolution: "fallback_current_task",
      };
    }
  }
  if (workflowAction === "advance_next_review") {
    const nextReviewItem = getBrowserReviewInboxQueue(refreshedSourceTask ?? sourceTask, { excludeCurrent: true }).nextItem;
    if (nextReviewItem?.taskId) {
      return {
        item: nextReviewItem,
        task: browserReviewInboxTaskSnapshot(nextReviewItem),
        workflowRunId: nextReviewItem.runId ?? null,
        workflowQueueId: nextReviewItem.queueId ?? null,
        workflowTaskId: nextReviewItem.taskId ?? null,
        workflowItemProvided: false,
        resolution: "fallback_next_review",
      };
    }
  }
  return {
    item: null,
    task: refreshedSourceTask ?? sourceTask ?? null,
    workflowRunId: workflowRunId ?? null,
    workflowQueueId: workflowQueueId ?? null,
    workflowTaskId: workflowTaskId ?? refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
    workflowItemProvided: false,
    resolution: "fallback_source_task",
  };
}

function resolvePostSubmitBrowserSamplingTask(
  {
    workflow = {},
    workflowAction = "stay_current",
    sourceTask = null,
    refreshedSourceTask = null,
  } = {}
) {
  const workflowTaskId = workflow?.taskId ?? workflow?.task?.taskId ?? null;
  const workflowTask = browserSamplingTaskById(workflowTaskId) ?? workflow?.task ?? null;
  if (workflowTask?.taskId) {
    return {
      task: workflowTask,
      workflowTaskId: workflowTask.taskId ?? workflowTaskId ?? null,
      workflowTaskProvided: true,
      resolution: "workflow_task",
    };
  }
  if (workflowTaskId) {
    return {
      task: refreshedSourceTask ?? sourceTask ?? null,
      workflowTaskId,
      workflowTaskProvided: true,
      resolution: "workflow_task_missing_snapshot",
    };
  }
  if (workflowAction === "advance_next_capture") {
    const fallbackTask = findPostSubmitBrowserSamplingTask(refreshedSourceTask ?? sourceTask);
    if (fallbackTask?.taskId) {
      return {
        task: fallbackTask,
        workflowTaskId: null,
        workflowTaskProvided: false,
        resolution: "fallback_queue_task",
      };
    }
  }
  return {
    task: refreshedSourceTask ?? sourceTask ?? null,
    workflowTaskId: null,
    workflowTaskProvided: false,
    resolution: "fallback_source_task",
  };
}

function applyBrowserSamplingTaskProgress(taskSnapshot, taskProgress) {
  if (!taskSnapshot || !taskProgress) {
    return taskSnapshot;
  }
  const nextSnapshot = { ...taskSnapshot };
  const afterCount = Number(taskProgress.afterCount ?? browserSamplingCurrentCount(taskSnapshot));
  const targetCount = Number(taskProgress.targetCount ?? browserSamplingTargetCount(taskSnapshot));
  const missingCount = Number(taskProgress.missingCount ?? Math.max(targetCount - afterCount, 0));
  if (nextSnapshot.targetGranularity === "floor") {
    nextSnapshot.currentPairCount = afterCount;
    nextSnapshot.targetPairCount = targetCount;
    nextSnapshot.missingPairCount = missingCount;
  }
  nextSnapshot.currentSampleSize = afterCount;
  nextSnapshot.targetSampleSize = targetCount;
  nextSnapshot.missingSampleCount = missingCount;
  return nextSnapshot;
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
