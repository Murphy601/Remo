Leftover work after delivery is the holes in the surface. `plan` covers a blank block.

`plumbline infill <surface.asc> --config survey.toml`. `--config` is required. Fail if the raster has no depths, or `--min-area` / `--merge-gap` / `--min-length` below zero.

Border holes stay off the list; `--include-edge` brings them in. `--min-area` defaults to four cells. `--merge-gap` is metres, default two cell sizes: hole boxes closer than that become one job.

Course follows the empty cells, clockwise from grid north, in [0, 180). `--heading` if already known. Spacing is `--spacing` or `plan`'s swath/overlap from the shoalest filled neighbour (`--swath` from `cleaning.max_swath_angle` or 60, `--overlap` 0.2). Clip to empty cells, split on filled ones. `--min-length` defaults to two cells. Flip successive lines, matching `plan`. `--crosslines` writes `{out}.crosslines` beside `--out`.

`--max-lines` caps the count; 0 is illegal. `--speed` (3) is for hours. `--out` matches `plan`: `# line start_east start_north end_east end_north`, two decimals.

`--json` keys: survey, holidays, skipped, area_m2, heading_deg, spacing_m, shoalest_m, lines, length_m, hours, remainder_interior, remainder_area_m2. Remainder: paint half-width spacing/(2*(1-overlap)) around each line, then recount interior holes.

Print `infill of <survey.name>:` then `N holidays, A m², K skipped`; `heading H degrees, spacing S m from shoalest D m`; `L lines, X m on line, T hours at V m/s`; `remainder: R interior holidays, B m²`. Whole metres and degrees; one decimal on spacing, shoalest, length; two on hours. Empty: skip heading, print `0 lines`.

IMPORTANT: Please work on this in a new branch from main and commit everything when you are done.
