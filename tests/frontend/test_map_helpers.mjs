import { test } from "node:test";
import assert from "node:assert/strict";

import { centroidFromGeometry, positionForOpportunity } from "../../frontend/user/modules/map.js";

test("centroidFromGeometry: averages finite polygon points", () => {
  assert.deepEqual(
    centroidFromGeometry({
      type: "Polygon",
      coordinates: [
        [
          [121, 31],
          [123, 31],
          [123, 33],
          [121, 33],
        ],
      ],
    }),
    [122, 32],
  );
});

test("centroidFromGeometry: ignores malformed points and null geometry", () => {
  assert.equal(centroidFromGeometry(null), null);
  assert.deepEqual(
    centroidFromGeometry({
      type: "Polygon",
      coordinates: [
        [
          [121, 31],
          ["bad", 31],
          [123, 33],
        ],
      ],
    }),
    [122, 32],
  );
});

test("positionForOpportunity: prefers explicit primary-building center", () => {
  const position = positionForOpportunity({
    primaryBuildingId: "b2",
    buildings: [
      { id: "b1", centerLng: 121, centerLat: 31 },
      { id: "b2", centerLng: "122.5", centerLat: "32.5" },
    ],
  });
  assert.deepEqual(position, [122.5, 32.5]);
});

test("positionForOpportunity: falls back to primary-building geometry centroid", () => {
  const position = positionForOpportunity({
    primaryBuildingId: "b1",
    buildings: [
      {
        id: "b1",
        centerLng: null,
        centerLat: null,
        geometryJson: {
          type: "Polygon",
          coordinates: [
            [
              [120, 30],
              [122, 30],
              [122, 32],
              [120, 32],
            ],
          ],
        },
      },
    ],
  });
  assert.deepEqual(position, [121, 31]);
});
