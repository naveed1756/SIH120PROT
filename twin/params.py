"""BGW-SYN-01 parameter card: the ONE source of numbers for every module.

Synthetic reference well built on OIL's published field-level figures (Jul 2025
deck) plus literature priors. Not a Baghewala well; not field data.

Each constant carries its registry ID from Layer 3A section 14 (P-xx) and an
evidence label:
  OIL        measured/reported by Oil India
  Layer1     earlier project research from public sources, unconfirmed
  Literature published correlation / typical value from other fields (a prior)
  Assumed    placeholder chosen to make the prototype run
  Derived    computed from the values above
  DEMO       tuned knob for the PoC demo (see PROGRESS.md), not a prediction
Units are SI unless the name says otherwise (_M, _C, _KSC, _D, _MD, ...).
"""

# ---------------------------------------------------------------- unit helpers
G = 9.80665                  # m/s2
KSC_PA = 98_066.5            # 1 ksc (kgf/cm2) in Pa, gauge unless noted
ATM_PA = 101_325.0           # used to convert gauge -> absolute
BBL_M3 = 0.158987            # 1 bbl in m3
CP_PAS = 1e-3                # 1 cP in Pa.s
MD_M2 = 9.869233e-16         # 1 mD in m2
IN_M = 0.0254                # 1 inch in m
DAY_S = 86_400.0
HOUR_S = 3_600.0

# ------------------------------------------------------------------ reservoir
TOP_PAY_M = 1150.0           # P-01 OIL (field level ~1,150 m)
H_LAYERS_M = [4.0, 3.0, 3.0] # P-02 Layer1 (10 m total, range 5-23) / P-03 Assumed split; top -> bottom
KH_CONTRAST = [1.0, 0.6, 1.4]  # P-03 Assumed (kh multipliers, top -> bottom)
PHI = 0.19                   # P-04 Layer1 (18-20 %)
K_MD_LAYER1 = 500.0          # P-05 Layer1 (<1,000 mD); gives a cold rate of only ~1.4 bbl/d (3A FC-1)
K_MD = 6600.0                # DEMO: tuned to OIL field-level figures (FC-1), not a Baghewala prediction.
                             # Effective kh: cold rate 18 bbl/d. EXCEEDS the CLAUDE.md 8 guard of 5,000 mD;
                             # lumps residual heat / heaters / diluent / shear-thinning (3A FC-1). See PROGRESS.md
T_R_C = 50.0                 # P-06 OIL
P_INIT_KSC = 116.0           # P-07 OIL (initial reservoir pressure)
P_NEARWELL_KSC = 75.0        # P-08 Assumed (depleted near-well pressure, to calibrate)
RW_M = 0.108                 # Assumed (8 1/2" hole)
RE_M = 150.0                 # P-18 Assumed (drainage radius / grid outer edge)
M_R = 2.4e6                  # P-11 Literature, reservoir volumetric heat capacity (J/m3K, incl. pore fluid)
LAM_R = 2.5                  # P-11 Literature, reservoir conductivity (W/mK)
M_OB = 2.3e6                 # P-12 Literature, cap/base volumetric heat capacity (J/m3K)
LAM_OB = 1.7                 # P-12 Literature, cap/base conductivity (W/mK)
BETA_OVERRIDE = 2.0          # P-13 Assumed closure (prior U(0,4)); makes override visible
S_OI = 0.75                  # P-09 Assumed initial oil saturation (pore-fluid conductivity mix)
LAM_W = 0.64                 # Literature, liquid water conductivity near 50 C (W/mK, IAPWS)
RHO_W = 988.0                # Derived, liquid water density at 50 C (kg/m3, IAPWS) - heat-carrier mass

# ------------------------------------------- thermal grid numerics (T03, 3A 5.1)
NR_EDGES = 40                # radial cell edges, geometric RW -> RE (39 cells, ratio ~1.20)
N_CAP = 12                   # cap (and base) cells, geometric from the pay outward
CAP_DZ0_M = 0.25             # first cap/base cell thickness next to the pay
CAP_EXTENT_M = 60.0          # cap/base total thickness
PAY_DZ_M = 1.0               # pay cell thickness (layers 4/3/3 -> 10 cells)
DT_S = 3600.0                # nominal step
DT_FINE_S = 300.0            # step for the first FINE_WINDOW_S after each phase change
FINE_WINDOW_S = 6 * 3600.0
SNAP_EVERY_S = 6 * 3600.0    # T[t,z,r] snapshot interval (animation frames)
ML_T_S_C = 303.0             # Marx-Langenheim check: steam T (dT = 253 K, 3A 5.6 worked example)

# ---------------------------------------------------------------------- fluid
API = 16.0                   # P-19 OIL (14-17 deg API)
SG = 0.959                   # P-19 Derived from API 16
RHO15 = 959.0                # P-19 Derived, kg/m3 at 15 C
WALTHER_A = 9.049            # P-20 OIL anchor: ~11,500 cP at 50 C, 50 1/s (range 10,000-13,000)
WALTHER_B = 3.362            # P-21 Assumed via 300 cP at 100 C (placeholder slope)
T_PP_C = 24.0                # P-22 Layer1 (pour point 21-27 C)
T_NN_C = 70.0                # P-23 Literature band 57-85 C (Newtonian transition)
TAU0_PA = 0.1                # P-23 Assumed (cut to 0.1 Pa to satisfy FC-1)
N0_HB = 0.7                  # P-23 Assumed (flow index at the pour point)
A_HB = 1.5                   # P-23 Assumed (yield-stress exponent)
B_HB = 1.0                   # P-23 Assumed (flow-index exponent)
GDOT_REF = 50.0              # 1/s, OIL's viscosity measurement shear rate (anchor, 3A B.4)
M_PAPANASTASIOU = 1.0e3      # s, regularisation constant (3A B.5, numerical device)
F_INV = 0.60                 # P-24 Assumed, inversion water fraction (emulsion)
F_INV_W = 0.05               # P-24 Assumed, inversion transition width
PHI100 = 0.75                # P-24 Assumed, Pal-Rhodes dispersed fraction at which mu_r = 100
PAL_RHODES_CAP = 1.1         # numerical cap on phi/PHI100 (brief T02)
P_WATER_VISC_PA = 1.0e6      # pressure for water viscosity when none is given (brief T02)

# ------------------------------------------------------------- steam / cycle
STEAM_KGS = 3100.0 / 3600.0  # P-34 OIL (~3.1 t/h)
P_SURF_KSC = 91.0            # P-35 OIL operating range 85-97 ksc(g), mid value
X_SURF = 0.65                # P-36 OIL (0.60-0.70)
X_SF = 0.50                  # Derived: sandface quality for VIT grade D (3B Fig. 3 ~0.51-0.54)
P_BH_INJ_KSC = 99.0          # Derived: bottomhole injection pressure (3A section 9, 3B section 2)
T_INJ_D = 18.0               # P-37 OIL (14-21 d), mid value
SOAK_RATIO = 0.55            # P-37 OIL (0.5-0.6 of injection time)
T_PROD_D = 150.0             # T09 knob 1: 120 -> 150 d so rod-float onset (~day 125) falls inside the cycle

# --------------------------------------------------------------- inflow (T04)
P_WF_KSC = 10.0              # Assumed pump-intake / bottomhole flowing pressure for the cold IPR
FW0 = 0.85                   # Assumed, initial water cut of the condensate-return curve (3A 7.3 fallback)
FW_INF = 0.25                # Assumed, late water cut
TAU_W_D = 20.0               # Assumed, water-cut decay time (days)
R_H_DT_K = 5.0               # 3A 5.4 definition of heated radius: T - T_R >= 5 K

# ------------------------------------------------------------ wellbore (T05)
T_SURF_GEO_C = 30.0          # P-31 Assumed surface geothermal temperature
LR_PER_M3D_VIT_D = 72.0      # Derived from 3B section 4.5 table (5 m3/d -> 360 m), metres per m3/d
LR_PER_M3D_BARE = 27.0       # Derived from 3B section 4.5 table (10 m3/d -> 270 m)
HEATER_DT_PER_KW_AT_5M3D = 10.0  # 3B section 4.5 rule of thumb: ~10 C per kW at 5 m3/d

# ---------------------------------------------------------- rods & pump (T06)
ROD_R_M = 0.0111             # 3B section 6 Assumed (7/8" rod)
TUB_RI_M = 0.038             # 3B section 6 Assumed (3 1/2" tubing, ID 76 mm)
ROD_LEN_M = 1100.0           # Assumed pump setting depth
E_STEEL = 2.07e11            # Literature, Pa
RHO_STEEL = 7850.0           # Literature, kg/m3
K_C_DRAG = 1.5               # Assumed coupling/guide drag multiplier
PLUNGER_D_M = 2.25 * IN_M     # T09: largest standard plunger; N_inflow at the production peak = 6.9 SPM (closest to the 5-6 band)
STROKE_M = 3.0               # Assumed beam-unit stroke length
PLUNGER_SIZES_IN = [1.25, 1.5, 1.75, 2.0, 2.25]  # standard API plunger sizes (brief T09)
T06_TEST_PLUNGER_IN = 1.75   # Assumed plunger for the T06 checks and the A1 cross-check until T09 sizes it
RHO_FLUID_ROD = 950.0        # Assumed oil/water mixture density around the rods (kg/m3) -> 26.2 N/m buoyant rod weight
P_THP_KSC = 5.0              # Assumed tubing-head pressure (ksc g) added to the fluid column for p_dis
DX_ROD_M = 10.0              # rod-string grid spacing (brief T06)
DT_ROD_S = 1.5e-3            # rod-string time step (brief T06); a*dt/dx = 0.77
N_STROKES_SIM = 3            # simulate 3 strokes, keep the 3rd
RAMP_FRAC = 0.03             # fluid-load transfer over 3 % of plunger stroke (brief T07)
POUND_DROP_FRAC = 0.01       # fluid-pound load release over 1 % of plunger stroke
GAS_N = 1.2                  # polytropic exponent, steam/gas interference
TAG_FRAC = -0.3              # plunger-tagging impulse, fraction of F_fl (compression)
TAG_S = 0.03                 # tagging impulse duration (s)
HYST_FRAC = 0.005            # plunger reversal detection hysteresis, fraction of S_p
MIN_DWELL_FRAC = 0.3         # no new reversal before 30 % of the half-stroke has elapsed (stops ringing chatter)
HYD_ACCEL = 0.5              # hydraulic unit acceleration (m/s2)
CARD_POINTS = 200            # points per resampled card
