+    assert!(r.stdout.contains("from shoalest 6.0 m"));
+}
+
+#[test]
+fn a_depth_flag_overrides_the_neighbour() {
+    let dir = TempDir::new("infill-depthflag");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(18, 18, 20.0);
+    punch(&mut raster, 6, 6, 12, 12);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config, "--depth", "15"]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("from shoalest 15.0 m"));
+}
+
+#[test]
+fn crosslines_are_written_next_to_the_main_file() {
+    let dir = TempDir::new("infill-cross");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(24, 24, 10.0);
+    punch(&mut raster, 4, 4, 20, 20);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let out = dir.join("main.txt");
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--spacing",
+        "4",
+        "--heading",
+        "0",
+        "--crosslines",
+        "--min-length",
+        "1",
+        "--out",
+        out.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    let cross = format!("{}.crosslines", out.to_str().unwrap());
+    assert!(r
+        .stdout
+        .contains(&format!("wrote {}", out.to_str().unwrap())));
+    assert!(r.stdout.contains(&format!("wrote {cross}")));
+    assert!(fs::read_to_string(&out)
+        .unwrap()
+        .starts_with("# line start_east start_north end_east end_north"));
+    let cross_text = fs::read_to_string(&cross).unwrap();
+    assert!(cross_text.starts_with("# line start_east start_north end_east end_north"));
+    assert!(
+        !parse_line_file(&cross_text).is_empty(),
+        "crosslines should not be an empty header: {cross_text}"
+    );
+}
+
+#[test]
+fn pieces_shorter_than_min_length_are_dropped() {
+    let dir = TempDir::new("infill-short");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(12, 12, 10.0);
+    punch(&mut raster, 5, 5, 6, 6);
+    let surface = write_surface(&dir, "speck.asc", &raster, &geometry);
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--min-area",
+        "0",
+        "--min-length",
+        "50",
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("1 holidays, 1 m², 0 skipped"));
+    assert!(r.stdout.contains("0 lines, 0.0 m on line"));
+    assert!(r.stdout.contains("remainder: 1 interior holidays, 1 m²"));
+}
+
+#[test]
+fn a_negative_merge_gap_is_refused() {
+    let dir = TempDir::new("infill-neggap");
+    let config = write_config(&dir);
+    let (raster, geometry) = filled(8, 8, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config, "--merge-gap", "-2"]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn a_negative_min_length_is_refused() {
+    let dir = TempDir::new("infill-neglen");
+    let config = write_config(&dir);
+    let (raster, geometry) = filled(8, 8, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--min-length",
+        "-4",
+    ]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn a_non_positive_speed_is_refused() {
+    let dir = TempDir::new("infill-speed");
+    let config = write_config(&dir);
+    let (raster, geometry) = filled(8, 8, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config, "--speed", "0"]);
+    assert_ne!(r.status, 0);
+    let negative = run(&["infill", &surface, "--config", &config, "--speed", "-1"]);
+    assert_ne!(negative.status, 0);
+}
+
+#[test]
+fn a_missing_surface_is_refused() {
+    let dir = TempDir::new("infill-nosurf");
+    let config = write_config(&dir);
+    let r = run(&["infill", "--config", &config]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn a_missing_surface_file_names_the_path() {
+    let dir = TempDir::new("infill-gone");
+    let config = write_config(&dir);
+    let r = run(&[
+        "infill",
+        dir.join("nope.asc").to_str().unwrap(),
+        "--config",
+        &config,
+    ]);
+    assert_eq!(r.status, 1);
+    assert!(r.stderr.contains("nope.asc"));
+}
+
+#[test]
+fn the_swath_flag_narrows_spacing() {
+    let dir = TempDir::new("infill-swathflag");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(20, 20, 10.0);
+    punch(&mut raster, 6, 6, 12, 14);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let wide = run(&["infill", &surface, "--config", &config]);
+    assert_eq!(wide.status, 0, "{}", wide.stderr);
+    assert!(wide.stdout.contains("spacing 27.7 m from shoalest 10.0 m"));
+    let tight = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--swath",
+        "30",
+    ]);
+    assert_eq!(tight.status, 0, "{}", tight.stderr);
+    // 2 * 10 * tan(30) * 0.8 ≈ 9.2 m, against the 27.7 m of the 60° default.
+    assert!(tight.stdout.contains("spacing 9.2 m from shoalest 10.0 m"));
+}
+
+#[test]
+fn a_heading_of_two_seventy_wraps_to_ninety() {
+    let dir = TempDir::new("infill-wrap270");
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
+        "270",
+        "--min-length",
+        "1",
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("heading 90 degrees"));
+}
+
+#[test]
+fn a_heading_of_one_eighty_prints_zero() {
+    let dir = TempDir::new("infill-wrap180");
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
+        "180",
+        "--min-length",
+        "1",
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("heading 0 degrees"));
+}
+
+#[test]
+fn swath_from_the_config_changes_the_spacing() {
+    let dir = TempDir::new("infill-swath");
+    let tight = r#"
+[survey]
+name = "berth 4"
+utm_zone = 36
+[vessel]
+draft = 1.8
+[grid]
+cell_size = 1.0
+[cleaning]
+max_swath_angle = 30.0
+"#;
+    let config_path = dir.join("survey.toml");
+    fs::write(&config_path, tight).unwrap();
