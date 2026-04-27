function normalizeWorkspaceView(value) {
  return workspaceViews.includes(value) ? value : "frontstage";
}

function normalizeBackstageTab(value) {
  return backstageTabs.includes(value) ? value : "operations";
}

function normalizeOperationsHistoryTab(value) {
  return operationsHistoryTabs.includes(value) ? value : "reference";
}

function normalizeOperationsDetailTab(value) {
  return operationsDetailTabs.includes(value) ? value : "geo";
}

function normalizeOperationsQualityTab(value) {
  return operationsQualityTabs.includes(value) ? value : "workbench";
}

function initialWorkspaceViewFromLocation() {
  try {
    const params = new URLSearchParams(window.location.search);
    return normalizeWorkspaceView(params.get("view"));
  } catch (error) {
    return "frontstage";
  }
}

function initialBackstageTabFromLocation() {
  try {
    const params = new URLSearchParams(window.location.search);
    return normalizeBackstageTab(params.get("backstage"));
  } catch (error) {
    return "operations";
  }
}

function initialOperationsHistoryTabFromLocation() {
  try {
    const params = new URLSearchParams(window.location.search);
    return normalizeOperationsHistoryTab(params.get("opsHistory"));
  } catch (error) {
    return "reference";
  }
}

function initialOperationsDetailTabFromLocation() {
  try {
    const params = new URLSearchParams(window.location.search);
    return normalizeOperationsDetailTab(params.get("opsDetail"));
  } catch (error) {
    return "geo";
  }
}

function initialOperationsQualityTabFromLocation() {
  try {
    const params = new URLSearchParams(window.location.search);
    return normalizeOperationsQualityTab(params.get("opsQuality"));
  } catch (error) {
    return "workbench";
  }
}

function initialOperationsSelectionParamFromLocation(name) {
  try {
    const params = new URLSearchParams(window.location.search);
    if (
      normalizeWorkspaceView(params.get("view")) !== "backstage"
      || normalizeBackstageTab(params.get("backstage")) !== "operations"
    ) {
      return null;
    }
    const value = params.get(name);
    return value && value.trim() ? value.trim() : null;
  } catch (error) {
    return null;
  }
}

