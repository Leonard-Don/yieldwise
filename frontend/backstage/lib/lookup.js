function findCommunityById(communityId) {
  return (
    districts.flatMap((district) => district.communities).find((community) => community.id === communityId) ??
    mapCommunities.find((community) => community.id === communityId) ??
    null
  );
}

function findBuildingById(buildingId) {
  for (const district of districts) {
    for (const community of district.communities) {
      const building = (community.buildings ?? []).find((item) => item.id === buildingId);
      if (building) {
        return { community, building };
      }
    }
  }
  return null;
}

function findBuildingGeoFeature(buildingId) {
  return state.buildingGeoFeatures.find((feature) => feature?.properties?.building_id === buildingId) ?? null;
}

function findFloorGeoFeature(buildingId, floorNo) {
  return (
    state.floorGeoFeatures.find(
      (feature) =>
        feature?.properties?.building_id === buildingId &&
        Number(feature?.properties?.floor_no) === Number(floorNo)
    ) ?? null
  );
}

function resolveBuildingGeometry(community, building) {
  const fallbackPoints = buildingFootprintPoints(community, building);
  const fallbackCenter = buildingSvgPoint(community, building);
  const feature = findBuildingGeoFeature(building.id);
  const svgPoints = featureSvgPoints(feature);
  const center = featureSvgCenter(feature) ?? fallbackCenter;
  const lonLatPath = featureLonLatPath(feature);
  return {
    center,
    svgPoints: svgPoints.length ? svgPoints : fallbackPoints,
    lonLatPath: lonLatPath.length ? lonLatPath : footprintPathToLonLat(fallbackPoints),
    position: featureLonLatCenter(feature) ?? normalizeSvgToLonLat(center.x, center.y)
  };
}

function resolveFloorGeometry(item) {
  const lookup = findBuildingById(item.buildingId);
  if (!lookup) {
    return null;
  }
  const fallbackPoints = floorFootprintPoints(lookup.community, lookup.building, item.floorNo);
  const fallbackCenter = floorSvgPoint(lookup.community, lookup.building, item.floorNo);
  const feature = findFloorGeoFeature(item.buildingId, item.floorNo);
  const svgPoints = featureSvgPoints(feature);
  const center = featureSvgCenter(feature) ?? fallbackCenter;
  const lonLatPath = featureLonLatPath(feature);
  return {
    center,
    svgPoints: svgPoints.length ? svgPoints : fallbackPoints,
    lonLatPath: lonLatPath.length ? lonLatPath : footprintPathToLonLat(fallbackPoints),
    position: featureLonLatCenter(feature) ?? normalizeSvgToLonLat(center.x, center.y)
  };
}
