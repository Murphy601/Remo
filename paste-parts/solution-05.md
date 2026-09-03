+            min_length: 2.0 * cell_size,
+            max_lines: None,
+            crosslines: false,
+            speed: 3.0,
+        })
+    }
+}
+
+/// One campaign after it has been planned.
+#[derive(Debug, Clone, PartialEq)]
+pub struct CampaignPlan {
+    /// The holes this plan fills.
+    pub campaign: Campaign,
+    /// Heading that was used.
+    pub heading: Angle,
+    /// Spacing that was used.
+    pub spacing: f64,
+    /// Depth that produced the spacing, when one was available.
+    pub shoalest: Option<f64>,
+    /// Main-scheme lines, clipped to the hole.
+    pub lines: Vec<PlannedLine>,
+    /// Crosslines, clipped the same way.
+    pub crosslines: Vec<PlannedLine>,
+}
+
+/// Everything the infill command reports on.
+#[derive(Debug, Clone, PartialEq)]
+pub struct InfillResult {
+    /// Name of the survey, from the configuration.
+    pub survey: String,
+    /// Campaigns that were planned, largest first.
+    pub campaigns: Vec<CampaignPlan>,
+    /// Holidays that were skipped (edge, or under the area cutoff).
+    pub skipped: usize,
+    /// Combined area of the campaigns, square metres.
+    pub area_m2: f64,
+    /// Heading printed for the report: the first campaign's, or zero.
+    pub heading: Angle,
+    /// Spacing printed for the report: the first campaign's, or zero.
+    pub spacing: f64,
+    /// Shoalest depth printed for the report.
+    pub shoalest: f64,
+    /// Main lines across every campaign, numbered from one.
+    pub lines: Vec<PlannedLine>,
+    /// Crosslines across every campaign, numbered from one.
+    pub crosslines: Vec<PlannedLine>,
+    /// Interior holidays still open after the planned swaths are painted.
+    pub remainder_interior: usize,
+    /// Combined area of those remaining interior holidays.
+    pub remainder_area_m2: f64,
+}
+
+impl InfillResult {
+    /// Total on-line length of the main scheme.
+    pub fn length_m(&self) -> f64 {
+        self.lines.iter().map(PlannedLine::length).sum()
+    }
+
+    /// Hours at the requested speed, main scheme only, including turns.
+    pub fn hours_at(&self, speed: f64) -> f64 {
+        if speed <= 0.0 {
+            return f64::INFINITY;
+        }
+        let line: f64 = self.length_m();
+        let turn: f64 = self
+            .lines
+            .windows(2)
+            .map(|w| w[0].end.distance_to(&w[1].start))
+            .sum();
+        (line + turn) / speed / 3600.0
+    }
+}
+
+/// Plan infill lines over the holes of a surface.
+pub fn plan_infill(
+    raster: &DepthRaster,
+    geometry: &GridGeometry,
+    survey: &str,
+    options: InfillOptions,
+) -> Result<InfillResult> {
+    if raster.columns != geometry.columns || raster.rows != geometry.rows {
+        return Err(Error::Config(
+            "raster and geometry disagree about the shape of the grid".into(),
+        ));
+    }
+    if raster.populated() == 0 {
+        return Err(Error::Config(
+            "the surface has no soundings to plan around".into(),
+        ));
+    }
+    if !options.min_area.is_finite() || options.min_area < 0.0 {
+        return Err(Error::domain(
+            "min area",
+            options.min_area,
+            "finite and not negative",
+        ));
+    }
+    if !options.min_length.is_finite() || options.min_length < 0.0 {
+        return Err(Error::domain(
+            "min length",
+            options.min_length,
+            "finite and not negative",
+        ));
+    }
+    if let Some(max) = options.max_lines {
+        if max == 0 {
+            return Err(Error::Config(
+                "--max-lines of 0 would refuse every plan".into(),
+            ));
+        }
+    }
+    if options.speed <= 0.0 {
+        return Err(Error::domain("speed", options.speed, "positive"));
+    }
+
+    let discovered = discover(raster, geometry);
+    let (kept, skipped) = filter(discovered, options.include_edge, options.min_area);
+    let groups = campaigns(kept, geometry, options.merge_gap)?;
+
+    let mut campaign_plans = Vec::new();
+    for group in groups {
+        campaign_plans.push(plan_campaign(raster, geometry, &group, options)?);
+    }
+
+    let mut lines = Vec::new();
+    let mut crosses = Vec::new();
+    for plan in &campaign_plans {
+        lines.extend(plan.lines.iter().copied());
+        crosses.extend(plan.crosslines.iter().copied());
+    }
+    for (i, line) in lines.iter_mut().enumerate() {
+        line.number = i + 1;
+    }
+    for (i, line) in crosses.iter_mut().enumerate() {
+        line.number = i + 1;
+    }
+
+    if let Some(max) = options.max_lines {
+        if lines.len() > max {
+            return Err(Error::Config(format!(
+                "infill would need {} lines, --max-lines is {max}",
+                lines.len()
+            )));
+        }
+    }
+
+    let area_m2 = campaign_plans.iter().map(|c| c.campaign.area()).sum();
+    let heading = campaign_plans
+        .first()
+        .map(|c| c.heading)
+        .unwrap_or(Angle::ZERO);
+    let spacing = campaign_plans.first().map(|c| c.spacing).unwrap_or(0.0);
+    let shoalest = campaign_plans
+        .first()
+        .and_then(|c| c.shoalest)
+        .unwrap_or(0.0);
+
+    let (remainder_interior, remainder_area_m2) =
+        remainder(raster, geometry, &lines, spacing, options.overlap);
+
+    Ok(InfillResult {
+        survey: survey.to_string(),
+        campaigns: campaign_plans,
+        skipped,
+        area_m2,
+        heading,
+        spacing,
+        shoalest,
+        lines,
+        crosslines: crosses,
+        remainder_interior,
+        remainder_area_m2,
+    })
+}
+
+fn plan_campaign(
+    raster: &DepthRaster,
+    geometry: &GridGeometry,
+    campaign: &Campaign,
+    options: InfillOptions,
+) -> Result<CampaignPlan> {
+    let heading = match options.heading {
+        Some(h) => wrap_half(h),
+        None => principal_heading(campaign, geometry),
+    };
+    let shoalest = match options.depth {
+        Some(d) => Some(d),
+        None => shoalest_neighbour(raster, geometry, campaign),
+    };
+    let spacing = match options.spacing {
+        Some(s) => {
+            if !(s.is_finite() && s > 0.0) {
+                return Err(Error::domain("spacing", s, "finite and positive"));
+            }
+            s
+        }
+        None => {
+            let depth = shoalest.ok_or_else(|| {
+                Error::Config("no populated cell next to the hole to take a depth from".into())
+            })?;
+            spacing_for(depth, options.swath, options.overlap)?
+        }
+    };
+
+    let Some(bounds) = campaign.metre_bounds(geometry) else {
+        return Ok(CampaignPlan {
+            campaign: campaign.clone(),
+            heading,
+            spacing,
+            shoalest,
+            lines: Vec::new(),
+            crosslines: Vec::new(),
+        });
+    };
+
+    // A little pad so the first and last candidate lines sit on the hole
+    // rather than a cell outside it. plan_lines already insets by half a
+    // spacing from the bounding box; the pad stops a hole one cell wider
+    // than the spacing from vanishing.
+    let pad = geometry.cell_size * 0.51;
