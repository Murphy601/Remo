+    let config = write_config(&dir);
+    let (raster, geometry) = filled(8, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config, "--min-area", "-1"]);
+    assert_ne!(r.status, 0);
+}
diff --git a/tests/infill_edges.rs b/tests/infill_edges.rs
new file mode 100644
index 0000000..27d44c1
--- /dev/null
+++ b/tests/infill_edges.rs
@@ -0,0 +1,578 @@
+//! Further corners of the infill command: headings, crosslines, leftovers.
+
+mod common;
+
+use std::fs;
+use std::process::Command;
+
+use common::TempDir;
+use plumbline::grid::estimator::{DepthRaster, Estimator};
+use plumbline::grid::geometry::GridGeometry;
+use plumbline::io::ascii_grid::write_ascii_grid;
+
+const EXE: &str = env!("CARGO_BIN_EXE_plumbline");
+
+const CONFIG: &str = r#"
+[survey]
+name = "berth 4"
+order = "order 1"
+utm_zone = 36
+
+[vessel]
+draft = 1.8
+
+[grid]
+cell_size = 1.0
+
+[cleaning]
+max_swath_angle = 60.0
+"#;
+
+struct Run {
+    status: i32,
+    stdout: String,
+    stderr: String,
+}
+
+fn run(arguments: &[&str]) -> Run {
+    let output = Command::new(EXE)
+        .args(arguments)
+        .output()
+        .expect("could not run the tool");
+    Run {
+        status: output.status.code().unwrap_or(-1),
+        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
+        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
+    }
+}
+
+fn write_config(dir: &TempDir) -> String {
+    let path = dir.join("survey.toml");
+    fs::write(&path, CONFIG).unwrap();
+    path.to_string_lossy().to_string()
+}
+
+fn filled(columns: usize, rows: usize, depth: f64) -> (DepthRaster, GridGeometry) {
+    let geometry = GridGeometry::new(0.0, 0.0, 1.0, columns, rows).unwrap();
+    let raster = DepthRaster {
+        columns,
+        rows,
+        depths: vec![Some(depth); columns * rows],
+        estimator: Estimator::Shoalest,
+    };
+    (raster, geometry)
+}
+
+fn punch(raster: &mut DepthRaster, c0: usize, r0: usize, c1: usize, r1: usize) {
+    for row in r0..r1 {
+        for col in c0..c1 {
+            raster.depths[row * raster.columns + col] = None;
+        }
+    }
+}
+
+fn write_surface(
+    dir: &TempDir,
+    name: &str,
+    raster: &DepthRaster,
+    geometry: &GridGeometry,
+) -> String {
+    let path = dir.join(name);
+    write_ascii_grid(&path, raster, geometry, 1).unwrap();
+    path.to_string_lossy().to_string()
+}
+
+fn parse_line_file(text: &str) -> Vec<(usize, f64, f64, f64, f64)> {
+    let mut out = Vec::new();
+    for line in text.lines() {
+        if line.starts_with('#') || line.trim().is_empty() {
+            continue;
+        }
+        let mut bits = line.split_whitespace();
+        out.push((
+            bits.next().unwrap().parse().unwrap(),
+            bits.next().unwrap().parse().unwrap(),
+            bits.next().unwrap().parse().unwrap(),
+            bits.next().unwrap().parse().unwrap(),
+            bits.next().unwrap().parse().unwrap(),
+        ));
+    }
+    out
+}
+
+fn json_i(text: &str, key: &str) -> i64 {
+    let needle = format!("\"{key}\": ");
+    let rest = text.split(&needle).nth(1).expect(key);
+    rest.split([',', '\n'])
+        .next()
+        .unwrap()
+        .trim()
+        .parse()
+        .unwrap()
+}
+
+fn json_f(text: &str, key: &str) -> f64 {
+    let needle = format!("\"{key}\": ");
+    let rest = text.split(&needle).nth(1).expect(key);
+    rest.split([',', '\n'])
+        .next()
+        .unwrap()
+        .trim()
+        .parse()
+        .unwrap()
+}
+
+#[test]
+fn a_long_east_west_hole_takes_a_heading_near_ninety() {
+    let dir = TempDir::new("infill-axis");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(30, 16, 8.0);
+    punch(&mut raster, 4, 7, 26, 10);
+    let surface = write_surface(&dir, "ew.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config, "--min-area", "4"]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("1 holidays, 66 m², 0 skipped"));
+    // Long axis is east-west, so the default heading is 90 degrees, not 0.
+    assert!(r.stdout.contains("heading 90 degrees"));
+}
+
+#[test]
+fn an_explicit_heading_overrides_the_long_axis() {
+    let dir = TempDir::new("infill-heading");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(30, 16, 8.0);
+    punch(&mut raster, 4, 7, 26, 10);
+    let surface = write_surface(&dir, "ew.asc", &raster, &geometry);
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--heading",
+        "0",
+        "--min-length",
+        "1",
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("heading 0 degrees"));
+}
+
+#[test]
+fn spacing_can_be_set_directly_and_depth_is_still_reported() {
+    let dir = TempDir::new("infill-spacing");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(20, 20, 12.0);
+    punch(&mut raster, 5, 5, 15, 15);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--spacing",
+        "5",
+        "--heading",
+        "0",
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("spacing 5.0 m from shoalest 12.0 m"));
+    let lines_word = r
+        .stdout
+        .lines()
+        .find(|l| l.contains("lines,") && l.contains("m on line"))
+        .unwrap();
+    let n: usize = lines_word
+        .split_whitespace()
+        .next()
+        .unwrap()
+        .parse()
+        .unwrap();
+    assert!(
+        n >= 2,
+        "a 10 m hole at 5 m spacing needs more than one line: {lines_word}"
+    );
+}
+
+#[test]
+fn shoalest_neighbour_follows_the_water_next_to_the_hole() {
+    let dir = TempDir::new("infill-shoal");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(18, 18, 20.0);
+    punch(&mut raster, 6, 6, 12, 12);
+    // A shallow ring on the north side of the hole.
+    for col in 6..12 {
+        raster.depths[12 * raster.columns + col] = Some(6.0);
+    }
+    let surface = write_surface(&dir, "shoal.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
