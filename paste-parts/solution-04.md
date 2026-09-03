+        });
+    }
+
+    holes.sort_by(|a, b| b.cells.len().cmp(&a.cells.len()));
+    holes
+}
+
+/// Drop holes that should not be planned.
+///
+/// Edge holes are the grid being larger than the work, unless the caller has
+/// asked to include them. Area is the cutoff for specks that are one noisy
+/// cell rather than a gap a boat can fill.
+pub fn filter(holes: Vec<Hole>, include_edge: bool, min_area: f64) -> (Vec<Hole>, usize) {
+    let mut kept = Vec::new();
+    let mut skipped = 0;
+    for hole in holes {
+        if !include_edge && hole.on_edge {
+            skipped += 1;
+            continue;
+        }
+        if hole.area + 1.0e-12 < min_area {
+            skipped += 1;
+            continue;
+        }
+        kept.push(hole);
+    }
+    (kept, skipped)
+}
+
+/// How far apart two bounding boxes are, in metres.
+///
+/// Overlapping or touching boxes have distance zero. The value is the gap
+/// between the nearest edges otherwise, which is what you want when deciding
+/// whether a boat that came for one hole should bother with the next.
+fn bbox_gap(a: (f64, f64, f64, f64), b: (f64, f64, f64, f64)) -> f64 {
+    let gap_east = if a.2 < b.0 {
+        b.0 - a.2
+    } else if b.2 < a.0 {
+        a.0 - b.2
+    } else {
+        0.0
+    };
+    let gap_north = if a.3 < b.1 {
+        b.1 - a.3
+    } else if b.3 < a.1 {
+        a.1 - b.3
+    } else {
+        0.0
+    };
+    (gap_east * gap_east + gap_north * gap_north).sqrt()
+}
+
+/// Group holes whose bounding boxes sit within `merge_gap` metres.
+pub fn campaigns(
+    holes: Vec<Hole>,
+    geometry: &GridGeometry,
+    merge_gap: f64,
+) -> Result<Vec<Campaign>> {
+    if !merge_gap.is_finite() || merge_gap < 0.0 {
+        return Err(Error::domain(
+            "merge gap",
+            merge_gap,
+            "finite and not negative",
+        ));
+    }
+    if holes.is_empty() {
+        return Ok(Vec::new());
+    }
+
+    let bounds: Vec<Option<(f64, f64, f64, f64)>> =
+        holes.iter().map(|h| h.metre_bounds(geometry)).collect();
+    let n = holes.len();
+    let mut parent: Vec<usize> = (0..n).collect();
+
+    fn find(parent: &mut [usize], mut i: usize) -> usize {
+        while parent[i] != i {
+            let p = parent[i];
+            parent[i] = parent[p];
+            i = p;
+        }
+        i
+    }
+
+    for i in 0..n {
+        let Some(a) = bounds[i] else { continue };
+        for (j, bound_b) in bounds.iter().enumerate().skip(i + 1) {
+            let Some(b) = *bound_b else { continue };
+            if bbox_gap(a, b) <= merge_gap {
+                let pi = find(&mut parent, i);
+                let pj = find(&mut parent, j);
+                if pi != pj {
+                    parent[pj] = pi;
+                }
+            }
+        }
+    }
+
+    let mut groups: Vec<Vec<Hole>> = vec![Vec::new(); n];
+    for (i, hole) in holes.into_iter().enumerate() {
+        let p = find(&mut parent, i);
+        groups[p].push(hole);
+    }
+
+    let mut out: Vec<Campaign> = groups
+        .into_iter()
+        .filter(|g| !g.is_empty())
+        .map(|holes| Campaign { holes })
+        .collect();
+    out.sort_by(|a, b| {
+        b.area()
+            .partial_cmp(&a.area())
+            .unwrap_or(std::cmp::Ordering::Equal)
+    });
+    Ok(out)
+}
+
+/// Shoalest populated cell that shares an edge or a corner with the campaign.
+///
+/// Spacing has to come off the shallowest water next to the hole, because that
+/// is where the swath is narrowest. Using a depth from the other side of the
+/// block would plan lines too far apart and leave the hole still open.
+pub fn shoalest_neighbour(
+    raster: &DepthRaster,
+    geometry: &GridGeometry,
+    campaign: &Campaign,
+) -> Option<f64> {
+    let mut best: Option<f64> = None;
+    for cell in campaign.cells() {
+        for neighbour in cell.neighbourhood() {
+            if neighbour == cell {
+                continue;
+            }
+            let Some(offset) = geometry.offset_of(neighbour) else {
+                continue;
+            };
+            let Some(depth) = raster.depths[offset] else {
+                continue;
+            };
+            best = Some(match best {
+                Some(d) => d.min(depth),
+                None => depth,
+            });
+        }
+    }
+    best
+}
diff --git a/src/planning/infill.rs b/src/planning/infill.rs
new file mode 100644
index 0000000..0f71ea9
--- /dev/null
+++ b/src/planning/infill.rs
@@ -0,0 +1,506 @@
+//! Planning run lines that fill the holes on a delivered surface.
+//!
+//! The regular block planner is the wrong tool once a survey has already been
+//! run: going back over the whole rectangle repeats water that is already
+//! good. What is left is the interior holidays, grouped into campaigns, with
+//! lines clipped to the empty cells so a populated bridge splits a line in
+//! two. Remainder is what is still open after a swath of the planned spacing
+//! has been painted around every kept line.
+
+use crate::error::{Error, Result};
+use crate::grid::estimator::DepthRaster;
+use crate::grid::geometry::GridGeometry;
+use crate::planning::block::Block;
+use crate::planning::clip::{cell_covered_by_lines, clip_to_mask, segments_to_lines};
+use crate::planning::heading::{along, principal_heading, wrap_half};
+use crate::planning::holes::{campaigns, discover, filter, shoalest_neighbour, Campaign};
+use crate::planning::lines::{plan_crosslines, plan_lines, spacing_for, Plan, PlannedLine};
+use crate::qc::coverage::analyse;
+use crate::units::Angle;
+
+/// Inputs that decide an infill plan.
+#[derive(Debug, Clone, Copy, PartialEq)]
+pub struct InfillOptions {
+    /// Include gaps that touch the grid edge.
+    pub include_edge: bool,
+    /// Holidays smaller than this, in square metres, are skipped.
+    pub min_area: f64,
+    /// Merge holes whose bounding boxes sit this close, in metres.
+    pub merge_gap: f64,
+    /// Heading to run on. `None` takes the long axis of each campaign.
+    pub heading: Option<Angle>,
+    /// Depth used to work out spacing. `None` takes the shoalest neighbour.
+    pub depth: Option<f64>,
+    /// Line spacing. `None` uses [`spacing_for`] with depth, swath and overlap.
+    pub spacing: Option<f64>,
+    /// Swath half angle.
+    pub swath: Angle,
+    /// Fraction of a swath that neighbouring lines repeat.
+    pub overlap: f64,
+    /// Drop clipped pieces shorter than this, in metres.
+    pub min_length: f64,
+    /// Refuse a plan with more main lines than this. `None` means no cap.
+    pub max_lines: Option<usize>,
+    /// Also plan a sparse set of crosslines.
+    pub crosslines: bool,
+    /// Survey speed for the hour estimate, metres per second.
+    pub speed: f64,
+}
+
+impl InfillOptions {
+    /// Defaults that match the command line when nothing extra is passed.
+    ///
+    /// `cell_size` is taken from the surface, not from the configuration:
+    /// four cells of a 0.5 m grid is a different hole to four cells of a
+    /// 5 m grid, and the surface is the thing that has the holes in it.
+    pub fn defaults(cell_size: f64, swath_degrees: f64) -> Result<Self> {
+        if !(cell_size.is_finite() && cell_size > 0.0) {
+            return Err(Error::domain("cell size", cell_size, "finite and positive"));
+        }
+        Ok(InfillOptions {
+            include_edge: false,
+            min_area: 4.0 * cell_size * cell_size,
+            merge_gap: 2.0 * cell_size,
+            heading: None,
+            depth: None,
+            spacing: None,
+            swath: Angle::from_degrees(swath_degrees),
+            overlap: 0.2,
