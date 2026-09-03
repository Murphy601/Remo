diff --git a/src/cli/help.rs b/src/cli/help.rs
index 2ed80e3..90c00a4 100644
--- a/src/cli/help.rs
+++ b/src/cli/help.rs
@@ -17,6 +17,7 @@ commands:
   cast      what two sound speed casts do to the same beams
   compare   compare two surfaces, for crossline analysis
   plan      lay out run lines over a survey block
+  infill    plan run lines that fill holes on a delivered surface
   simulate  write a synthetic ping file, for testing a configuration
 
 run plumbline <command> --help for the options of one command
@@ -112,6 +113,34 @@ options:
   --out <file>        write the lines out
 ";
 
+/// Usage for the infill command.
+pub const INFILL: &str = "\
+plumbline infill <surface.asc> --config <file>
+
+Plans run lines through the coverage holes on a delivered surface. Gaps that
+touch the grid edge are ignored unless --include-edge is set, because those
+are usually the grid being bigger than the work. Nearby holes are merged into
+one campaign. Lines are clipped to the empty cells, so a populated strip
+through a hole splits a line in two.
+
+options:
+  --config <file>     survey configuration, required
+  --min-area <m2>     skip holidays smaller than this, default four cells
+  --merge-gap <m>     merge holes this close, default two cell sizes
+  --heading <deg>     line heading, default the long axis of each campaign
+  --depth <metres>    depth for spacing, default shoalest neighbour
+  --swath <degrees>   half angle, default cleaning.max_swath_angle or 60
+  --overlap <0 to 1>  fraction of a swath the next line repeats, default 0.2
+  --spacing <metres>  set the spacing directly instead
+  --speed <m/s>       survey speed for the time estimate, default 3
+  --min-length <m>    drop clipped pieces shorter than this, default two cells
+  --max-lines <n>     refuse a plan with more main lines than this
+  --include-edge      also plan gaps that touch the grid edge
+  --crosslines        plan a sparse set across the main heading
+  --out <file>        write the lines, same format as plan
+  --json <file>       write the same numbers as json
+";
+
 /// Usage for the simulate command.
 pub const SIMULATE: &str = "\
 plumbline simulate <output.pbf>
@@ -137,6 +166,7 @@ pub fn for_command(command: Option<&str>) -> &'static str {
         Some("cast") => CAST,
         Some("compare") => COMPARE,
         Some("plan") => PLAN,
+        Some("infill") => INFILL,
         Some("simulate") => SIMULATE,
         _ => USAGE,
     }
diff --git a/src/cli/infill.rs b/src/cli/infill.rs
new file mode 100644
index 0000000..f04f6c9
--- /dev/null
+++ b/src/cli/infill.rs
@@ -0,0 +1,117 @@
+//! The infill command: holes on a surface in, run lines out.
+
+use std::fs;
+use std::path::Path;
+
+use crate::cli::args::{Args, Spec};
+use crate::config::survey::SurveyConfig;
+use crate::error::{Error, Result};
+use crate::grid::estimator::{DepthRaster, Estimator};
+use crate::io::ascii_grid::read_ascii_grid;
+use crate::planning::infill::{
+    format_json, format_report, plan_infill, write_lines, InfillOptions,
+};
+use crate::units::Angle;
+
+/// What this command accepts.
+pub fn spec() -> Spec {
+    Spec::new()
+        .option("config")
+        .option("min-area")
+        .option("merge-gap")
+        .option("heading")
+        .option("depth")
+        .option("swath")
+        .option("overlap")
+        .option("spacing")
+        .option("speed")
+        .option("min-length")
+        .option("max-lines")
+        .option("out")
+        .option("json")
+        .flag("include-edge")
+        .flag("crosslines")
+        .positional(1, Some(1))
+}
+
+/// Run the command.
+pub fn run(args: &Args) -> Result<String> {
+    args.check(&spec())?;
+
+    let surface = args
+        .positional
+        .first()
+        .ok_or_else(|| Error::Config("a surface file is needed".into()))?;
+    let config_path = args.value("config")?;
+    let config = SurveyConfig::read(config_path)?;
+    let grid = read_ascii_grid(surface)?;
+    let raster = DepthRaster {
+        columns: grid.geometry.columns,
+        rows: grid.geometry.rows,
+        depths: grid.values,
+        estimator: Estimator::Shoalest,
+    };
+
+    let swath_default = config.swath_limit.unwrap_or(60.0);
+    let mut options = InfillOptions::defaults(grid.geometry.cell_size, swath_default)?;
+    options.include_edge = args.flag("include-edge");
+    options.crosslines = args.flag("crosslines");
+
+    if args.has("min-area") {
+        options.min_area = args.number("min-area")?;
+    }
+    if args.has("merge-gap") {
+        options.merge_gap = args.number("merge-gap")?;
+    }
+    if args.has("heading") {
+        options.heading = Some(Angle::from_degrees(args.number("heading")?));
+    }
+    if args.has("depth") {
+        options.depth = Some(args.number("depth")?);
+    }
+    if args.has("swath") {
+        options.swath = Angle::from_degrees(args.number("swath")?);
+    }
+    if args.has("overlap") {
+        options.overlap = args.number("overlap")?;
+    }
+    if args.has("spacing") {
+        options.spacing = Some(args.number("spacing")?);
+    }
+    if args.has("speed") {
+        options.speed = args.number("speed")?;
+    }
+    if args.has("min-length") {
+        options.min_length = args.number("min-length")?;
+    }
+    if args.has("max-lines") {
+        let n = args.number("max-lines")?;
+        if n != n.trunc() || n < 0.0 {
+            return Err(Error::Config(format!(
+                "--max-lines should be a whole number, it is {n}"
+            )));
+        }
+        options.max_lines = Some(n as usize);
+    }
+
+    let result = plan_infill(&raster, &grid.geometry, &config.name, options)?;
+
+    let mut wrote = Vec::new();
+    if args.has("out") {
+        let path = args.value("out")?;
+        write_lines(Path::new(path), &result.lines)?;
+        wrote.push(path.to_string());
+        if options.crosslines {
+            let cross_path = format!("{path}.crosslines");
+            write_lines(Path::new(&cross_path), &result.crosslines)?;
+            wrote.push(cross_path);
+        }
+    }
+    if args.has("json") {
+        let path = args.value("json")?;
+        fs::write(path, format_json(&result, options.speed)).map_err(|e| Error::io(path, e))?;
+        wrote.push(path.to_string());
+    }
+
+    Ok(format_report(&result, options.speed, &wrote))
+}
diff --git a/src/cli/mod.rs b/src/cli/mod.rs
index 398f313..1713d54 100644
--- a/src/cli/mod.rs
+++ b/src/cli/mod.rs
@@ -8,6 +8,7 @@ pub mod cast;
 pub mod compare;
 pub mod grid;
 pub mod help;
+pub mod infill;
 pub mod info;
 pub mod plan;
 pub mod reduce;
diff --git a/src/main.rs b/src/main.rs
index 12f6b37..d7e7375 100644
--- a/src/main.rs
+++ b/src/main.rs
@@ -3,7 +3,7 @@
 use std::process::ExitCode;
 
 use plumbline::cli::args::Args;
-use plumbline::cli::{cast, compare, grid, help, info, plan, reduce, simulate};
+use plumbline::cli::{cast, compare, grid, help, infill, info, plan, reduce, simulate};
 
 fn main() -> ExitCode {
     let raw: Vec<String> = std::env::args().skip(1).collect();
@@ -30,6 +30,7 @@ fn main() -> ExitCode {
         Some("compare") => compare::run(&args),
         Some("grid") => grid::run(&args),
         Some("plan") => plan::run(&args),
+        Some("infill") => infill::run(&args),
         Some("reduce") => reduce::run(&args),
         Some("simulate") => simulate::run(&args),
         Some(other) => {
diff --git a/src/planning/clip.rs b/src/planning/clip.rs
new file mode 100644
index 0000000..6bb4e8a
--- /dev/null
+++ b/src/planning/clip.rs
@@ -0,0 +1,151 @@
+//! Clipping a straight run line to the empty cells of a campaign.
+//!
+//! A line that crosses a hole and then a strip of good data and then another
