function canUseDemoFallback() {
  return Boolean(runtimeConfig?.mockEnabled);
}

function currentDataMode() {
  return runtimeConfig?.activeDataMode ?? operationsOverview?.summary?.activeDataMode ?? "empty";
}

function applyDataModeDefaults() {
  const usingLegacyDefaults = state.minYield === 2.4 && state.maxBudget === 1200 && state.minSamples === 20;
  if (!usingLegacyDefaults) {
    return;
  }
  if (currentDataMode() === "staged" || currentDataMode() === "empty") {
    state.minYield = 0;
    state.maxBudget = 10000;
    state.minSamples = 1;
  }
}

function effectiveOperationsOverview() {
  return operationsOverview ?? emptyOperationsOverview;
}

function districtDirectory() {
  const directory = new Map();
  districts.forEach((district) => {
    directory.set(district.id, { id: district.id, name: district.name, short: district.short });
  });
  mapCommunities.forEach((community) => {
    if (!directory.has(community.districtId)) {
      directory.set(community.districtId, {
        id: community.districtId,
        name: community.districtName ?? community.districtId,
        short: community.districtShort ?? community.districtName ?? community.districtId
      });
    }
  });
  return Array.from(directory.values()).sort((left, right) => left.id.localeCompare(right.id, "zh-Hans-CN"));
}

