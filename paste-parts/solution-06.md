+    let block = Block::rectangle(
+        "hole",
+        bounds.0 - pad,
+        bounds.1 - pad,
+        bounds.2 + pad,
+        bounds.3 + pad,
+    )?;
+
+    let raw = plan_lines(&block, heading, spacing)?;
+    let mask = campaign.mask(geometry);
+    let mut clipped = Vec::new();
+    for line in &raw.lines {
+        let segs = clip_to_mask(line.start, line.end, geometry, &mask, options.min_length);
+        clipped.extend(segments_to_lines(&segs, clipped.len() + 1));
+    }
+
+    // One line down the long axis when spacing is wider than the hole and
+    // the bounding-box planner produced nothing that survived the clip.
+    if clipped.is_empty() {
+        let along_dir = along(heading);
+        let centre = crate::geodesy::utm::Projected::new(
+            (bounds.0 + bounds.2) / 2.0,
+            (bounds.1 + bounds.3) / 2.0,
+        );
+        let span = (bounds.2 - bounds.0).hypot(bounds.3 - bounds.1) + spacing;
+        let start = crate::geodesy::utm::Projected::new(
+            centre.east - along_dir.0 * span,
+            centre.north - along_dir.1 * span,
+        );
+        let end = crate::geodesy::utm::Projected::new(
+            centre.east + along_dir.0 * span,
+            centre.north + along_dir.1 * span,
+        );
+        let segs = clip_to_mask(start, end, geometry, &mask, options.min_length);
+        clipped.extend(segments_to_lines(&segs, 1));
+    }
+
+    let mut plan = Plan {
+        block: "hole".into(),
+        spacing,
+        heading,
+        lines: clipped,
+    };
+    plan.alternate_directions();
+
+    let mut cross = Vec::new();
+    if options.crosslines && !plan.lines.is_empty() {
+        let mut raw_cross = plan_crosslines(&block, &raw)?;
+        raw_cross.alternate_directions();
+        for line in &raw_cross.lines {
+            let segs = clip_to_mask(line.start, line.end, geometry, &mask, options.min_length);
+            cross.extend(segments_to_lines(&segs, cross.len() + 1));
+        }
+    }
+
+    Ok(CampaignPlan {
+        campaign: campaign.clone(),
+        heading,
+        spacing,
+        shoalest,
+        lines: plan.lines,
+        crosslines: cross,
+    })
+}
+
+fn remainder(
+    raster: &DepthRaster,
+    geometry: &GridGeometry,
+    lines: &[PlannedLine],
+    spacing: f64,
+    overlap: f64,
+) -> (usize, f64) {
+    if lines.is_empty() {
+        let coverage = analyse(raster, geometry);
+        let interior: Vec<_> = coverage.interior_holidays().collect();
+        let area: f64 = interior.iter().map(|h| h.area).sum();
+        return (interior.len(), area);
+    }
+    let denom = 2.0 * (1.0 - overlap).max(1.0e-6);
+    let half_width = spacing / denom;
+    let mut painted = raster.clone();
+    for (offset, depth) in painted.depths.iter_mut().enumerate() {
+        if depth.is_some() {
+            continue;
+        }
+        let Some(index) = geometry.index_at_offset(offset) else {
+            continue;
+        };
+        let centre = geometry.centre_of(index);
+        if cell_covered_by_lines(centre, lines, half_width) {
+            *depth = Some(1.0);
+        }
+    }
+    let coverage = analyse(&painted, geometry);
+    let interior: Vec<_> = coverage.interior_holidays().collect();
+    let area: f64 = interior.iter().map(|h| h.area).sum();
+    (interior.len(), area)
+}
+
+/// The text report the command prints.
+pub fn format_report(result: &InfillResult, speed: f64, wrote: &[String]) -> String {
+    let holidays = result
+        .campaigns
+        .iter()
+        .map(|c| c.campaign.holes.len())
+        .sum::<usize>();
+    let mut out = String::new();
+    out.push_str(&format!("infill of {}:\n", result.survey));
+    out.push_str(&format!(
+        "{} holidays, {} m², {} skipped\n",
+        holidays,
+        display_zero(result.area_m2, 0),
+        result.skipped
+    ));
+    if holidays > 0 {
+        out.push_str(&format!(
+            "heading {} degrees, spacing {} m from shoalest {} m\n",
+            display_zero(result.heading.degrees(), 0),
+            display_zero(result.spacing, 1),
+            display_zero(result.shoalest, 1)
+        ));
+        out.push_str(&format!(
+            "{} lines, {} m on line, {} hours at {} m/s\n",
+            result.lines.len(),
+            display_zero(result.length_m(), 1),
+            display_zero(result.hours_at(speed), 2),
+            display_zero(speed, 1)
+        ));
+    } else {
+        out.push_str("0 lines\n");
+    }
+    out.push_str(&format!(
+        "remainder: {} interior holidays, {} m²\n",
+        result.remainder_interior,
+        display_zero(result.remainder_area_m2, 0)
+    ));
+    for path in wrote {
+        out.push_str(&format!("wrote {path}\n"));
+    }
+    out
+}
+
+/// Format a quantity without IEEE negative zero leaking into the report.
+fn display_zero(value: f64, decimals: usize) -> String {
+    let v = if value.is_finite() && value.abs() >= 1.0e-12 {
+        value
+    } else {
+        0.0
+    };
+    match decimals {
+        0 => format!("{v:.0}"),
+        1 => format!("{v:.1}"),
+        2 => format!("{v:.2}"),
+        _ => format!("{v:.6}"),
+    }
+}
+
+/// The JSON object `--json` writes.
+pub fn format_json(result: &InfillResult, speed: f64) -> String {
+    let holidays = result
+        .campaigns
+        .iter()
+        .map(|c| c.campaign.holes.len())
+        .sum::<usize>();
+    let survey = escape_json(&result.survey);
+    format!(
+        "{{\n  \"survey\": \"{survey}\",\n  \"holidays\": {holidays},\n  \"skipped\": {},\n  \"area_m2\": {},\n  \"heading_deg\": {},\n  \"spacing_m\": {},\n  \"shoalest_m\": {},\n  \"lines\": {},\n  \"length_m\": {},\n  \"hours\": {},\n  \"remainder_interior\": {},\n  \"remainder_area_m2\": {}\n}}\n",
+        result.skipped,
+        display_zero(result.area_m2, 6),
+        display_zero(result.heading.degrees(), 6),
+        display_zero(result.spacing, 6),
+        display_zero(result.shoalest, 6),
+        result.lines.len(),
+        display_zero(result.length_m(), 6),
+        display_zero(result.hours_at(speed), 6),
+        result.remainder_interior,
+        display_zero(result.remainder_area_m2, 6)
+    )
+}
+
+fn escape_json(text: &str) -> String {
+    let mut out = String::with_capacity(text.len());
+    for c in text.chars() {
+        match c {
+            '"' => out.push_str("\\\""),
+            '\\' => out.push_str("\\\\"),
+            '\n' => out.push_str("\\n"),
+            '\r' => out.push_str("\\r"),
+            '\t' => out.push_str("\\t"),
+            c if (c as u32) < 0x20 => {
+                use std::fmt::Write as _;
+                let _ = write!(out, "\\u{:04x}", c as u32);
+            }
+            c => out.push(c),
+        }
+    }
+    out
+}
+
+/// Write a plan file in the same format `plan --out` uses.
+pub fn write_lines(path: &std::path::Path, lines: &[PlannedLine]) -> Result<()> {
+    use std::fs::File;
+    use std::io::{BufWriter, Write};
+    let file = File::create(path).map_err(|e| Error::io(path, e))?;
+    let mut out = BufWriter::new(file);
+    writeln!(out, "# line start_east start_north end_east end_north")
+        .map_err(|e| Error::io(path, e))?;
+    for line in lines {
+        writeln!(
+            out,
+            "{} {:.2} {:.2} {:.2} {:.2}",
+            line.number, line.start.east, line.start.north, line.end.east, line.end.north
+        )
+        .map_err(|e| Error::io(path, e))?;
+    }
+    out.flush().map_err(|e| Error::io(path, e))?;
+    Ok(())
+}
diff --git a/src/planning/mod.rs b/src/planning/mod.rs
index d6da68c..588cf1b 100644
