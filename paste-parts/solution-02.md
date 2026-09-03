+//! hole is two lines, not one. Running the populated strip again is wasted
+//! water and it also pulls the overlap arithmetic out of shape, because the
+//! boat would be covering cells the original survey already owns. The clipper
+//! walks the candidate line, keeps the stretches that sit on empty cells, and
+//! throws away pieces too short to be worth a turn.
+
+use crate::geodesy::utm::Projected;
+use crate::grid::geometry::GridGeometry;
+use crate::planning::lines::PlannedLine;
+
+/// One contiguous stretch of a candidate line that sits on empty cells.
+#[derive(Debug, Clone, Copy, PartialEq)]
+pub struct Segment {
+    /// Start of the stretch.
+    pub start: Projected,
+    /// End of the stretch.
+    pub end: Projected,
+}
+
+impl Segment {
+    /// Length in metres.
+    pub fn length(&self) -> f64 {
+        self.start.distance_to(&self.end)
+    }
+
+    /// Drop stretches shorter than `min_length`.
+    pub fn long_enough(&self, min_length: f64) -> bool {
+        self.length() + 1.0e-9 >= min_length
+    }
+}
+
+/// Walk a candidate line and keep the parts that fall on `mask`.
+///
+/// `mask` is row-major and the same shape as `geometry`. Sampling is at half
+/// a cell, which is enough to notice a one-cell populated bridge and not so
+/// fine that a long line becomes expensive. Each kept run is extended to the
+/// edges of the cells it covers so the written line matches what `plan`
+/// writes for a rectangular block of the same size.
+pub fn clip_to_mask(
+    start: Projected,
+    end: Projected,
+    geometry: &GridGeometry,
+    mask: &[bool],
+    min_length: f64,
+) -> Vec<Segment> {
+    let length = start.distance_to(&end);
+    if !(length.is_finite() && length > 0.0) {
+        return Vec::new();
+    }
+    let step = (geometry.cell_size * 0.5).max(0.05);
+    let samples = ((length / step).ceil() as usize).max(2);
+    let de = (end.east - start.east) / length;
+    let dn = (end.north - start.north) / length;
+
+    let mut on_hole = Vec::with_capacity(samples);
+    for i in 0..samples {
+        let t = if samples == 1 {
+            0.0
+        } else {
+            length * i as f64 / (samples - 1) as f64
+        };
+        let p = Projected::new(start.east + de * t, start.north + dn * t);
+        let index = geometry.index_of(p);
+        let hit = geometry
+            .offset_of(index)
+            .map(|o| mask.get(o).copied().unwrap_or(false))
+            .unwrap_or(false);
+        on_hole.push((t, p, hit));
+    }
+
+    let mut runs: Vec<Segment> = Vec::new();
+    let mut run_start: Option<(f64, Projected)> = None;
+    let mut last_hit: Option<(f64, Projected)> = None;
+
+    for &(t, p, hit) in &on_hole {
+        if hit {
+            if run_start.is_none() {
+                run_start = Some((t, p));
+            }
+            last_hit = Some((t, p));
+        } else if let (Some(s), Some(e)) = (run_start.take(), last_hit.take()) {
+            push_run(&mut runs, s.1, e.1, de, dn, geometry);
+        }
+    }
+    if let (Some(s), Some(e)) = (run_start, last_hit) {
+        push_run(&mut runs, s.1, e.1, de, dn, geometry);
+    }
+
+    runs.into_iter()
+        .filter(|s| s.long_enough(min_length))
+        .collect()
+}
+
+fn push_run(
+    runs: &mut Vec<Segment>,
+    start: Projected,
+    end: Projected,
+    de: f64,
+    dn: f64,
+    geometry: &GridGeometry,
+) {
+    // Nudge each end out by a quarter cell so a run that only sampled cell
+    // centres still covers the cell it is meant to fill.
+    let pad = geometry.cell_size * 0.25;
+    let start = Projected::new(start.east - de * pad, start.north - dn * pad);
+    let end = Projected::new(end.east + de * pad, end.north + dn * pad);
+    if start.distance_to(&end) > 0.0 {
+        runs.push(Segment { start, end });
+    }
+}
+
+/// Turn clipped segments into numbered planned lines.
+pub fn segments_to_lines(segments: &[Segment], first_number: usize) -> Vec<PlannedLine> {
+    segments
+        .iter()
+        .enumerate()
+        .map(|(i, s)| PlannedLine {
+            number: first_number + i,
+            start: s.start,
+            end: s.end,
+        })
+        .collect()
+}
+
+/// Shortest distance from a point to a finite line segment.
+pub fn distance_to_segment(point: Projected, start: Projected, end: Projected) -> f64 {
+    let abe = end.east - start.east;
+    let abn = end.north - start.north;
+    let length2 = abe * abe + abn * abn;
+    if length2 <= 1.0e-18 {
+        return point.distance_to(&start);
+    }
+    let t = ((point.east - start.east) * abe + (point.north - start.north) * abn) / length2;
+    let t = t.clamp(0.0, 1.0);
+    let closest = Projected::new(start.east + t * abe, start.north + t * abn);
+    point.distance_to(&closest)
+}
+
+/// True when a cell centre lies within `half_width` of any of the lines.
+pub fn cell_covered_by_lines(
+    cell_centre: Projected,
+    lines: &[PlannedLine],
+    half_width: f64,
+) -> bool {
+    lines
+        .iter()
+        .any(|line| distance_to_segment(cell_centre, line.start, line.end) <= half_width + 1.0e-9)
+}
diff --git a/src/planning/heading.rs b/src/planning/heading.rs
new file mode 100644
index 0000000..f963749
--- /dev/null
+++ b/src/planning/heading.rs
@@ -0,0 +1,105 @@
+//! Heading of a campaign from the shape of its empty cells.
+//!
+//! A long thin hole should be run along its length, not across it, or the boat
+//! spends the day turning. The heading that does that is the first principal
+//! axis of the empty cell centres, expressed the same way the block planner
+//! expresses a heading: clockwise from grid north.
+
+use crate::geodesy::utm::Projected;
+use crate::grid::geometry::{CellIndex, GridGeometry};
+use crate::units::Angle;
+
+use super::holes::Campaign;
+
+/// Principal-axis heading of a campaign, wrapped into `[0, 180)`.
+///
+/// Reciprocal headings are the same scheme: running 90 degrees and running
+/// 270 degrees lays the same lines. Wrapping into a half turn keeps the
+/// default stable and stops a nearly-square hole flipping between two answers
+/// that differ only in direction.
+pub fn principal_heading(campaign: &Campaign, geometry: &GridGeometry) -> Angle {
+    let points: Vec<Projected> = campaign
+        .cells()
+        .map(|cell| geometry.centre_of(cell))
+        .collect();
+    heading_of_points(&points)
+}
+
+/// Principal-axis heading of a cloud of projected points.
+pub fn heading_of_points(points: &[Projected]) -> Angle {
+    if points.len() < 2 {
+        return Angle::ZERO;
+    }
+
+    let n = points.len() as f64;
+    let mut mean_e = 0.0;
+    let mut mean_n = 0.0;
+    for p in points {
+        mean_e += p.east;
+        mean_n += p.north;
+    }
+    mean_e /= n;
+    mean_n /= n;
+
+    let mut cov_ee = 0.0;
+    let mut cov_nn = 0.0;
+    let mut cov_en = 0.0;
+    for p in points {
+        let de = p.east - mean_e;
+        let dn = p.north - mean_n;
+        cov_ee += de * de;
+        cov_nn += dn * dn;
+        cov_en += de * dn;
+    }
+
+    // Eigenvector of the 2x2 covariance for the larger eigenvalue. The
+    // degenerate case (a round hole, or every cell the same) falls back to
+    // north so the caller still has a number to print.
+    let trace = cov_ee + cov_nn;
+    let det = cov_ee * cov_nn - cov_en * cov_en;
+    let disc = (trace * trace / 4.0 - det).max(0.0).sqrt();
+    let lambda = trace / 2.0 + disc;
+    let (east, north) = if cov_en.abs() > 1.0e-12 {
+        (lambda - cov_nn, cov_en)
+    } else if cov_ee >= cov_nn {
+        (1.0, 0.0)
+    } else {
