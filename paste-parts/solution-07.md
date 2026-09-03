--- a/src/planning/mod.rs
+++ b/src/planning/mod.rs
@@ -1,7 +1,12 @@
 //! Planning the lines before anything gets wet.
 
 pub mod block;
+pub mod clip;
+pub mod heading;
+pub mod holes;
+pub mod infill;
 pub mod lines;
 
 pub use block::Block;
+pub use infill::{plan_infill, InfillOptions, InfillResult};
 pub use lines::{plan_crosslines, plan_lines, spacing_for, Plan, PlannedLine};


