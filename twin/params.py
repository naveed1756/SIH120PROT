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
K_MD = 500.0                 # P-05 Layer1 (<1,000 mD). NOTE: overwritten by DEMO tuning in T04
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
T_PROD_D = 120.0             # Assumed production window for the PoC cycle (T09 knob 1)

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
PLUNGER_D_M = None           # set in T09 so N_inflow is 5-6 SPM at the production peak
STROKE_M = 3.0               # Assumed beam-unit stroke length
