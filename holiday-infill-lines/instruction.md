After a block has been surveyed, the only water worth going back to is the interior holidays on the delivered grid. Add `plumbline infill <surface.asc> --config survey.toml` for those holes.

Ignore gaps that touch the grid edge unless `--include-edge` is set. Skip holidays smaller than `--min-area` (default four cells). Nearby holes whose bounding boxes sit within `--merge-gap` metres (default two cell sizes) are planned as one group.

Heading defaults to the long axis of the group's empty cells, clockwise from grid north in [0, 180); `--heading` overrides it. Spacing is `--spacing`, or plan's swath/overlap rule from the shoalest populated neighbour (`--swath` from cleaning.max_swath_angle or 60, `--overlap` 0.2). Clip candidates to empty cells and split where good coverage crosses them. Drop pieces shorter than `--min-length` (default two cells). Alternate directions like `plan`. `--crosslines` writes a sparse set across the main heading to `{out}.crosslines` when `--out` is set.

`--max-lines` refuses a plan over that cap, including 0. `--speed` (default 3) is for the hour estimate. `--out` writes the same `# line start_east start_north end_east end_north` file as `plan`, two decimal places. `--json` keys: survey, holidays, skipped, area_m2, heading_deg, spacing_m, shoalest_m, lines, length_m, hours, remainder_interior, remainder_area_m2. Remainder paints a swath of half-width spacing/(2*(1-overlap)) around every infill line and recounts interior holidays.

Stdout: `infill of <survey.name>:` then `N holidays, A m², K skipped`; `heading H degrees, spacing S m from shoalest D m`; `L lines, X m on line, T hours at V m/s`; `remainder: R interior holidays, B m²`. Area whole metres, heading whole degrees, spacing/shoalest/length one decimal, hours two. Zero holidays prints `0 lines` instead of the heading line. Negative min-area, merge-gap or min-length is refused. No soundings is refused. `--config` is required.

IMPORTANT: Please work on this in a new branch from main and commit everything when you are done.
