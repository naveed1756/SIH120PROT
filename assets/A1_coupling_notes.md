# Notes on A1 (steam heat to rod float)

Synthetic test well (BGW-SYN-01) based on OIL's published parameters (July 2025) and literature. Not field data. Prototype.

## Settings used
- Pumping period: 150 days (raised from 120, because rod float only starts around day 125).
- Water share of the produced liquid: starts at 85 %, settles at 25 %,
  halfway there in about 14 days.
- The oil and water mix turns thick when the water share drops below 60 %
  (day 10.8 of pumping). Changing this point between 50 and 80 % did not move the rod float date.
- Reservoir permeability is set to 6,600 mD so that the unheated well makes about 18 bbl/day.
  This is a demo setting, not a Baghewala estimate.
- We aimed for rod float to start between day 30 and day 80. With these settings it starts later
  (around day 125), because the well produces enough liquid to keep the tubing warm for most of the cycle.

## Pump
- Plunger 2.25" (the largest standard size), 3 m stroke.
- Current practice: a fixed 6.9 strokes/min, which matches the inflow at peak production.
  The fastest downstroke speed is then 1.08 m/s.

## When rod float starts (days of pumping)
| Case | Start of rod float |
|---|---|
| Current practice, quick estimate (fall speed of the rods) | day 125.2 |
| Current practice, full rod simulation (surface load drops below zero) | day 121.2 |
| With a 6 kW downhole heater | no rod float in the cycle |
| Hydraulic unit, 6 m stroke, slower downstroke (3.4 strokes/min) | no rod float in the cycle |
| AI speed plan | no rod float (lowest margin 0.76) |

The two estimates for current practice differ by about 4 days. We show both.
The quick estimate treats the rods as one rigid piece. The full simulation also includes the rods
stretching and the fluid load at the pump, and the extra bounce on the downstroke makes the rods
float a few days sooner.

The dashboard's "now" is day 124.6, 14 hours before the quick estimate says rod float begins.

## Rod simulation check (current practice)
| Day | Tubing viscosity (Pa·s) | Lowest surface load (kN) | Load range (kN) | Rods floating? |
|---|---|---|---|---|
| 95.2 | 1.69 | +7.74 | 67.1 | no |
| 125.2 | 3.17 | -1.75 | 86.2 | yes |
| 140.2 | 4.12 | -8.72 | 100.1 | yes |

## About the top strip
The top strip shows how far out the oil is still above 70 °C in each layer (end of pumping:
layer 1 13.6 m, layer 2 13.0 m, layer 3 10.7 m). The edge of the "warm by 5 °C" zone keeps
creeping outward as heat spreads, so it would not show the hot zone shrinking.
