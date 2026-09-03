+    assert_eq!(planned[0].0, 1);
+    // Two decimal places, and a north-south line over the hole.
+    assert!((planned[0].1 - planned[0].3).abs() < 1.0e-6);
+}
+
+#[test]
+fn a_one_cell_speck_is_skipped_until_the_area_cutoff_is_dropped() {
+    let dir = TempDir::new("infill-speck");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(12, 10.0);
+    punch(&mut raster, 5, 5, 6, 6);
+    let surface = write_surface(&dir, "speck.asc", &raster, &geometry);
+
+    let skipped = run(&["infill", &surface, "--config", &config]);
+    assert_eq!(skipped.status, 0, "{}", skipped.stderr);
+    assert!(skipped.stdout.contains("0 holidays, 0 m², 1 skipped"));
+    assert!(skipped
+        .stdout
+        .contains("remainder: 1 interior holidays, 1 m²"));
+
+    let kept = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--min-area",
+        "0",
+        "--min-length",
+        "0.5",
+    ]);
+    assert_eq!(kept.status, 0, "{}", kept.stderr);
+    assert!(kept.stdout.contains("1 holidays, 1 m², 0 skipped"));
+    assert!(kept.stdout.contains("1 lines,"));
+}
+
+#[test]
+fn an_edge_gap_is_ignored_unless_include_edge_is_set() {
+    let dir = TempDir::new("infill-edge");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(12, 10.0);
+    punch(&mut raster, 0, 0, 1, 12);
+    let surface = write_surface(&dir, "edge.asc", &raster, &geometry);
+
+    let ignored = run(&["infill", &surface, "--config", &config]);
+    assert_eq!(ignored.status, 0, "{}", ignored.stderr);
+    assert!(ignored.stdout.contains("0 holidays, 0 m², 1 skipped"));
+    assert!(ignored
+        .stdout
+        .contains("remainder: 0 interior holidays, 0 m²"));
+
+    let included = run(&["infill", &surface, "--config", &config, "--include-edge"]);
+    assert_eq!(included.status, 0, "{}", included.stderr);
+    assert!(included.stdout.contains("1 holidays, 12 m², 0 skipped"));
+    assert!(included.stdout.contains("1 lines,"));
+}
+
+#[test]
+fn nearby_holes_merge_when_the_gap_allows_it() {
+    let dir = TempDir::new("infill-merge");
+    let config = write_config(&dir);
+    // Two tall thin holes with a four-cell gap. Alone each is taller than it
+    // is wide, so the default heading is north. Together they are a wide
+    // pair, so a merge turns the heading to east.
+    let (mut raster, geometry) = filled(24, 20.0);
+    punch(&mut raster, 4, 8, 7, 14);
+    punch(&mut raster, 11, 8, 14, 14);
+    let surface = write_surface(&dir, "two.asc", &raster, &geometry);
+
+    let separate = run(&["infill", &surface, "--config", &config, "--merge-gap", "0"]);
+    assert_eq!(separate.status, 0, "{}", separate.stderr);
+    assert!(separate.stdout.contains("2 holidays, 36 m², 0 skipped"));
+    assert!(separate.stdout.contains("heading 0 degrees"));
+
+    let merged = run(&["infill", &surface, "--config", &config, "--merge-gap", "6"]);
+    assert_eq!(merged.status, 0, "{}", merged.stderr);
+    assert!(merged.stdout.contains("2 holidays, 36 m², 0 skipped"));
+    assert!(merged.stdout.contains("heading 90 degrees"));
+}
+
+#[test]
+fn a_populated_bridge_splits_a_line_in_two() {
+    let dir = TempDir::new("infill-bridge");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(20, 10.0);
+    punch(&mut raster, 4, 8, 16, 12);
+    for row in 8..12 {
+        raster.depths[row * raster.columns + 10] = Some(10.0);
+    }
+    let surface = write_surface(&dir, "bridge.asc", &raster, &geometry);
+    let out = dir.join("lines.txt");
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--heading",
+        "90",
+        "--min-length",
+        "1",
+        "--out",
+        out.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("2 holidays, 44 m², 0 skipped"));
+    assert!(r.stdout.contains("heading 90 degrees"));
+    assert!(r.stdout.contains("2 lines,"));
+    let planned = parse_line_file(&fs::read_to_string(&out).unwrap());
+    assert_eq!(planned.len(), 2);
+    assert_eq!(planned[0].0, 1);
+    assert_eq!(planned[1].0, 2);
+}
+
+#[test]
+fn the_json_object_carries_the_named_keys() {
+    let dir = TempDir::new("infill-json");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(20, 10.0);
+    punch(&mut raster, 6, 6, 12, 14);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let json = dir.join("rep.json");
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--json",
+        json.to_str().unwrap(),
+        "--speed",
+        "4",
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    let body = fs::read_to_string(&json).unwrap();
+    assert!(body.contains("\"survey\": \"berth 4\""));
+    for key in [
+        "holidays",
+        "skipped",
+        "area_m2",
+        "heading_deg",
+        "spacing_m",
+        "shoalest_m",
+        "lines",
+        "length_m",
+        "hours",
+        "remainder_interior",
+        "remainder_area_m2",
+    ] {
+        assert!(body.contains(&format!("\"{key}\":")), "missing {key}");
+    }
+    assert!(json_f(&body, "hours") > 0.0);
+    assert!(r.stdout.contains("hours at 4.0 m/s"));
+}
+
+#[test]
+fn an_empty_surface_is_refused() {
+    let dir = TempDir::new("infill-empty");
+    let config = write_config(&dir);
+    let geometry = GridGeometry::new(0.0, 0.0, 1.0, 8, 8).unwrap();
+    let raster = DepthRaster {
+        columns: 8,
+        rows: 8,
+        depths: vec![None; 64],
+        estimator: Estimator::Shoalest,
+    };
+    let surface = write_surface(&dir, "empty.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn a_missing_config_is_refused() {
+    let dir = TempDir::new("infill-noconfig");
+    let (raster, geometry) = filled(8, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let r = run(&["infill", &surface]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn max_lines_of_zero_is_refused() {
+    let dir = TempDir::new("infill-max0");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(20, 10.0);
+    punch(&mut raster, 4, 4, 16, 16);
+    let surface = write_surface(&dir, "big.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config, "--max-lines", "0"]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn max_lines_refuses_a_plan_that_would_exceed_it() {
+    let dir = TempDir::new("infill-max1");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(20, 10.0);
+    punch(&mut raster, 4, 4, 16, 16);
+    let surface = write_surface(&dir, "big.asc", &raster, &geometry);
+    let uncapped = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--spacing",
+        "2",
+    ]);
+    assert_eq!(uncapped.status, 0, "{}", uncapped.stderr);
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--max-lines",
+        "1",
+        "--spacing",
+        "2",
+    ]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn a_negative_min_area_is_refused() {
+    let dir = TempDir::new("infill-negarea");
