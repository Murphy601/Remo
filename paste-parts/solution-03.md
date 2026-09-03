+        (0.0, 1.0)
+    };
+    if east * east + north * north < 1.0e-18 {
+        return Angle::ZERO;
+    }
+    wrap_half(Angle::from_radians(east.atan2(north)))
+}
+
+/// Reduce a heading into `[0, 180)`.
+pub fn wrap_half(heading: Angle) -> Angle {
+    let mut deg = heading.wrapped().degrees();
+    while deg >= 180.0 {
+        deg -= 180.0;
+    }
+    Angle::from_degrees(deg)
+}
+
+/// Unit direction of a heading, as `(east, north)`.
+pub fn along(heading: Angle) -> (f64, f64) {
+    let (sin_hd, cos_hd) = heading.sin_cos();
+    (sin_hd, cos_hd)
+}
+
+/// Unit direction across a heading, pointing to the right of along.
+pub fn across(heading: Angle) -> (f64, f64) {
+    let (e, n) = along(heading);
+    (n, -e)
+}
+
+/// Whether a cell centre is closer to a heading's along-axis than a width.
+pub fn projected_offset(
+    cell: CellIndex,
+    geometry: &GridGeometry,
+    origin: Projected,
+    across_dir: (f64, f64),
+) -> f64 {
+    let p = geometry.centre_of(cell);
+    (p.east - origin.east) * across_dir.0 + (p.north - origin.north) * across_dir.1
+}
diff --git a/src/planning/holes.rs b/src/planning/holes.rs
new file mode 100644
index 0000000..e6b993a
--- /dev/null
+++ b/src/planning/holes.rs
@@ -0,0 +1,321 @@
+//! Empty cells on a delivered surface, grouped the way a boat would see them.
+//!
+//! Coverage analysis already reports holidays as bounding boxes. Infill needs
+//! the cells themselves: a C-shaped gap and the rectangle that bounds it are
+//! not the same piece of water, and a line laid through the bounding box
+//! surveys seabed that is already good. This module flood-fills the holes,
+//! keeps the cell lists, and merges holes that sit close enough that one
+//! campaign should cover them together.
+
+use crate::error::{Error, Result};
+use crate::grid::estimator::DepthRaster;
+use crate::grid::geometry::{CellIndex, GridGeometry};
+
+/// One contiguous run of empty cells.
+#[derive(Debug, Clone, PartialEq)]
+pub struct Hole {
+    /// Cells in this hole, in the order the flood fill visited them.
+    pub cells: Vec<CellIndex>,
+    /// True when any cell sits on the outer edge of the grid.
+    pub on_edge: bool,
+    /// Area in square metres.
+    pub area: f64,
+}
+
+impl Hole {
+    /// Number of empty cells.
+    pub fn cell_count(&self) -> usize {
+        self.cells.len()
+    }
+
+    /// Axis-aligned bounding box of the cells, as inclusive indices.
+    pub fn index_bounds(&self) -> Option<(CellIndex, CellIndex)> {
+        let first = self.cells.first()?;
+        let mut min_c = first.column;
+        let mut max_c = first.column;
+        let mut min_r = first.row;
+        let mut max_r = first.row;
+        for cell in &self.cells {
+            min_c = min_c.min(cell.column);
+            max_c = max_c.max(cell.column);
+            min_r = min_r.min(cell.row);
+            max_r = max_r.max(cell.row);
+        }
+        Some((CellIndex::new(min_c, min_r), CellIndex::new(max_c, max_r)))
+    }
+
+    /// Bounding box in metres, lower left and upper right corners of the
+    /// cells, not of their centres.
+    pub fn metre_bounds(&self, geometry: &GridGeometry) -> Option<(f64, f64, f64, f64)> {
+        let (lo, hi) = self.index_bounds()?;
+        Some((
+            geometry.origin_east + lo.column as f64 * geometry.cell_size,
+            geometry.origin_north + lo.row as f64 * geometry.cell_size,
+            geometry.origin_east + (hi.column as f64 + 1.0) * geometry.cell_size,
+            geometry.origin_north + (hi.row as f64 + 1.0) * geometry.cell_size,
+        ))
+    }
+
+    /// Longest side of the bounding box, in metres.
+    pub fn extent(&self, geometry: &GridGeometry) -> f64 {
+        match self.metre_bounds(geometry) {
+            Some((e0, n0, e1, n1)) => (e1 - e0).max(n1 - n0),
+            None => 0.0,
+        }
+    }
+}
+
+/// A set of holes that will be planned as one campaign.
+///
+/// Merging is about the boat, not about connectivity on the grid. Two gaps
+/// twenty metres apart with a thin strip of data between them are still one
+/// trip if the merge gap is wider than that strip.
+#[derive(Debug, Clone, PartialEq)]
+pub struct Campaign {
+    /// Holes that belong together.
+    pub holes: Vec<Hole>,
+}
+
+impl Campaign {
+    /// Every empty cell in the campaign.
+    pub fn cells(&self) -> impl Iterator<Item = CellIndex> + '_ {
+        self.holes.iter().flat_map(|h| h.cells.iter().copied())
+    }
+
+    /// Combined area in square metres.
+    pub fn area(&self) -> f64 {
+        self.holes.iter().map(|h| h.area).sum()
+    }
+
+    /// True when any member hole touches the grid edge.
+    pub fn on_edge(&self) -> bool {
+        self.holes.iter().any(|h| h.on_edge)
+    }
+
+    /// Bounding box of every member hole, in metres.
+    pub fn metre_bounds(&self, geometry: &GridGeometry) -> Option<(f64, f64, f64, f64)> {
+        let mut iter = self.holes.iter().filter_map(|h| h.metre_bounds(geometry));
+        let first = iter.next()?;
+        let mut bounds = first;
+        for next in iter {
+            bounds.0 = bounds.0.min(next.0);
+            bounds.1 = bounds.1.min(next.1);
+            bounds.2 = bounds.2.max(next.2);
+            bounds.3 = bounds.3.max(next.3);
+        }
+        Some(bounds)
+    }
+
+    /// A lookup mask: true at offsets that belong to this campaign.
+    pub fn mask(&self, geometry: &GridGeometry) -> Vec<bool> {
+        let mut mask = vec![false; geometry.cell_count()];
+        for cell in self.cells() {
+            if let Some(offset) = geometry.offset_of(cell) {
+                mask[offset] = true;
+            }
+        }
+        mask
+    }
+}
+
+/// Find the empty regions on a raster.
+///
+/// Four-way connectivity, matching the coverage report. Two cells that only
+/// touch at a corner are not a hole a vessel can sail through.
+pub fn discover(raster: &DepthRaster, geometry: &GridGeometry) -> Vec<Hole> {
+    let columns = raster.columns;
+    let rows = raster.rows;
+    let total = columns * rows;
+    let mut seen = vec![false; total];
+    let mut holes = Vec::new();
+    let mut stack = Vec::new();
+    let cell_area = geometry.cell_size * geometry.cell_size;
+
+    for start in 0..total {
+        if seen[start] || raster.depths[start].is_some() {
+            continue;
+        }
+        let mut cells = Vec::new();
+        let mut on_edge = false;
+        stack.clear();
+        stack.push(start);
+        seen[start] = true;
+
+        while let Some(offset) = stack.pop() {
+            let column = offset % columns;
+            let row = offset / columns;
+            cells.push(CellIndex::new(column as i64, row as i64));
+            if column == 0 || row == 0 || column + 1 == columns || row + 1 == rows {
+                on_edge = true;
+            }
+            let push = |c: usize, r: usize, stack: &mut Vec<usize>, seen: &mut Vec<bool>| {
+                let o = r * columns + c;
+                if !seen[o] && raster.depths[o].is_none() {
+                    seen[o] = true;
+                    stack.push(o);
+                }
+            };
+            if column > 0 {
+                push(column - 1, row, &mut stack, &mut seen);
+            }
+            if column + 1 < columns {
+                push(column + 1, row, &mut stack, &mut seen);
+            }
+            if row > 0 {
+                push(column, row - 1, &mut stack, &mut seen);
+            }
+            if row + 1 < rows {
+                push(column, row + 1, &mut stack, &mut seen);
+            }
+        }
+
+        holes.push(Hole {
+            area: cells.len() as f64 * cell_area,
+            cells,
+            on_edge,
