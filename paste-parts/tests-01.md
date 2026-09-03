diff --git a/tests/infill_command.rs b/tests/infill_command.rs
new file mode 100644
index 0000000..7e3d135
--- /dev/null
+++ b/tests/infill_command.rs
@@ -0,0 +1,440 @@
+//! The infill command: holes on a delivered surface become run lines.
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
+name = "demo launch"
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
+/// A square grid of populated cells, south-origin, origin at (100, 200).
+fn filled(side: usize, depth: f64) -> (DepthRaster, GridGeometry) {
+    let geometry = GridGeometry::new(100.0, 200.0, 1.0, side, side).unwrap();
+    let raster = DepthRaster {
+        columns: side,
+        rows: side,
+        depths: vec![Some(depth); side * side],
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
+        let n: usize = bits.next().unwrap().parse().unwrap();
+        let a: f64 = bits.next().unwrap().parse().unwrap();
+        let b: f64 = bits.next().unwrap().parse().unwrap();
+        let c: f64 = bits.next().unwrap().parse().unwrap();
+        let d: f64 = bits.next().unwrap().parse().unwrap();
+        out.push((n, a, b, c, d));
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
+fn infill_help_describes_the_surface_and_the_config() {
+    let r = run(&["infill", "--help"]);
+    assert_eq!(r.status, 0);
+    let text = format!("{}{}", r.stdout, r.stderr);
+    assert!(text.contains("infill"));
+    assert!(text.contains("--config"));
+    assert!(text.contains("--include-edge"));
+    assert!(text.contains("--min-area"));
+    assert!(text.contains("--merge-gap"));
+    assert!(text.contains("--depth"));
+    assert!(text.contains("--swath"));
+    assert!(text.contains("--json"));
+}
+
+#[test]
+fn the_top_level_usage_lists_infill() {
+    let r = run(&[]);
+    assert_eq!(r.status, 0);
+    assert!(r
+        .stdout
+        .lines()
+        .any(|line| line.split_whitespace().next() == Some("infill")));
+}
+
+#[test]
+fn a_surface_with_no_holes_writes_no_lines() {
+    let dir = TempDir::new("infill-full");
+    let config = write_config(&dir);
+    let (raster, geometry) = filled(16, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let out = dir.join("lines.txt");
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--out",
+        out.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("infill of berth 4:"));
+    assert!(r.stdout.contains("0 holidays, 0 m², 0 skipped"));
+    assert!(r.stdout.contains("0 lines\n"));
+    assert!(r.stdout.contains("remainder: 0 interior holidays, 0 m²"));
+    let text = fs::read_to_string(&out).unwrap();
+    assert!(text.starts_with("# line start_east start_north end_east end_north"));
+    assert!(parse_line_file(&text).is_empty());
+}
+
+#[test]
+fn an_interior_rectangle_is_planned_and_closes() {
+    let dir = TempDir::new("infill-rect");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(20, 10.0);
+    punch(&mut raster, 6, 6, 12, 14);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let json = dir.join("rep.json");
+    let lines = dir.join("lines.txt");
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--out",
+        lines.to_str().unwrap(),
+        "--json",
+        json.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("1 holidays, 48 m², 0 skipped"));
+    assert!(r
+        .stdout
+        .contains("heading 0 degrees, spacing 27.7 m from shoalest 10.0 m"));
+    assert!(r.stdout.contains("1 lines,"));
+    assert!(r.stdout.contains("remainder: 0 interior holidays, 0 m²"));
+    assert!(r
+        .stdout
+        .contains(&format!("wrote {}", lines.to_str().unwrap())));
+    let body = fs::read_to_string(&json).unwrap();
+    assert_eq!(json_i(&body, "holidays"), 1);
+    assert_eq!(json_i(&body, "skipped"), 0);
+    assert_eq!(json_i(&body, "lines"), 1);
+    assert_eq!(json_i(&body, "remainder_interior"), 0);
+    assert!((json_f(&body, "area_m2") - 48.0).abs() < 1.0e-6);
+    assert!((json_f(&body, "shoalest_m") - 10.0).abs() < 1.0e-6);
+    assert!((json_f(&body, "heading_deg") - 0.0).abs() < 1.0e-6);
+    let planned = parse_line_file(&fs::read_to_string(&lines).unwrap());
+    assert_eq!(planned.len(), 1);
