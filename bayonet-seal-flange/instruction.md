HELIOS-M34 bayonet — receiver + window cap
ICD-H34-09  rev C2   (C2 is the released one. A and B had the lock going the other way. Do not use those.)

I need both halves, not a look-alike of one part. These have to assemble on the bench. Binary STL, millimetres, one solid per file:

  /app/female.stl     receiver. Stays on the vessel.
  /app/male.stl       window cap. The bit you twist on.

OpenSCAD is already on the box if you want it. Use something else if you prefer. I do not want STEP, ASCII STL, or a zip.

Frame
-----
Axis on the origin. +Z is the insertion direction, into the vessel. Female lives at z >= 0. Her sealing face is the z = 0 plane. Male comes in from z < 0 and is seated when his z = 0 face is against hers.

+X is the key-lug centre at the INSERT pose (before you twist). Looking along +Z, lock is CCW. I know that is the other way from a Nikon F. Do not write me about it. We scrapped a batch last year when a vendor mirrored the lugs.

Female — receiver
-----------------
Overall:
  z = 0 to 10     flange, Ø72
  z = 10 to 12    tube seat / back wall, Ø50. This is a real step. The Ø72 does not run through.

Bores (female):
  z = 0 to 10     barrel clearance Ø48.30
  z = 10 to 12    optical only, Ø34.00   (the back wall closes down)
  z = 5.40 to 10  lug race, Ø56.40. This is a counterbore on the barrel hole. Male's lugs live here after they pass the lip.

Retainer lip:
  z = 3.00 to 5.40
  material from r = 24.15 out to the race wall, except three windows:
    key window   centred on +X (0°), 46° wide
    two regulars centred at 120° and 240°, 34° wide each
  Windows cut the lip out to the race diameter so the lugs can pass. They do not cut the flange OD.

O-ring gland (HX-7, 1.78 cord — we already did the crush math, do not reinvent it):
  rectangular groove in the z = 0 face, into +Z
  ID 50.00   OD 54.20   depth 1.40
  That sits in the flange meat outside the barrel hole. Male just needs a flat land over that annulus. Groove is on the female.

Bolt circle:
  4 × M3 clear, Ø3.40 through the 10 mm flange
  BCD 58.00, at 45° / 135° / 225° / 315°
  Spotface Ø6.00 × 0.8 deep on the vessel-side shoulder (into the flange from z = 10 toward z = 9.2). Not on the seal face — I do not want a washer on the O-ring land. Holes sit at r = 29 so they miss the Ø50 tube seat.

Hard stop in the race:
  a block so you cannot twist past lock
  72° to 80° (absolute, same frame as above)
  z = 5.60 to 8.00
  r = 24.20 to 28.20
  The key lug's leading face comes up against this at lock. Leave a couple of degrees of air. Do not omit it — we had caps walk past lock in rev A.

Male — window cap
-----------------
Cap:   Ø64, z = -8 to 0
Barrel: Ø48.00, z = 0 to 9.50. Stop short of the female back wall. If you run the barrel to z = 12 you will hit her.
Through bore Ø34.00
Optic pocket on the -Z face of the cap: Ø36.50 × 2.20 deep (z = -8.00 to -5.80). The step down to Ø34 is the retention lip for a 2 mm window. Do not bore 36.5 all the way through.

Lugs, sitting in the race when seated:
  z = 5.60 to 8.00
  r = 24.00 to 27.60
  key lug     38° wide, centred on +X at INSERT
  two regulars 26° wide, centred at 120° and 240° at INSERT

Three identical lugs will go in in three poses. That fails. The fat lug is the clock.

Assembly
--------
1. Line up the key lug with the fat window (+X).
2. Push +Z. Lugs have to clear the lip windows. The fat lug will not go through a 34° window — that is on purpose.
3. When the z = 0 faces meet, twist 50° CCW looking along +Z. Lugs park in the race, behind the lip. You should not be able to pull -Z without twisting back.
4. Stop block kills further CCW.

Clearances I already put in the numbers (0.15 mm on the barrel, etc.). Do not add your own "just in case" slop on the lug span or the window widths. Off by a few degrees and either it will not insert or it will not lock.

Break edges 0.2 max if you want. I am not grading fillets. I am grading whether the pair mates, clocks, seals, and stops.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
