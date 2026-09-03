+    let (mut raster, geometry) = filled(20, 20, 10.0);
+    punch(&mut raster, 6, 6, 12, 14);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        config_path.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    // 2 * 10 * tan(30) * 0.8 ≈ 9.2 m, not the 27.7 m of a 60 degree swath.
+    assert!(r.stdout.contains("spacing 9.2 m from shoalest 10.0 m"));
+}
+
+#[test]
+fn an_unknown_option_is_refused() {
+    let dir = TempDir::new("infill-unknown");
+    let config = write_config(&dir);
+    let (raster, geometry) = filled(8, 8, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let r = run(&["infill", &surface, "--config", &config, "--banana", "1"]);
+    assert_ne!(r.status, 0);
+}
+
+#[test]
+fn alternate_directions_flip_every_other_line() {
+    let dir = TempDir::new("infill-alt");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(24, 24, 10.0);
+    punch(&mut raster, 4, 4, 20, 20);
+    let surface = write_surface(&dir, "hole.asc", &raster, &geometry);
+    let out = dir.join("lines.txt");
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--spacing",
+        "4",
+        "--heading",
+        "0",
+        "--out",
+        out.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    let planned = parse_line_file(&fs::read_to_string(&out).unwrap());
+    assert!(planned.len() >= 3);
+    // Heading 0 is north-south, so easting is constant on a line. Odd lines
+    // run the other way, which shows up as the northing of the start and end
+    // swapping relative to the even lines.
+    let even_northward = planned[0].4 > planned[0].2;
+    let odd_northward = planned[1].4 > planned[1].2;
+    assert_ne!(even_northward, odd_northward);
+}
+
+#[test]
+fn remainder_stays_open_when_the_swath_is_too_narrow() {
+    let dir = TempDir::new("infill-remain");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(30, 30, 10.0);
+    punch(&mut raster, 5, 5, 25, 25);
+    let surface = write_surface(&dir, "wide.asc", &raster, &geometry);
+    let json = dir.join("left.json");
+    // half-width = spacing / (2*(1-overlap)) = 12/2 = 6 m on a 20 m hole.
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--heading",
+        "0",
+        "--spacing",
+        "12",
+        "--overlap",
+        "0",
+        "--min-length",
+        "1",
+        "--json",
+        json.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("1 holidays, 400 m², 0 skipped"));
+    assert!(r.stdout.contains("spacing 12.0 m"));
+    assert!(r.stdout.contains("remainder: 1 interior holidays, 20 m²"));
+    let body = fs::read_to_string(&json).unwrap();
+    assert_eq!(json_i(&body, "remainder_interior"), 1);
+    assert!((json_f(&body, "remainder_area_m2") - 20.0).abs() < 1.0e-6);
+}
+
+#[test]
+fn remainder_closes_when_the_paint_covers_the_hole() {
+    let dir = TempDir::new("infill-covered");
+    let config = write_config(&dir);
+    let (mut raster, geometry) = filled(30, 30, 10.0);
+    punch(&mut raster, 5, 5, 25, 25);
+    let surface = write_surface(&dir, "wide.asc", &raster, &geometry);
+    let json = dir.join("closed.json");
+    // half-width = 40 / 2 = 20 m, which covers this 20 m hole.
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        &config,
+        "--heading",
+        "0",
+        "--spacing",
+        "40",
+        "--overlap",
+        "0",
+        "--min-length",
+        "1",
+        "--json",
+        json.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    assert!(r.stdout.contains("remainder: 0 interior holidays, 0 m²"));
+    let body = fs::read_to_string(&json).unwrap();
+    assert_eq!(json_i(&body, "remainder_interior"), 0);
+    assert!(json_f(&body, "remainder_area_m2").abs() < 1.0e-6);
+}
+
+#[test]
+fn quoted_survey_names_round_trip_through_json() {
+    let dir = TempDir::new("infill-quote");
+    let config_text = r#"
+[survey]
+name = "berth \"4\""
+utm_zone = 36
+[vessel]
+draft = 1.8
+[grid]
+cell_size = 1.0
+"#;
+    let config_path = dir.join("survey.toml");
+    fs::write(&config_path, config_text).unwrap();
+    let (raster, geometry) = filled(8, 8, 10.0);
+    let surface = write_surface(&dir, "full.asc", &raster, &geometry);
+    let json = dir.join("rep.json");
+    let r = run(&[
+        "infill",
+        &surface,
+        "--config",
+        config_path.to_str().unwrap(),
+        "--json",
+        json.to_str().unwrap(),
+    ]);
+    assert_eq!(r.status, 0, "{}", r.stderr);
+    let body = fs::read_to_string(&json).unwrap();
+    assert!(body.contains("\"survey\": \"berth \\\"4\\\"\""));
+}


