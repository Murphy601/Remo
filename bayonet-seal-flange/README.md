# bayonet-seal-flange

Hardware / CAD. Two-part Helios-M34 bayonet (receiver + window cap).

## Maintainer notes

`solution/build_pair.py` is an implicit solid, not a GUI CAD file. `female_solid` / `male_solid` are point-in-metal predicates. A 0.25 mm voxel grid is filled and only the solid/empty faces are written as binary STL. The male is modelled in the insert pose; lock is a +47° CCW rotation applied by the verifier. The grader also accepts ASCII STL (typical CLI CAD export). The agent image has a headless STL exporter on PATH (`xvfb-run` + `xauth`) so a real CAD path works without a display.

Windows are cut from the seal face (z=0 to 5.40). The 1.10 mm pull-in is extra lip height after each window's CCW edge (`_ramp_extra`), not a helix on the male.

Gland probes in the grader sit near 160°, not on a window centreline. Volume bands (16500–22500, 27000–34000) allow 0.2 mm edge breaks or a smoother CAD mesh. Probe points sit ≥0.4 mm inside or outside a face so tessellation should not flip them.

Regenerate locally:

`python3 solution/build_pair.py --outdir /tmp/helios`

Then copy the two STLs to `/app` and run `tests/test_outputs.py`.
