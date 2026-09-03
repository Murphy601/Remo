`plan` covers a blank block.

`plumbline infill <surface.asc> --config survey.toml`. `--config` is required. Fail on a raster with no depths, negative `--min-area` / `--merge-gap` / `--min-length`, or non-positive `--speed`.

Border holes stay off the list; `--include-edge` brings them in. `--min-area` defaults to four cells. `--merge-gap` is metres, default two cell sizes: hole boxes closer than that become one job.

Course follows the empty cells, clockwise from grid north, in [0, 180). `--heading` wraps the same way. Spacing is `--spacing`, or `plan`'s swath/overlap using `--depth` when given, otherwise the shoalest filled neighbour. `--swath` defaults to `cleaning.max_swath_angle` or 60; `--overlap` is 0.2. Clip to empty cells, split on filled ones. `--min-length` defaults to two cells. Flip successive lines. `--crosslines` writes `{out}.crosslines` beside `--out`.

`--max-lines` caps the count; 0 is illegal. `--speed` defaults to 3. `--out` matches `plan`: `# line start_east start_north end_east end_north`, two decimals.

`--json` keys: survey, holidays, skipped, area_m2, heading_deg, spacing_m, shoalest_m, lines, length_m, hours, remainder_interior, remainder_area_m2. Remainder paints half-width spacing/(2*(1-overlap)) around each line, then recounts interior holes and area. Printed shoalest follows `--depth` if set.

Print `infill of <survey.name>:` then `N holidays, A m², K skipped`; `heading H degrees, spacing S m from shoalest D m`; `L lines, X m on line, T hours at V m/s`; `remainder: R interior holidays, B m²`. Metres and degrees whole; spacing, shoalest, length one decimal; hours two. Empty: skip heading, print `0 lines`.

IMPORTANT: Please work on this in a new branch from main and commit everything when you are done.
