function formatTimestamp(value) {
  if (!value) {
    return "时间待补";
  }
  return value.replace("T", " ").slice(0, 16);
}

function comparableTimestamp(value) {
  const timestamp = Date.parse(value ?? "");
  return Number.isFinite(timestamp) ? timestamp : Number.NEGATIVE_INFINITY;
}

function compareCreatedAtDesc(left, right) {
  return comparableTimestamp(right?.createdAt) - comparableTimestamp(left?.createdAt);
}

function createdAtIsBefore(left, right) {
  return comparableTimestamp(left?.createdAt) < comparableTimestamp(right?.createdAt);
}

function metricsRefreshStatusTone(status) {
  return {
    completed: "resolved",
    partial: "matching",
    error: "needs_review"
  }[String(status ?? "").trim().toLowerCase()] ?? "captured";
}

function comparisonToneClass(status) {
  return {
    improved: "improved",
    deteriorated: "deteriorated",
    stable: "stable",
    new: "new"
  }[status] ?? "stable";
}

function geoComparisonToneClass(status) {
  return {
    new: "new",
    changed: "changed",
    removed: "removed"
  }[status] ?? "stable";
}

function geoImpactBandClass(band) {
  return {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low"
  }[band] ?? "stable";
}

function geoTaskColor(band) {
  return {
    critical: "#ff8c6b",
    high: "#ffb347",
    medium: "#75f0cf",
    low: "#97bfe2"
  }[band] ?? "#97bfe2";
}

function geoTaskBadgeText(task) {
  if ((task.watchlistHits ?? 0) > 0) {
    return String(task.watchlistHits);
  }
  return task.impactBand === "critical" ? "!" : String(Math.max(1, Math.round((task.impactScore ?? 0) / 10)));
}

function scaleRelativePolygon(points, scale = 1) {
  return points.map((point) => ({
    x: Number((point.x * scale).toFixed(2)),
    y: Number((point.y * scale).toFixed(2))
  }));
}

function polygonBounds(points) {
  if (!points.length) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  return points.reduce(
    (bounds, point) => ({
      minX: Math.min(bounds.minX, point.x),
      maxX: Math.max(bounds.maxX, point.x),
      minY: Math.min(bounds.minY, point.y),
      maxY: Math.max(bounds.maxY, point.y)
    }),
    { minX: points[0].x, maxX: points[0].x, minY: points[0].y, maxY: points[0].y }
  );
}

function geoTaskIsOpen(task) {
  return ["needs_review", "needs_capture", "scheduled"].includes(task?.status);
}

function compareGeoTaskPriority(left, right) {
  const statusRank = { needs_review: 0, needs_capture: 1, scheduled: 2, resolved: 3, captured: 4 };
  return (
    (statusRank[left?.status] ?? 9) - (statusRank[right?.status] ?? 9) ||
    Number(right?.impactScore ?? 0) - Number(left?.impactScore ?? 0) ||
    Number(right?.watchlistHits ?? 0) - Number(left?.watchlistHits ?? 0) ||
    String(left?.communityName ?? "").localeCompare(String(right?.communityName ?? "")) ||
    String(left?.buildingName ?? "").localeCompare(String(right?.buildingName ?? ""))
  );
}

function compareBrowserSamplingTask(left, right) {
  const lifecycleRank = { needs_capture: 0, needs_review: 1, captured: 2 };
  return (
    (lifecycleRank[left?.taskLifecycleStatus] ?? 9) - (lifecycleRank[right?.taskLifecycleStatus] ?? 9) ||
    Number(right?.priorityScore ?? 0) - Number(left?.priorityScore ?? 0) ||
    String(left?.taskType ?? "").localeCompare(String(right?.taskType ?? "")) ||
    String(left?.communityName ?? "").localeCompare(String(right?.communityName ?? "")) ||
    String(left?.buildingName ?? "").localeCompare(String(right?.buildingName ?? ""))
  );
}

function compareBrowserSamplingMapTask(left, right) {
  const statusRank = { needs_review: 0, needs_capture: 1, in_progress: 2, resolved: 3 };
  return (
    (statusRank[browserSamplingCoverageState(left)] ?? 9) - (statusRank[browserSamplingCoverageState(right)] ?? 9) ||
    compareBrowserSamplingTask(left, right)
  );
}

function browserSamplingTaskKey(task) {
  return task?.buildingId && task?.floorNo != null ? `${task.buildingId}:${task.floorNo}` : null;
}

function setBestBrowserSamplingTask(map, key, task) {
  if (!key) {
    return;
  }
  const current = map.get(key);
  if (!current || compareBrowserSamplingMapTask(task, current) < 0) {
    map.set(key, task);
  }
}

function browserCapturePendingAttentionCount(target) {
  return Number(target?.pendingAttentionCount ?? target?.reviewSummary?.pendingCount ?? 0);
}

function browserCaptureResolvedCount(target) {
  return Number(target?.reviewSummary?.resolvedCount ?? 0);
}

function browserCaptureWaivedCount(target) {
  return Number(target?.reviewSummary?.waivedCount ?? 0);
}

function browserCaptureSupersededCount(target) {
  return Number(target?.reviewSummary?.supersededCount ?? 0);
}

function browserSamplingTargetCount(task) {
  if (!task) {
    return 0;
  }
  return Number(
    task.targetGranularity === "floor"
      ? task.targetPairCount ?? 0
      : task.targetSampleSize ?? 0
  );
}

function browserSamplingCurrentCount(task) {
  if (!task) {
    return 0;
  }
  return Number(
    task.targetGranularity === "floor"
      ? task.currentPairCount ?? 0
      : task.currentSampleSize ?? 0
  );
}

function browserSamplingMissingCount(task) {
  return Math.max(browserSamplingTargetCount(task) - browserSamplingCurrentCount(task), 0);
}

function browserSamplingCoverageState(task) {
  const pendingAttentionCount = browserCapturePendingAttentionCount(task);
  if (pendingAttentionCount > 0) {
    return "needs_review";
  }
  if (browserSamplingMissingCount(task) <= 0 && browserSamplingTargetCount(task) > 0) {
    return "resolved";
  }
  if (browserSamplingCurrentCount(task) > 0 || Number(task?.captureHistoryCount ?? 0) > 0) {
    return "in_progress";
  }
  return "needs_capture";
}

function browserSamplingCoverageLabel(task) {
  return browserSamplingTaskStatusLabel(browserSamplingCoverageState(task));
}

function browserSamplingCoverageProgress(task) {
  const target = browserSamplingTargetCount(task);
  if (target <= 0) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((browserSamplingCurrentCount(task) / target) * 100)));
}
