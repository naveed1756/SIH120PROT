# Assets

All numbers come from our own models of a **synthetic** test well (BGW-SYN-01), set up from
OIL's published field figures and the literature. Nothing here is field data. Every figure
carries this line in the bottom-left corner:

> Synthetic test well (BGW-SYN-01) based on OIL's published parameters (July 2025) and literature. Not field data. Prototype.

Each figure is made by a script in `figures/` (see DEVINSTRUCT.md §2 for the list).

| File | What it shows | Key numbers | Suggested slide |
|---|---|---|---|
| `A4_dashboard.png` (3840 × 2160) | One screen with the whole well, from reservoir heat to the pumping unit, and an AI recommendation that stops rod float before it happens. | On day 124.6 of pumping the rods have almost no margin left; rod float is forecast in about 14 hours at 6.9 strokes/min. Advice: slow to 1.1 strokes/min over 6 hours. Tubing viscosity 3.1 Pa·s, 58 °C at the surface, 25 % water. | Proposed solution (full-width) |
| `A1_coupling.png` + `A1_coupling_notes.md` | As the steam heat fades, the oil in the tubing thickens and the rods start to float. The twin sees it coming and the AI speed plan prevents it. | Rod float starts on day 125 (quick estimate) or day 121 (full rod simulation); we show both. With the AI speed plan, a 6 kW heater, or a hydraulic unit with a slower downstroke: no rod float in the 150-day cycle. | Impact and benefits (main figure) |
| `A2_thermal_cycle.mp4` | Temperature around the well through one steam cycle: the hot zone grows during steaming (wider at the top, because steam rises), spreads during the soak and cools while pumping. | 712 frames, one every 6 hours. Hot-zone radius at the end of steaming: 18.6 / 15.5 / 13.5 m (top / middle / bottom layer). Heat balance closes to within 1e-13. | Technical approach (thumbnail or video) |
| `A2_end_injection.png`, `A2_end_soak.png`, `A2_day60.png` | Stills of the same picture at three moments of the cycle. | 3.1 t/h of steam for 18 days, about 1.6 MW of heat reaching the sand face. | Technical approach |
| `A3_card_library.png` | We have no failure records, so we simulate them: nine pump problems from a model of the rod string. | 13,104 simulated pump cards (9 problems × 1,500, 92–100 % usable per problem), with 2–5 % sensor noise on the surface cards. | Technical approach |
| `A6a_marx_langenheim.png` | Our reservoir simulator matches the textbook formula for the heated area. | 275 / 402 m² from our simulator vs 276 / 403 m² from the formula after 14 / 21 days (within 1 %). | Feasibility |
| `A5_confusion.png`, `A5_f1_bars.png` | The AI learns pump problems from simulated cards and is tested on thicker oil and deeper pumps than it was trained on. | 82 % of unseen cards named correctly (average score 0.80 over 5,917 cards). Hardest pair: "normal" vs "tagging", which look alike. | Feasibility |
| `A6b_gibbs_roundtrip.png` | We can see the pump from the surface: the pump card is worked out from the surface card. | Error 0.6 % (normal pump) and 3.7 % (pump 60 % full) of the load range; 1.9 % with thick oil. | Feasibility |
| `A7_sectional_speed.png` | Same pump speed, no rod float: slowing only the downstroke of a hydraulic unit keeps the rods attached. | Day 135, 4.5 strokes/min: downstroke 50 → 56 % of each stroke, top downstroke speed 0.78 → 0.65 m/s, lowest load −0.8 → +4.5 kN. | Impact and benefits |
| `S2_tubing_profiles.png` | The tubing, not the reservoir, decides how thick the fluid around the rods is. | Surface temperature falls from 189 to 64 °C between day 5 and day 100; viscosity at the top rises from 0.0007 to 8 Pa·s. | Technical approach (backup) |
| `A8_vit_quality.png` | Better tubing insulation gets more steam down to the oil. Our model agrees with an earlier design study. | Steam quality at the sand face for grades E / D / C / B: 0.59 / 0.51 / 0.34 / 0.23 (design study 0.61 / 0.54 / 0.37 / 0.25). Plain tubing loses all its steam by 779 m. | Technical approach (backup) |
| `A9_pareto.png` | The twin can search for a better steam plan: the best trade-offs between oil per day and steam used, with OIL's current practice for comparison. | Same oil per day with 5 % less steam per barrel, or 10 % more oil per day for the same steam per barrel. The steam-oil ratios are low because of the demo permeability; read the shape, not the values. | Impact and benefits (optional) |
| `S1_viscosity.png` | Baghewala crude gets far thinner as it heats up. Only the 50 °C point is measured by OIL. | 11.7 / 0.30 / 0.011 Pa·s at 50 / 100 / 200 °C. | Feasibility (small) or backup |

## Also available

The dashboard has a 75-second **demo tour** (the "Demo tour" button, or `?tour=1` in the URL).
No video of it is recorded yet; screen-record `npm run preview` with `?tour=1&present=1`.

## How A4 was made

In `web/`: `npm run build`, `npm run preview`, then `node scripts/screenshot.mjs`. This opens
`http://localhost:4173/?present=1&shot=1` in headless Chromium at 1920 × 1080 with device scale 2
and waits for the 3D scene to draw. `present=1` hides the cursor; `shot=1` freezes the pump at the
same point of the stroke every time so the image is repeatable.

## Questions a reviewer may ask

- **No natural-flow phase.** In the field the well may flow on its own for a while after the soak.
  This prototype goes straight to pumping (marked on the dashboard timeline and on A1).
- **Permeability is a demo value.** 6,600 mD is set so the unheated well makes 18 bbl/day. Pumped
  output then averages 52 bbl/day, above the field's roughly 26 bbl/day.
- **Rod float starts late.** Around day 121–125 rather than mid-cycle, because at these rates the
  tubing stays warm for most of the cycle.
- **Current practice** means running at the peak-inflow speed all cycle with a full pump.
