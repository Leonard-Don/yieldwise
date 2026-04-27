function hydrateDistrictsPayload(rawDistricts) {
  return (rawDistricts ?? []).map((district) => ({
    ...district,
    communities: (district.communities ?? []).map(hydrateCommunity)
  }));
}

function hydrateCommunity(community) {
  const buildings = (community.buildings ?? []).map((building, index) => hydrateBuilding(community, building, index));
  const focusMatch = buildings.find((building) => building.name === community.buildingFocus);
  return {
    ...community,
    centerLng: community.centerLng ?? community.center_lng ?? null,
    centerLat: community.centerLat ?? community.center_lat ?? null,
    anchorSource: community.anchorSource ?? community.anchor_source ?? null,
    anchorQuality: community.anchorQuality ?? community.anchor_quality ?? null,
    previewCenterLng: community.previewCenterLng ?? community.preview_center_lng ?? null,
    previewCenterLat: community.previewCenterLat ?? community.preview_center_lat ?? null,
    previewAnchorSource: community.previewAnchorSource ?? community.preview_anchor_source ?? null,
    previewAnchorQuality: community.previewAnchorQuality ?? community.preview_anchor_quality ?? null,
    previewAnchorName: community.previewAnchorName ?? community.preview_anchor_name ?? null,
    previewAnchorAddress: community.previewAnchorAddress ?? community.preview_anchor_address ?? null,
    anchorDecisionState: community.anchorDecisionState ?? community.anchor_decision_state ?? null,
    latestAnchorReview: community.latestAnchorReview ?? community.latest_anchor_review ?? null,
    sampleStatus: community.sampleStatus ?? community.sample_status ?? (community.sample > 0 ? "active_metrics" : "dictionary_only"),
    sampleStatusLabel: community.sampleStatusLabel ?? community.sample_status_label ?? "状态待补",
    buildings,
    primaryBuildingId: community.primaryBuildingId ?? focusMatch?.id ?? buildings[0]?.id ?? null
  };
}

