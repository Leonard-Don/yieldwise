function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function bucketForFloor(totalFloors, floorNo) {
  const lowTop = Math.max(1, Math.round(totalFloors * 0.33));
  const highStart = Math.max(lowTop + 1, Math.round(totalFloors * 0.67));
  if (floorNo <= lowTop) {
    return "low";
  }
  if (floorNo >= highStart) {
    return "high";
  }
  return "mid";
}

function hydrateBuilding(community, building, index = 0) {
  const buildingId = building.id ?? `${community.id}-b${index + 1}`;
  const yieldAvg = Number((((building.low ?? 0) + (building.mid ?? 0) + (building.high ?? 0)) / 3).toFixed(2));
  const floorPairs = [
    ["low", building.low ?? 0],
    ["mid", building.mid ?? 0],
    ["high", building.high ?? 0]
  ];
  floorPairs.sort((left, right) => right[1] - left[1]);
  return {
    ...building,
    id: buildingId,
    sequenceNo: building.sequenceNo ?? index + 1,
    communityId: building.communityId ?? community.id,
    communityName: building.communityName ?? community.name,
    districtId: building.districtId ?? community.districtId,
    districtName: building.districtName ?? community.districtName,
    yieldAvg: building.yieldAvg ?? yieldAvg,
    bestBucket: building.bestBucket ?? floorPairs[0][0]
  };
}

function communityCenter(community) {
  if (community?.centerLng != null && community?.centerLat != null) {
    return [Number(community.centerLng), Number(community.centerLat)];
  }
  return normalizeSvgToLonLat(community?.x ?? 380, community?.y ?? 260);
}

function communityAnchorPreview(community) {
  if (!community || community.centerLng != null || community.centerLat != null) {
    return null;
  }
  if (community.previewCenterLng != null && community.previewCenterLat != null) {
    return {
      centerLng: Number(community.previewCenterLng),
      centerLat: Number(community.previewCenterLat),
      anchorSource: community.previewAnchorSource ?? "candidate_preview",
      anchorQuality: community.previewAnchorQuality ?? null,
      anchorName: community.previewAnchorName ?? community.candidateSuggestions?.[0]?.name ?? null,
      anchorAddress: community.previewAnchorAddress ?? community.candidateSuggestions?.[0]?.address ?? null
    };
  }
  return null;
}

function interpolateFloorYield(building, floorNo) {
  const totalFloors = Math.max(Number(building.totalFloors ?? 1), 1);
  if (totalFloors === 1) {
    return Number((building.mid ?? building.low ?? building.high ?? 0).toFixed(2));
  }
  const midFloor = Math.max(2, Math.round(totalFloors / 2));
  let yieldPct = 0;
  if (floorNo <= midFloor) {
    const ratio = (floorNo - 1) / Math.max(1, midFloor - 1);
    yieldPct = (building.low ?? 0) + ((building.mid ?? 0) - (building.low ?? 0)) * ratio;
  } else {
    const ratio = (floorNo - midFloor) / Math.max(1, totalFloors - midFloor);
    yieldPct = (building.mid ?? 0) + ((building.high ?? 0) - (building.mid ?? 0)) * ratio;
  }
  return Number(yieldPct.toFixed(2));
}

function buildFloorCurve(building, avgPriceWanEstimate) {
  const totalFloors = Math.max(Number(building.totalFloors ?? 1), 1);
  const averageYield = building.yieldAvg ?? Number((((building.low ?? 0) + (building.mid ?? 0) + (building.high ?? 0)) / 3).toFixed(2));

  return Array.from({ length: totalFloors }, (_, index) => {
    const floorNo = index + 1;
    const bucket = bucketForFloor(totalFloors, floorNo);
    const floorRatio = totalFloors === 1 ? 0 : index / Math.max(1, totalFloors - 1);
    const pricePremiumPct = -2 + floorRatio * 8;
    const shapeBonus = 10 - Math.abs(floorRatio - 0.68) * 18;
    const estPriceWan = Number((avgPriceWanEstimate * (1 + pricePremiumPct / 100)).toFixed(1));
    const yieldPct = interpolateFloorYield(building, floorNo);
    const estMonthlyRent = Math.round(estPriceWan * 10000 * (yieldPct / 100) / 12);
    const yieldSpreadVsBuilding = Number((yieldPct - averageYield).toFixed(2));
    const opportunityScore = Math.round(
      clamp(
        (building.score ?? 0) -
          10 +
          yieldSpreadVsBuilding * 40 +
          shapeBonus -
          Math.max(pricePremiumPct, 0) * 0.35 +
          Math.max(-pricePremiumPct, 0) * 0.12,
        0,
        99
      )
    );

    return {
      floorNo,
      bucket,
      bucketLabel: { low: "低楼层", mid: "中楼层", high: "高楼层" }[bucket],
      yieldPct,
      yieldSpreadVsBuilding,
      estPriceWan,
      estMonthlyRent,
      pricePremiumPct: Number(pricePremiumPct.toFixed(2)),
      opportunityScore,
      arbitrageTag:
        opportunityScore >= 90
          ? "重点关注"
          : opportunityScore >= 82
            ? "可跟进"
            : opportunityScore >= 74
              ? "观察"
              : "对照"
    };
  });
}

function buildingSvgPoint(community, building) {
  const buildingCount = Math.max(community.buildings?.length ?? 1, 1);
  const sequenceNo = building?.sequenceNo ?? 1;
  const sequenceOffset = sequenceNo - (buildingCount + 1) / 2;
  return {
    x: community.x + sequenceOffset * 18,
    y: community.y + (sequenceNo % 2 === 0 ? 10 : -10)
  };
}

function floorSvgPoint(community, building, floorNo) {
  const anchor = buildingSvgPoint(community, building);
  const safeFloor = Math.max(Number(floorNo) || 1, 1);
  const totalFloors = Math.max(Number(building?.totalFloors) || safeFloor, 1);
  const floorOffset = Math.min(safeFloor, totalFloors) / totalFloors;
  return {
    x: anchor.x + ((safeFloor % 4) - 1.5) * 2.2,
    y: anchor.y - floorOffset * 22
  };
}

function footprintDimensions(building, scale = 1) {
  const totalFloors = Math.max(Number(building?.totalFloors) || 12, 1);
  return {
    halfWidth: (8 + Math.min(totalFloors, 30) * 0.22) * scale,
    halfHeight: (6 + Math.min(totalFloors, 30) * 0.14) * scale
  };
}

function footprintPolygon(center, dimensions) {
  return [
    { x: Number((center.x - dimensions.halfWidth).toFixed(2)), y: Number((center.y + dimensions.halfHeight * 0.45).toFixed(2)) },
    { x: Number((center.x + dimensions.halfWidth * 0.35).toFixed(2)), y: Number((center.y + dimensions.halfHeight).toFixed(2)) },
    { x: Number((center.x + dimensions.halfWidth).toFixed(2)), y: Number((center.y - dimensions.halfHeight * 0.35).toFixed(2)) },
    { x: Number((center.x - dimensions.halfWidth * 0.25).toFixed(2)), y: Number((center.y - dimensions.halfHeight).toFixed(2)) }
  ];
}

function buildingFootprintPoints(community, building) {
  return footprintPolygon(buildingSvgPoint(community, building), footprintDimensions(building, 1));
}

function floorFootprintPoints(community, building, floorNo) {
  return footprintPolygon(floorSvgPoint(community, building, floorNo), footprintDimensions(building, 0.82));
}

function polygonPointsAttribute(points) {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
}

function footprintCentroid(points) {
  if (!points.length) {
    return { x: 0, y: 0 };
  }
  const total = points.reduce(
    (sum, point) => ({ x: sum.x + point.x, y: sum.y + point.y }),
    { x: 0, y: 0 }
  );
  return {
    x: Number((total.x / points.length).toFixed(2)),
    y: Number((total.y / points.length).toFixed(2))
  };
}

function footprintPathToLonLat(points) {
  const ring = points.map((point) => normalizeSvgToLonLat(point.x, point.y));
  if (ring.length) {
    const [firstLon, firstLat] = ring[0];
    const [lastLon, lastLat] = ring[ring.length - 1];
    if (firstLon !== lastLon || firstLat !== lastLat) {
      ring.push([firstLon, firstLat]);
    }
  }
  return ring;
}

function fallbackDistrictPolygonPath(district) {
  const rawPolygon = district?.polygon;
  if (!rawPolygon) {
    return [];
  }
  const points = String(rawPolygon)
    .trim()
    .split(/\s+/)
    .map((segment) => segment.split(",").map(Number))
    .filter((pair) => pair.length === 2 && Number.isFinite(pair[0]) && Number.isFinite(pair[1]))
    .map(([x, y]) => normalizeSvgToLonLat(x, y));
  if (!points.length) {
    return [];
  }
  const [firstLon, firstLat] = points[0];
  const [lastLon, lastLat] = points[points.length - 1];
  if (firstLon !== lastLon || firstLat !== lastLat) {
    points.push([firstLon, firstLat]);
  }
  return points;
}

function polygonCenterLonLat(ring) {
  if (!Array.isArray(ring) || !ring.length) {
    return null;
  }
  const rawPoints = ring.slice(0, ring.length > 1 ? -1 : ring.length);
  const points = rawPoints
    .map((point) => {
      if (Array.isArray(point) && point.length >= 2) {
        return [Number(point[0]), Number(point[1])];
      }
      const lng = typeof point?.getLng === "function" ? point.getLng() : point?.lng;
      const lat = typeof point?.getLat === "function" ? point.getLat() : point?.lat;
      if (Number.isFinite(Number(lng)) && Number.isFinite(Number(lat))) {
        return [Number(lng), Number(lat)];
      }
      return null;
    })
    .filter((point) => Array.isArray(point) && Number.isFinite(point[0]) && Number.isFinite(point[1]));
  if (!points.length) {
    return null;
  }
  const total = points.reduce(
    (sum, [lon, lat]) => ({ lon: sum.lon + Number(lon), lat: sum.lat + Number(lat) }),
    { lon: 0, lat: 0 }
  );
  return [Number((total.lon / points.length).toFixed(6)), Number((total.lat / points.length).toFixed(6))];
}

function featureSvgPoints(feature) {
  const points = feature?.properties?.svg_points;
  if (!Array.isArray(points)) {
    return [];
  }
  return points
    .filter((point) => Array.isArray(point) && point.length >= 2)
    .map(([x, y]) => ({ x: Number(x), y: Number(y) }));
}

function featureSvgCenter(feature) {
  const svgCenter = feature?.properties?.svg_center;
  if (Array.isArray(svgCenter) && svgCenter.length >= 2) {
    return { x: Number(svgCenter[0]), y: Number(svgCenter[1]) };
  }
  const svgPoints = featureSvgPoints(feature);
  return svgPoints.length ? footprintCentroid(svgPoints) : null;
}

function featureLonLatPath(feature) {
  const geometry = feature?.geometry;
  if (geometry?.type === "Polygon" && Array.isArray(geometry.coordinates?.[0])) {
    return geometry.coordinates[0].map(([lon, lat]) => [Number(lon), Number(lat)]);
  }
  return [];
}

function featureLonLatCenter(feature) {
  const properties = feature?.properties ?? {};
  if (properties.center_lng != null && properties.center_lat != null) {
    return [Number(properties.center_lng), Number(properties.center_lat)];
  }
  const geometry = feature?.geometry;
  if (geometry?.type === "Point" && Array.isArray(geometry.coordinates)) {
    return geometry.coordinates.map((value) => Number(value));
  }
  return polygonCenterLonLat(featureLonLatPath(feature));
}

function normalizeSvgToLonLat(x, y) {
  const lon = 121.05 + (x / 760) * 0.8;
  const lat = 31.0 + ((520 - y) / 520) * 0.55;
  return [Number(lon.toFixed(6)), Number(lat.toFixed(6))];
}

function normalizeLonLatToSvg(lon, lat) {
  const x = ((Number(lon) - 121.05) / 0.8) * 760;
  const y = 520 - ((Number(lat) - 31.0) / 0.55) * 520;
  return {
    x: Number(x.toFixed(2)),
    y: Number(y.toFixed(2))
  };
}
