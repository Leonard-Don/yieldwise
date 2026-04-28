function ensureImportRunSelection() {
  const importRuns = effectiveOperationsOverview().importRuns ?? [];
  if (!importRuns.length) {
    state.selectedImportRunId = null;
    state.selectedBaselineRunId = null;
    state.selectedImportRunDetail = null;
    return;
  }
  if (!importRuns.some((item) => item.runId === state.selectedImportRunId)) {
    state.selectedImportRunId = importRuns[0].runId;
    state.selectedBaselineRunId = null;
  }
  if (state.selectedBaselineRunId) {
    const selectedRun = importRuns.find((item) => item.runId === state.selectedImportRunId);
    const baselineRun = importRuns.find((item) => item.runId === state.selectedBaselineRunId);
    if (
      !selectedRun ||
      !baselineRun ||
      baselineRun.runId === selectedRun.runId ||
      !createdAtIsBefore(baselineRun, selectedRun)
    ) {
      state.selectedBaselineRunId = null;
    }
  }
}

function ensureGeoAssetRunSelection() {
  const geoAssetRuns = effectiveOperationsOverview().geoAssetRuns ?? [];
  if (!geoAssetRuns.length) {
    state.selectedGeoAssetRunId = null;
    state.selectedGeoBaselineRunId = null;
    state.selectedGeoAssetRunDetail = null;
    return;
  }
  if (!geoAssetRuns.some((item) => item.runId === state.selectedGeoAssetRunId)) {
    state.selectedGeoAssetRunId = geoAssetRuns[0].runId;
  }
  if (state.selectedGeoBaselineRunId) {
    const selectedRun = geoAssetRuns.find((item) => item.runId === state.selectedGeoAssetRunId);
    const baselineRun = geoAssetRuns.find((item) => item.runId === state.selectedGeoBaselineRunId);
    if (
      !selectedRun ||
      !baselineRun ||
      baselineRun.runId === selectedRun.runId ||
      baselineRun.providerId !== selectedRun.providerId ||
      baselineRun.assetType !== selectedRun.assetType ||
      !createdAtIsBefore(baselineRun, selectedRun)
    ) {
      state.selectedGeoBaselineRunId = null;
    }
  }
}

function normalizeGeoWorkOrderFilters() {
  const items = state.selectedGeoAssetRunDetail?.workOrders ?? [];
  const assignees = new Set(
    items
      .map((item) => (item.assignee ?? "").trim())
      .filter((value) => value)
  );
  const validStatuses = new Set(["all", "open", "assigned", "in_progress", "delivered", "closed"]);
  if (!validStatuses.has(state.geoWorkOrderStatusFilter)) {
    state.geoWorkOrderStatusFilter = "all";
  }
  if (state.geoWorkOrderAssigneeFilter !== "all" && !assignees.has(state.geoWorkOrderAssigneeFilter)) {
    state.geoWorkOrderAssigneeFilter = "all";
  }
}

function availableGeoBaselineRunsFor(runId) {
  const geoAssetRuns = effectiveOperationsOverview().geoAssetRuns ?? [];
  const selectedRun = geoAssetRuns.find((item) => item.runId === runId);
  if (!selectedRun) {
    return [];
  }
  return geoAssetRuns.filter(
    (item) =>
      item.runId !== runId &&
      item.providerId === selectedRun.providerId &&
      item.assetType === selectedRun.assetType &&
      createdAtIsBefore(item, selectedRun)
  );
}

function availableBaselineRunsFor(runId) {
  const importRuns = effectiveOperationsOverview().importRuns ?? [];
  const selectedRun = importRuns.find((item) => item.runId === runId);
  if (!selectedRun) {
    return [];
  }
  return importRuns.filter(
    (item) => item.runId !== runId && createdAtIsBefore(item, selectedRun)
  );
}

