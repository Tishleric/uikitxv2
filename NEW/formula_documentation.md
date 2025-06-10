# Actant PnL Excel Formula Documentation

Generated: 2025-06-10 12:39:35

Source file: actantpnl.xlsx

## Overview

This document maps Excel formulas used in PnL calculations.

## Formula Analysis Summary

### Section Summary

**Input Data**
- Total cells: 420
- Formula cells: 0
- Unique formulas: 0

**Call Analysis**
- Total cells: 312
- Formula cells: 250
- Unique formulas: 248

**Put Analysis**
- Total cells: 312
- Formula cells: 225
- Unique formulas: 223

### Common Excel Functions

| Function | Count |
|----------|-------|

## Detailed Formula Mappings

### Input Data

| Cell | Value/Formula | Type | Dependencies |
|------|---------------|------|--------------|
| AA1 | 2.5 | Value | - |
| AB1 | 2.75 | Value | - |
| AC1 | 3 | Value | - |
| B1 | Expiration | Value | - |
| C1 | Value | Value | - |
| D1 | UPrice | Value | - |
| E1 | -3 | Value | - |
| F1 | -2.75 | Value | - |
| G1 | -2.5 | Value | - |
| H1 | -2.25 | Value | - |
| I1 | -2 | Value | - |
| J1 | -1.75 | Value | - |
| K1 | -1.5 | Value | - |
| L1 | -1.25 | Value | - |
| M1 | -1 | Value | - |
| N1 | -0.75 | Value | - |
| O1 | -0.5 | Value | - |
| P1 | -0.25 | Value | - |
| Q1 | 0 | Value | - |
| R1 | 0.25 | Value | - |
| S1 | 0.5 | Value | - |
| T1 | 0.75 | Value | - |
| U1 | 1 | Value | - |
| V1 | 1.25 | Value | - |
| W1 | 1.5 | Value | - |
| X1 | 1.75 | Value | - |
| Y1 | 2 | Value | - |
| Z1 | 2.25 | Value | - |
| AA2 | 0.99912 | Value | - |
| AB2 | 0.99942 | Value | - |
| AC2 | 0.99962 | Value | - |
| B2 | XCME.ZN | Value | - |
| C2 | ab_sDeltaPathCallPct | Value | - |
| D2 | 110.383 | Value | - |
| E2 | 0.00145 | Value | - |
| F2 | 0.00228 | Value | - |
| G2 | 0.0036 | Value | - |
| H2 | 0.00578 | Value | - |
| I2 | 0.00975 | Value | - |
| J2 | 0.01889 | Value | - |
| K2 | 0.04029 | Value | - |
| L2 | 0.08909 | Value | - |
| M2 | 0.17909 | Value | - |
| N2 | 0.30322 | Value | - |
| O2 | 0.43917 | Value | - |
| P2 | 0.56999 | Value | - |
| Q2 | 0.70499 | Value | - |
| R2 | 0.82615 | Value | - |
| S2 | 0.91288 | Value | - |
| T2 | 0.96004 | Value | - |
| U2 | 0.98114 | Value | - |
| V2 | 0.99037 | Value | - |
| W2 | 0.99451 | Value | - |
| X2 | 0.99667 | Value | - |
| Y2 | 0.99791 | Value | - |
| Z2 | 0.99865 | Value | - |
| AA3 | -0.00088 | Value | - |
| AB3 | -0.00058 | Value | - |
| AC3 | -0.00038 | Value | - |
| B3 | XCME.ZN | Value | - |
| C3 | ab_sDeltaPathPutPct | Value | - |
| D3 | 110.383 | Value | - |
| E3 | -0.99855 | Value | - |
| F3 | -0.99772 | Value | - |
| G3 | -0.9964 | Value | - |
| H3 | -0.99422 | Value | - |
| I3 | -0.99025 | Value | - |
| J3 | -0.98111 | Value | - |
| K3 | -0.95971 | Value | - |
| L3 | -0.91091 | Value | - |
| M3 | -0.82091 | Value | - |
| N3 | -0.69678 | Value | - |
| O3 | -0.56083 | Value | - |
| P3 | -0.43001 | Value | - |
| Q3 | -0.29501 | Value | - |
| R3 | -0.17385 | Value | - |
| S3 | -0.08712 | Value | - |
| T3 | -0.03996 | Value | - |
| U3 | -0.01886 | Value | - |
| V3 | -0.00963 | Value | - |
| W3 | -0.00549 | Value | - |
| X3 | -0.00333 | Value | - |
| Y3 | -0.00209 | Value | - |
| Z3 | -0.00135 | Value | - |
| AA4 | 62.95847 | Value | - |
| AB4 | 62.97735 | Value | - |
| AC4 | 62.98984 | Value | - |
| B4 | XCME.ZN | Value | - |
| C4 | ab_sDeltaPathDV01Call | Value | - |
| D4 | 110.383 | Value | - |
| E4 | 0.09143 | Value | - |
| F4 | 0.14382 | Value | - |
| G4 | 0.22679 | Value | - |
| H4 | 0.36427 | Value | - |
| I4 | 0.61457 | Value | - |
| J4 | 1.1906 | Value | - |
| K4 | 2.53865 | Value | - |
| L4 | 5.61412 | Value | - |
| M4 | 11.28538 | Value | - |
| N4 | 19.10716 | Value | - |
| O4 | 27.67362 | Value | - |
| P4 | 35.91731 | Value | - |
| Q4 | 44.42395 | Value | - |
| R4 | 52.05891 | Value | - |
| S4 | 57.52441 | Value | - |
| T4 | 60.49583 | Value | - |
| U4 | 61.82548 | Value | - |
| V4 | 62.40716 | Value | - |
| W4 | 62.66797 | Value | - |
| X4 | 62.80429 | Value | - |
| Y4 | 62.88242 | Value | - |
| Z4 | 62.92924 | Value | - |
| AA5 | -0.05553 | Value | - |
| AB5 | -0.03665 | Value | - |
| AC5 | -0.02416 | Value | - |
| B5 | XCME.ZN | Value | - |
| C5 | ab_sDeltaPathDV01Put | Value | - |
| D5 | 110.383 | Value | - |
| E5 | -62.92257 | Value | - |
| F5 | -62.87018 | Value | - |
| G5 | -62.78721 | Value | - |
| H5 | -62.64973 | Value | - |
| I5 | -62.39943 | Value | - |
| J5 | -61.8234 | Value | - |
| K5 | -60.47535 | Value | - |
| L5 | -57.39988 | Value | - |
| M5 | -51.72862 | Value | - |
| N5 | -43.90684 | Value | - |
| O5 | -35.34038 | Value | - |
| P5 | -27.09669 | Value | - |
| Q5 | -18.59005 | Value | - |
| R5 | -10.95509 | Value | - |
| S5 | -5.48959 | Value | - |
| T5 | -2.51817 | Value | - |
| U5 | -1.18852 | Value | - |
| V5 | -0.60684 | Value | - |
| W5 | -0.34603 | Value | - |
| X5 | -0.20971 | Value | - |
| Y5 | -0.13158 | Value | - |
| Z5 | -0.08476 | Value | - |
| AA6 | 0.02684 | Value | - |
| AB6 | 0.02483 | Value | - |
| AC6 | 0.02356 | Value | - |
| B6 | XCME.ZN | Value | - |
| C6 | ab_sGammaPathDV01 | Value | - |
| D6 | 110.383 | Value | - |
| E6 | 0.03157 | Value | - |
| F6 | 0.03735 | Value | - |
| G6 | 0.04743 | Value | - |
| H6 | 0.06574 | Value | - |
| I6 | 0.11292 | Value | - |
| J6 | 0.23663 | Value | - |
| K6 | 0.52417 | Value | - |
| L6 | 1.12785 | Value | - |
| M6 | 1.76323 | Value | - |
| N6 | 2.15618 | Value | - |
| O6 | 2.14437 | Value | - |
| P6 | 2.14719 | Value | - |
| Q6 | 2.12238 | Value | - |
| R6 | 1.70827 | Value | - |
| S6 | 1.08264 | Value | - |
| T6 | 0.51301 | Value | - |
| U6 | 0.23616 | Value | - |
| V6 | 0.11584 | Value | - |
| W6 | 0.0664 | Value | - |
| X6 | 0.04649 | Value | - |
| Y6 | 0.03597 | Value | - |
| Z6 | 0.03018 | Value | - |
| AA7 | 0.00031 | Value | - |
| AB7 | 6e-05 | Value | - |
| AC7 | 1e-05 | Value | - |
| B7 | XCME.ZN | Value | - |
| C7 | ab_VegaDV01 | Value | - |
| D7 | 110.383 | Value | - |
| E7 | 0.00148 | Value | - |
| F7 | 0.00571 | Value | - |
| G7 | 0.01917 | Value | - |
| H7 | 0.05628 | Value | - |
| I7 | 0.14433 | Value | - |
| J7 | 0.32336 | Value | - |
| K7 | 0.63285 | Value | - |
| L7 | 1.08201 | Value | - |
| M7 | 1.6161 | Value | - |
| N7 | 2.10871 | Value | - |
| O7 | 2.40367 | Value | - |
| P7 | 2.39354 | Value | - |
| Q7 | 2.08216 | Value | - |
| R7 | 1.58234 | Value | - |
| S7 | 1.05049 | Value | - |
| T7 | 0.60925 | Value | - |
| U7 | 0.30868 | Value | - |
| V7 | 0.13662 | Value | - |
| W7 | 0.05283 | Value | - |
| X7 | 0.01784 | Value | - |
| Y7 | 0.00527 | Value | - |
| Z7 | 0.00136 | Value | - |
| AA8 | 0.00326 | Value | - |
| AB8 | 0.00053 | Value | - |
| AC8 | 7e-05 | Value | - |
| B8 | XCME.ZN | Value | - |
| C8 | ab_Theta | Value | - |
| D8 | 110.383 | Value | - |
| E8 | 0.01833 | Value | - |
| F8 | 0.07782 | Value | - |
| G8 | 0.28014 | Value | - |
| H8 | 0.86095 | Value | - |
| I8 | 2.27259 | Value | - |
| J8 | 5.17719 | Value | - |
| K8 | 10.21808 | Value | - |
| L8 | 17.52746 | Value | - |
| M8 | 26.19093 | Value | - |
| N8 | 34.15297 | Value | - |
| O8 | 38.90787 | Value | - |
| P8 | 38.74473 | Value | - |
| Q8 | 33.72451 | Value | - |
| R8 | 25.64423 | Value | - |
| S8 | 17.01514 | Value | - |
| T8 | 9.8336 | Value | - |
| U8 | 4.93842 | Value | - |
| V8 | 2.14815 | Value | - |
| W8 | 0.80624 | Value | - |
| X8 | 0.2598 | Value | - |
| Y8 | 0.07145 | Value | - |
| Z8 | 0.01665 | Value | - |
| AA9 | 112.88281 | Value | - |
| AB9 | 113.13281 | Value | - |
| AC9 | 113.38281 | Value | - |
| B9 | XCME.ZN | Value | - |
| C9 | ab_F | Value | - |
| D9 | 110.383 | Value | - |
| E9 | 107.38281 | Value | - |
| F9 | 107.63281 | Value | - |
| G9 | 107.88281 | Value | - |
| H9 | 108.13281 | Value | - |
| I9 | 108.38281 | Value | - |
| J9 | 108.63281 | Value | - |
| K9 | 108.88281 | Value | - |
| L9 | 109.13281 | Value | - |
| M9 | 109.38281 | Value | - |
| N9 | 109.63281 | Value | - |
| O9 | 109.88281 | Value | - |
| P9 | 110.13281 | Value | - |
| Q9 | 110.38281 | Value | - |
| R9 | 110.63281 | Value | - |
| S9 | 110.88281 | Value | - |
| T9 | 111.13281 | Value | - |
| U9 | 111.38281 | Value | - |
| V9 | 111.63281 | Value | - |
| W9 | 111.88281 | Value | - |
| X9 | 112.13281 | Value | - |
| Y9 | 112.38281 | Value | - |
| Z9 | 112.63281 | Value | - |
| AA10 | 110 | Value | - |
| AB10 | 110 | Value | - |
| AC10 | 110 | Value | - |
| B10 | XCME.ZN | Value | - |
| C10 | ab_K | Value | - |
| D10 | 110.383 | Value | - |
| E10 | 110 | Value | - |
| F10 | 110 | Value | - |
| G10 | 110 | Value | - |
| H10 | 110 | Value | - |
| I10 | 110 | Value | - |
| J10 | 110 | Value | - |
| K10 | 110 | Value | - |
| L10 | 110 | Value | - |
| M10 | 110 | Value | - |
| N10 | 110 | Value | - |
| O10 | 110 | Value | - |
| P10 | 110 | Value | - |
| Q10 | 110 | Value | - |
| R10 | 110 | Value | - |
| S10 | 110 | Value | - |
| T10 | 110 | Value | - |
| U10 | 110 | Value | - |
| V10 | 110 | Value | - |
| W10 | 110 | Value | - |
| X10 | 110 | Value | - |
| Y10 | 110 | Value | - |
| Z10 | 110 | Value | - |
| AA11 | 0 | Value | - |
| AB11 | 0 | Value | - |
| AC11 | 0 | Value | - |
| B11 | XCME.ZN | Value | - |
| C11 | ab_R | Value | - |
| D11 | 110.383 | Value | - |
| E11 | 0 | Value | - |
| F11 | 0 | Value | - |
| G11 | 0 | Value | - |
| H11 | 0 | Value | - |
| I11 | 0 | Value | - |
| J11 | 0 | Value | - |
| K11 | 0 | Value | - |
| L11 | 0 | Value | - |
| M11 | 0 | Value | - |
| N11 | 0 | Value | - |
| O11 | 0 | Value | - |
| P11 | 0 | Value | - |
| Q11 | 0 | Value | - |
| R11 | 0 | Value | - |
| S11 | 0 | Value | - |
| T11 | 0 | Value | - |
| U11 | 0 | Value | - |
| V11 | 0 | Value | - |
| W11 | 0 | Value | - |
| X11 | 0 | Value | - |
| Y11 | 0 | Value | - |
| Z11 | 0 | Value | - |
| AA12 | 3.4375 | Value | - |
| AB12 | 3.4375 | Value | - |
| AC12 | 3.4375 | Value | - |
| B12 | XCME.ZN | Value | - |
| C12 | ab_T | Value | - |
| D12 | 110.383 | Value | - |
| E12 | 3.4375 | Value | - |
| F12 | 3.4375 | Value | - |
| G12 | 3.4375 | Value | - |
| H12 | 3.4375 | Value | - |
| I12 | 3.4375 | Value | - |
| J12 | 3.4375 | Value | - |
| K12 | 3.4375 | Value | - |
| L12 | 3.4375 | Value | - |
| M12 | 3.4375 | Value | - |
| N12 | 3.4375 | Value | - |
| O12 | 3.4375 | Value | - |
| P12 | 3.4375 | Value | - |
| Q12 | 3.4375 | Value | - |
| R12 | 3.4375 | Value | - |
| S12 | 3.4375 | Value | - |
| T12 | 3.4375 | Value | - |
| U12 | 3.4375 | Value | - |
| V12 | 3.4375 | Value | - |
| W12 | 3.4375 | Value | - |
| X12 | 3.4375 | Value | - |
| Y12 | 3.4375 | Value | - |
| Z12 | 3.4375 | Value | - |
| AA13 | 11.78233 | Value | - |
| AB13 | 12.56288 | Value | - |
| AC13 | 13.36212 | Value | - |
| B13 | XCME.ZN | Value | - |
| C13 | ab_Vol | Value | - |
| D13 | 110.383 | Value | - |
| E13 | 11.5777 | Value | - |
| F13 | 10.76767 | Value | - |
| G13 | 9.98839 | Value | - |
| H13 | 9.24295 | Value | - |
| I13 | 8.5356 | Value | - |
| J13 | 7.89891 | Value | - |
| K13 | 7.39238 | Value | - |
| L13 | 7.07501 | Value | - |
| M13 | 6.97317 | Value | - |
| N13 | 7.0053 | Value | - |
| O13 | 7.06886 | Value | - |
| P13 | 7.06887 | Value | - |
| Q13 | 7.00765 | Value | - |
| R13 | 6.97418 | Value | - |
| S13 | 7.05827 | Value | - |
| T13 | 7.32771 | Value | - |
| U13 | 7.7603 | Value | - |
| V13 | 8.30969 | Value | - |
| W13 | 8.93093 | Value | - |
| X13 | 9.5945 | Value | - |
| Y13 | 10.29386 | Value | - |
| Z13 | 11.02458 | Value | - |
| AA14 | 2884.95779 | Value | - |
| AB14 | 3134.77756 | Value | - |
| AC14 | 3384.65859 | Value | - |
| B14 | XCME.ZN | Value | - |
| C14 | ab_sCall | Value | - |
| D14 | 110.383 | Value | - |
| E14 | 3.77366 | Value | - |
| F14 | 4.23275 | Value | - |
| G14 | 4.95476 | Value | - |
| H14 | 6.10331 | Value | - |
| I14 | 7.98427 | Value | - |
| J14 | 11.40434 | Value | - |
| K14 | 18.42741 | Value | - |
| L14 | 33.79875 | Value | - |
| M14 | 66.47711 | Value | - |
| N14 | 126.24534 | Value | - |
| O14 | 219.0641 | Value | - |
| P14 | 345.19411 | Value | - |
| Q14 | 504.59469 | Value | - |
| R14 | 696.53571 | Value | - |
| S14 | 914.74595 | Value | - |
| T14 | 1149.61519 | Value | - |
| U14 | 1392.62322 | Value | - |
| V14 | 1639.21828 | Value | - |
| W14 | 1887.393 | Value | - |
| X14 | 2136.31657 | Value | - |
| Y14 | 2385.6533 | Value | - |
| Z14 | 2635.23172 | Value | - |
| AA15 | 2.14529 | Value | - |
| AB15 | 1.96506 | Value | - |
| AC15 | 1.84609 | Value | - |
| B15 | XCME.ZN | Value | - |
| C15 | ab_sPut | Value | - |
| D15 | 110.383 | Value | - |
| E15 | 2620.96116 | Value | - |
| F15 | 2371.42025 | Value | - |
| G15 | 2122.14226 | Value | - |
| H15 | 1873.29081 | Value | - |
| I15 | 1625.17177 | Value | - |
| J15 | 1378.59184 | Value | - |
| K15 | 1135.61491 | Value | - |
| L15 | 900.98625 | Value | - |
| M15 | 683.66461 | Value | - |
| N15 | 493.43284 | Value | - |
| O15 | 336.2516 | Value | - |
| P15 | 212.38161 | Value | - |
| Q15 | 121.78219 | Value | - |
| R15 | 63.72321 | Value | - |
| S15 | 31.93345 | Value | - |
| T15 | 16.80269 | Value | - |
| U15 | 9.81072 | Value | - |
| V15 | 6.40578 | Value | - |
| W15 | 4.5805 | Value | - |
| X15 | 3.50407 | Value | - |
| Y15 | 2.8408 | Value | - |
| Z15 | 2.41922 | Value | - |

### Call Analysis

| Cell | Value/Formula | Type | Dependencies |
|------|---------------|------|--------------|
| AA18 | 40 | Value | - |
| AB18 | 44 | Value | - |
| AC18 | 48 | Value | - |
| C18 | shift in bp | Value | - |
| E18 | -48 | Value | - |
| F18 | -44 | Value | - |
| G18 | -40 | Value | - |
| H18 | -36 | Value | - |
| I18 | -32 | Value | - |
| J18 | -28 | Value | - |
| K18 | -24 | Value | - |
| L18 | -20 | Value | - |
| M18 | -16 | Value | - |
| N18 | -12 | Value | - |
| O18 | -8 | Value | - |
| P18 | -4 | Value | - |
| Q18 | 0 | Value | - |
| R18 | 4 | Value | - |
| S18 | 8 | Value | - |
| T18 | 12 | Value | - |
| U18 | 16 | Value | - |
| V18 | 20 | Value | - |
| W18 | 24 | Value | - |
| X18 | 28 | Value | - |
| Y18 | 32 | Value | - |
| Z18 | 36 | Value | - |
| AA19 | =AA14 | Formula | AA14 |
| AB19 | =AB14 | Formula | AB14 |
| AC19 | =AC14 | Formula | AC14 |
| C19 | Call Price ACTANT | Value | - |
| E19 | =E14 | Formula | E14 |
| F19 | =F14 | Formula | F14 |
| G19 | =G14 | Formula | G14 |
| H19 | =H14 | Formula | H14 |
| I19 | =I14 | Formula | I14 |
| J19 | =J14 | Formula | J14 |
| K19 | =K14 | Formula | K14 |
| L19 | =L14 | Formula | L14 |
| M19 | =M14 | Formula | M14 |
| N19 | =N14 | Formula | N14 |
| O19 | =O14 | Formula | O14 |
| P19 | =P14 | Formula | P14 |
| Q19 | =Q14 | Formula | Q14 |
| R19 | =R14 | Formula | R14 |
| S19 | =S14 | Formula | S14 |
| T19 | =T14 | Formula | T14 |
| U19 | =U14 | Formula | U14 |
| V19 | =V14 | Formula | V14 |
| W19 | =W14 | Formula | W14 |
| X19 | =X14 | Formula | X14 |
| Y19 | =Y14 | Formula | Y14 |
| Z19 | =Z14 | Formula | Z14 |
| AA20 | =$Q$20+$Q$4*(AA18-$Q$18)+0.5*$Q$6*(AA18-$Q$18)*(AA... | Formula | $Q$20, $Q$4, AA18, $Q$18, $Q$6 |
| AB20 | =$Q$20+$Q$4*(AB18-$Q$18)+0.5*$Q$6*(AB18-$Q$18)*(AB... | Formula | $Q$20, $Q$4, AB18, $Q$18, $Q$6 |
| AC20 | =$Q$20+$Q$4*(AC18-$Q$18)+0.5*$Q$6*(AC18-$Q$18)*(AC... | Formula | $Q$20, $Q$4, AC18, $Q$18, $Q$6 |
| C20 | TS Predicted from 0 | Value | - |
| E20 | =$Q$20+$Q$4*(E18-$Q$18)+0.5*$Q$6*(E18-$Q$18)*(E18-... | Formula | $Q$20, $Q$4, E18, $Q$18, $Q$6 |
| F20 | =$Q$20+$Q$4*(F18-$Q$18)+0.5*$Q$6*(F18-$Q$18)*(F18-... | Formula | $Q$20, $Q$4, F18, $Q$18, $Q$6 |
| G20 | =$Q$20+$Q$4*(G18-$Q$18)+0.5*$Q$6*(G18-$Q$18)*(G18-... | Formula | $Q$20, $Q$4, G18, $Q$18, $Q$6 |
| H20 | =$Q$20+$Q$4*(H18-$Q$18)+0.5*$Q$6*(H18-$Q$18)*(H18-... | Formula | $Q$20, $Q$4, H18, $Q$18, $Q$6 |
| I20 | =$Q$20+$Q$4*(I18-$Q$18)+0.5*$Q$6*(I18-$Q$18)*(I18-... | Formula | $Q$20, $Q$4, I18, $Q$18, $Q$6 |
| J20 | =$Q$20+$Q$4*(J18-$Q$18)+0.5*$Q$6*(J18-$Q$18)*(J18-... | Formula | $Q$20, $Q$4, J18, $Q$18, $Q$6 |
| K20 | =$Q$20+$Q$4*(K18-$Q$18)+0.5*$Q$6*(K18-$Q$18)*(K18-... | Formula | $Q$20, $Q$4, K18, $Q$18, $Q$6 |
| L20 | =$Q$20+$Q$4*(L18-$Q$18)+0.5*$Q$6*(L18-$Q$18)*(L18-... | Formula | $Q$20, $Q$4, L18, $Q$18, $Q$6 |
| M20 | =$Q$20+$Q$4*(M18-$Q$18)+0.5*$Q$6*(M18-$Q$18)*(M18-... | Formula | $Q$20, $Q$4, M18, $Q$18, $Q$6 |
| N20 | =$Q$20+$Q$4*(N18-$Q$18)+0.5*$Q$6*(N18-$Q$18)*(N18-... | Formula | $Q$20, $Q$4, N18, $Q$18, $Q$6 |
| O20 | =$Q$20+$Q$4*(O18-$Q$18)+0.5*$Q$6*(O18-$Q$18)*(O18-... | Formula | $Q$20, $Q$4, O18, $Q$18, $Q$6 |
| P20 | =$Q$20+$Q$4*(P18-$Q$18)+0.5*$Q$6*(P18-$Q$18)*(P18-... | Formula | $Q$20, $Q$4, P18, $Q$18, $Q$6 |
| Q20 | =Q14 | Formula | Q14 |
| R20 | =$Q$20+$Q$4*(R18-$Q$18)+0.5*$Q$6*(R18-$Q$18)*(R18-... | Formula | $Q$20, $Q$4, R18, $Q$18, $Q$6 |
| S20 | =$Q$20+$Q$4*(S18-$Q$18)+0.5*$Q$6*(S18-$Q$18)*(S18-... | Formula | $Q$20, $Q$4, S18, $Q$18, $Q$6 |
| T20 | =$Q$20+$Q$4*(T18-$Q$18)+0.5*$Q$6*(T18-$Q$18)*(T18-... | Formula | $Q$20, $Q$4, T18, $Q$18, $Q$6 |
| U20 | =$Q$20+$Q$4*(U18-$Q$18)+0.5*$Q$6*(U18-$Q$18)*(U18-... | Formula | $Q$20, $Q$4, U18, $Q$18, $Q$6 |
| V20 | =$Q$20+$Q$4*(V18-$Q$18)+0.5*$Q$6*(V18-$Q$18)*(V18-... | Formula | $Q$20, $Q$4, V18, $Q$18, $Q$6 |
| W20 | =$Q$20+$Q$4*(W18-$Q$18)+0.5*$Q$6*(W18-$Q$18)*(W18-... | Formula | $Q$20, $Q$4, W18, $Q$18, $Q$6 |
| X20 | =$Q$20+$Q$4*(X18-$Q$18)+0.5*$Q$6*(X18-$Q$18)*(X18-... | Formula | $Q$20, $Q$4, X18, $Q$18, $Q$6 |
| Y20 | =$Q$20+$Q$4*(Y18-$Q$18)+0.5*$Q$6*(Y18-$Q$18)*(Y18-... | Formula | $Q$20, $Q$4, Y18, $Q$18, $Q$6 |
| Z20 | =$Q$20+$Q$4*(Z18-$Q$18)+0.5*$Q$6*(Z18-$Q$18)*(Z18-... | Formula | $Q$20, $Q$4, Z18, $Q$18, $Q$6 |
| AA21 | =Z14+Z4*(AA18-Z18)+0.5*Z6*(AA18-Z18)*(AA18-Z18) | Formula | Z14, Z4, AA18, Z18, Z6 |
| AB21 | =AA14+AA4*(AB18-AA18)+0.5*AA6*(AB18-AA18)*(AB18-AA... | Formula | AA14, AA4, AB18, AA18, AA6 |
| AC21 | =AB14+AB4*(AC18-AB18)+0.5*AB6*(AC18-AB18)*(AC18-AB... | Formula | AB14, AB4, AC18, AB18, AB6 |
| C21 | TS Predicted from n-0.25 | Value | - |
| E21 | =F14+F4*(E18-F18)+0.5*F6*(E18-F18)*(E18-F18) | Formula | F14, F4, E18, F18, F6 |
| F21 | =G14+G4*(F18-G18)+0.5*G6*(F18-G18)*(F18-G18) | Formula | G14, G4, F18, G18, G6 |
| G21 | =H14+H4*(G18-H18)+0.5*H6*(G18-H18)*(G18-H18) | Formula | H14, H4, G18, H18, H6 |
| H21 | =I14+I4*(H18-I18)+0.5*I6*(H18-I18)*(H18-I18) | Formula | I14, I4, H18, I18, I6 |
| I21 | =J14+J4*(I18-J18)+0.5*J6*(I18-J18)*(I18-J18) | Formula | J14, J4, I18, J18, J6 |
| J21 | =K14+K4*(J18-K18)+0.5*K6*(J18-K18)*(J18-K18) | Formula | K14, K4, J18, K18, K6 |
| K21 | =L14+L4*(K18-L18)+0.5*L6*(K18-L18)*(K18-L18) | Formula | L14, L4, K18, L18, L6 |
| L21 | =M14+M4*(L18-M18)+0.5*M6*(L18-M18)*(L18-M18) | Formula | M14, M4, L18, M18, M6 |
| M21 | =N14+N4*(M18-N18)+0.5*N6*(M18-N18)*(M18-N18) | Formula | N14, N4, M18, N18, N6 |
| N21 | =O14+O4*(N18-O18)+0.5*O6*(N18-O18)*(N18-O18) | Formula | O14, O4, N18, O18, O6 |
| O21 | =P14+P4*(O18-P18)+0.5*P6*(O18-P18)*(O18-P18) | Formula | P14, P4, O18, P18, P6 |
| P21 | =Q14+Q4*(P18-Q18)+0.5*Q6*(P18-Q18)*(P18-Q18) | Formula | Q14, Q4, P18, Q18, Q6 |
| Q21 | =Q14 | Formula | Q14 |
| R21 | =Q14+Q4*(R18-Q18)+0.5*Q6*(R18-Q18)*(R18-Q18) | Formula | Q14, Q4, R18, Q18, Q6 |
| S21 | =R14+R4*(S18-R18)+0.5*R6*(S18-R18)*(S18-R18) | Formula | R14, R4, S18, R18, R6 |
| T21 | =S14+S4*(T18-S18)+0.5*S6*(T18-S18)*(T18-S18) | Formula | S14, S4, T18, S18, S6 |
| U21 | =T14+T4*(U18-T18)+0.5*T6*(U18-T18)*(U18-T18) | Formula | T14, T4, U18, T18, T6 |
| V21 | =U14+U4*(V18-U18)+0.5*U6*(V18-U18)*(V18-U18) | Formula | U14, U4, V18, U18, U6 |
| W21 | =V14+V4*(W18-V18)+0.5*V6*(W18-V18)*(W18-V18) | Formula | V14, V4, W18, V18, V6 |
| X21 | =W14+W4*(X18-W18)+0.5*W6*(X18-W18)*(X18-W18) | Formula | W14, W4, X18, W18, W6 |
| Y21 | =X14+X4*(Y18-X18)+0.5*X6*(Y18-X18)*(Y18-X18) | Formula | X14, X4, Y18, X18, X6 |
| Z21 | =Y14+Y4*(Z18-Y18)+0.5*Y6*(Z18-Y18)*(Z18-Y18) | Formula | Y14, Y4, Z18, Y18, Y6 |
| AA22 | =AA20-AA19 | Formula | AA20, AA19 |
| AB22 | =AB20-AB19 | Formula | AB20, AB19 |
| AC22 | =AC20-AC19 | Formula | AC20, AC19 |
| C22 | Call TS0vA Diff | Value | - |
| E22 | =E20-E19 | Formula | E20, E19 |
| F22 | =F20-F19 | Formula | F20, F19 |
| G22 | =G20-G19 | Formula | G20, G19 |
| H22 | =H20-H19 | Formula | H20, H19 |
| I22 | =I20-I19 | Formula | I20, I19 |
| J22 | =J20-J19 | Formula | J20, J19 |
| K22 | =K20-K19 | Formula | K20, K19 |
| L22 | =L20-L19 | Formula | L20, L19 |
| M22 | =M20-M19 | Formula | M20, M19 |
| N22 | =N20-N19 | Formula | N20, N19 |
| O22 | =O20-O19 | Formula | O20, O19 |
| P22 | =P20-P19 | Formula | P20, P19 |
| Q22 | =Q20-Q19 | Formula | Q20, Q19 |
| R22 | =R20-R19 | Formula | R20, R19 |
| S22 | =S20-S19 | Formula | S20, S19 |
| T22 | =T20-T19 | Formula | T20, T19 |
| U22 | =U20-U19 | Formula | U20, U19 |
| V22 | =V20-V19 | Formula | V20, V19 |
| W22 | =W20-W19 | Formula | W20, W19 |
| X22 | =X20-X19 | Formula | X20, X19 |
| Y22 | =Y20-Y19 | Formula | Y20, Y19 |
| Z22 | =Z20-Z19 | Formula | Z20, Z19 |
| AA23 | =AA21-AA19 | Formula | AA21, AA19 |
| AB23 | =AB21-AB19 | Formula | AB21, AB19 |
| AC23 | =AC21-AC19 | Formula | AC21, AC19 |
| C23 | Call TS-0.25vA Diff | Value | - |
| E23 | =E21-E19 | Formula | E21, E19 |
| F23 | =F21-F19 | Formula | F21, F19 |
| G23 | =G21-G19 | Formula | G21, G19 |
| H23 | =H21-H19 | Formula | H21, H19 |
| I23 | =I21-I19 | Formula | I21, I19 |
| J23 | =J21-J19 | Formula | J21, J19 |
| K23 | =K21-K19 | Formula | K21, K19 |
| L23 | =L21-L19 | Formula | L21, L19 |
| M23 | =M21-M19 | Formula | M21, M19 |
| N23 | =N21-N19 | Formula | N21, N19 |
| O23 | =O21-O19 | Formula | O21, O19 |
| P23 | =P21-P19 | Formula | P21, P19 |
| Q23 | =Q21-Q19 | Formula | Q21, Q19 |
| R23 | =R21-R19 | Formula | R21, R19 |
| S23 | =S21-S19 | Formula | S21, S19 |
| T23 | =T21-T19 | Formula | T21, T19 |
| U23 | =U21-U19 | Formula | U21, U19 |
| V23 | =V21-V19 | Formula | V21, V19 |
| W23 | =W21-W19 | Formula | W21, W19 |
| X23 | =X21-X19 | Formula | X21, X19 |
| Y23 | =Y21-Y19 | Formula | Y21, Y19 |
| Z23 | =Z21-Z19 | Formula | Z21, Z19 |
| AA25 | 40 | Value | - |
| AB25 | 44 | Value | - |
| AC25 | 48 | Value | - |
| C25 | shift in bp | Value | - |
| E25 | -48 | Value | - |
| F25 | -44 | Value | - |
| G25 | -40 | Value | - |
| H25 | -36 | Value | - |
| I25 | -32 | Value | - |
| J25 | -28 | Value | - |
| K25 | -24 | Value | - |
| L25 | -20 | Value | - |
| M25 | -16 | Value | - |
| N25 | -12 | Value | - |
| O25 | -8 | Value | - |
| P25 | -4 | Value | - |
| Q25 | 0 | Value | - |
| R25 | 4 | Value | - |
| S25 | 8 | Value | - |
| T25 | 12 | Value | - |
| U25 | 16 | Value | - |
| V25 | 20 | Value | - |
| W25 | 24 | Value | - |
| X25 | 28 | Value | - |
| Y25 | 32 | Value | - |
| Z25 | 36 | Value | - |
| AA26 | =AA19-$Q$19 | Formula | AA19, $Q$19 |
| AB26 | =AB19-$Q$19 | Formula | AB19, $Q$19 |
| AC26 | =AC19-$Q$19 | Formula | AC19, $Q$19 |
| C26 | ACTANT PNL | Value | - |
| E26 | =E19-$Q$19 | Formula | E19, $Q$19 |
| F26 | =F19-$Q$19 | Formula | F19, $Q$19 |
| G26 | =G19-$Q$19 | Formula | G19, $Q$19 |
| H26 | =H19-$Q$19 | Formula | H19, $Q$19 |
| I26 | =I19-$Q$19 | Formula | I19, $Q$19 |
| J26 | =J19-$Q$19 | Formula | J19, $Q$19 |
| K26 | =K19-$Q$19 | Formula | K19, $Q$19 |
| L26 | =L19-$Q$19 | Formula | L19, $Q$19 |
| M26 | =M19-$Q$19 | Formula | M19, $Q$19 |
| N26 | =N19-$Q$19 | Formula | N19, $Q$19 |
| O26 | =O19-$Q$19 | Formula | O19, $Q$19 |
| P26 | =P19-$Q$19 | Formula | P19, $Q$19 |
| Q26 | =Q19-$Q$19 | Formula | Q19, $Q$19 |
| R26 | =R19-$Q$19 | Formula | R19, $Q$19 |
| S26 | =S19-$Q$19 | Formula | S19, $Q$19 |
| T26 | =T19-$Q$19 | Formula | T19, $Q$19 |
| U26 | =U19-$Q$19 | Formula | U19, $Q$19 |
| V26 | =V19-$Q$19 | Formula | V19, $Q$19 |
| W26 | =W19-$Q$19 | Formula | W19, $Q$19 |
| X26 | =X19-$Q$19 | Formula | X19, $Q$19 |
| Y26 | =Y19-$Q$19 | Formula | Y19, $Q$19 |
| Z26 | =Z19-$Q$19 | Formula | Z19, $Q$19 |
| AA27 | =AA20-$Q$20 | Formula | AA20, $Q$20 |
| AB27 | =AB20-$Q$20 | Formula | AB20, $Q$20 |
| AC27 | =AC20-$Q$20 | Formula | AC20, $Q$20 |
| C27 | TS0 PNL (cumlv) | Value | - |
| E27 | =E20-$Q$20 | Formula | E20, $Q$20 |
| F27 | =F20-$Q$20 | Formula | F20, $Q$20 |
| G27 | =G20-$Q$20 | Formula | G20, $Q$20 |
| H27 | =H20-$Q$20 | Formula | H20, $Q$20 |
| I27 | =I20-$Q$20 | Formula | I20, $Q$20 |
| J27 | =J20-$Q$20 | Formula | J20, $Q$20 |
| K27 | =K20-$Q$20 | Formula | K20, $Q$20 |
| L27 | =L20-$Q$20 | Formula | L20, $Q$20 |
| M27 | =M20-$Q$20 | Formula | M20, $Q$20 |
| N27 | =N20-$Q$20 | Formula | N20, $Q$20 |
| O27 | =O20-$Q$20 | Formula | O20, $Q$20 |
| P27 | =P20-$Q$20 | Formula | P20, $Q$20 |
| Q27 | =Q20-$Q$20 | Formula | Q20, $Q$20 |
| R27 | =R20-$Q$20 | Formula | R20, $Q$20 |
| S27 | =S20-$Q$20 | Formula | S20, $Q$20 |
| T27 | =T20-$Q$20 | Formula | T20, $Q$20 |
| U27 | =U20-$Q$20 | Formula | U20, $Q$20 |
| V27 | =V20-$Q$20 | Formula | V20, $Q$20 |
| W27 | =W20-$Q$20 | Formula | W20, $Q$20 |
| X27 | =X20-$Q$20 | Formula | X20, $Q$20 |
| Y27 | =Y20-$Q$20 | Formula | Y20, $Q$20 |
| Z27 | =Z20-$Q$20 | Formula | Z20, $Q$20 |
| AA28 | =AA21-$Q$21 | Formula | AA21, $Q$21 |
| AB28 | =AB21-$Q$21 | Formula | AB21, $Q$21 |
| AC28 | =AC21-$Q$21 | Formula | AC21, $Q$21 |
| C28 | TS-0.25 PNL (cumlv) | Value | - |
| E28 | =E21-$Q$21 | Formula | E21, $Q$21 |
| F28 | =F21-$Q$21 | Formula | F21, $Q$21 |
| G28 | =G21-$Q$21 | Formula | G21, $Q$21 |
| H28 | =H21-$Q$21 | Formula | H21, $Q$21 |
| I28 | =I21-$Q$21 | Formula | I21, $Q$21 |
| J28 | =J21-$Q$21 | Formula | J21, $Q$21 |
| K28 | =K21-$Q$21 | Formula | K21, $Q$21 |
| L28 | =L21-$Q$21 | Formula | L21, $Q$21 |
| M28 | =M21-$Q$21 | Formula | M21, $Q$21 |
| N28 | =N21-$Q$21 | Formula | N21, $Q$21 |
| O28 | =O21-$Q$21 | Formula | O21, $Q$21 |
| P28 | =P21-$Q$21 | Formula | P21, $Q$21 |
| Q28 | =Q21-$Q$21 | Formula | Q21, $Q$21 |
| R28 | =R21-$Q$21 | Formula | R21, $Q$21 |
| S28 | =S21-$Q$21 | Formula | S21, $Q$21 |
| T28 | =T21-$Q$21 | Formula | T21, $Q$21 |
| U28 | =U21-$Q$21 | Formula | U21, $Q$21 |
| V28 | =V21-$Q$21 | Formula | V21, $Q$21 |
| W28 | =W21-$Q$21 | Formula | W21, $Q$21 |
| X28 | =X21-$Q$21 | Formula | X21, $Q$21 |
| Y28 | =Y21-$Q$21 | Formula | Y21, $Q$21 |
| Z28 | =Z21-$Q$21 | Formula | Z21, $Q$21 |
| AA29 | =AA27-AA26 | Formula | AA27, AA26 |
| AB29 | =AB27-AB26 | Formula | AB27, AB26 |
| AC29 | =AC27-AC26 | Formula | AC27, AC26 |
| C29 | 0DIFF | Value | - |
| E29 | =E27-E26 | Formula | E27, E26 |
| F29 | =F27-F26 | Formula | F27, F26 |
| G29 | =G27-G26 | Formula | G27, G26 |
| H29 | =H27-H26 | Formula | H27, H26 |
| I29 | =I27-I26 | Formula | I27, I26 |
| J29 | =J27-J26 | Formula | J27, J26 |
| K29 | =K27-K26 | Formula | K27, K26 |
| L29 | =L27-L26 | Formula | L27, L26 |
| M29 | =M27-M26 | Formula | M27, M26 |
| N29 | =N27-N26 | Formula | N27, N26 |
| O29 | =O27-O26 | Formula | O27, O26 |
| P29 | =P27-P26 | Formula | P27, P26 |
| Q29 | =Q27-Q26 | Formula | Q27, Q26 |
| R29 | =R27-R26 | Formula | R27, R26 |
| S29 | =S27-S26 | Formula | S27, S26 |
| T29 | =T27-T26 | Formula | T27, T26 |
| U29 | =U27-U26 | Formula | U27, U26 |
| V29 | =V27-V26 | Formula | V27, V26 |
| W29 | =W27-W26 | Formula | W27, W26 |
| X29 | =X27-X26 | Formula | X27, X26 |
| Y29 | =Y27-Y26 | Formula | Y27, Y26 |
| Z29 | =Z27-Z26 | Formula | Z27, Z26 |
| AA30 | =AA28-AA26 | Formula | AA28, AA26 |
| AB30 | =AB28-AB26 | Formula | AB28, AB26 |
| AC30 | =AC28-AC26 | Formula | AC28, AC26 |
| C30 | -0.25DIFF | Value | - |
| E30 | =E28-E26 | Formula | E28, E26 |
| F30 | =F28-F26 | Formula | F28, F26 |
| G30 | =G28-G26 | Formula | G28, G26 |
| H30 | =H28-H26 | Formula | H28, H26 |
| I30 | =I28-I26 | Formula | I28, I26 |
| J30 | =J28-J26 | Formula | J28, J26 |
| K30 | =K28-K26 | Formula | K28, K26 |
| L30 | =L28-L26 | Formula | L28, L26 |
| M30 | =M28-M26 | Formula | M28, M26 |
| N30 | =N28-N26 | Formula | N28, N26 |
| O30 | =O28-O26 | Formula | O28, O26 |
| P30 | =P28-P26 | Formula | P28, P26 |
| Q30 | =Q28-Q26 | Formula | Q28, Q26 |
| R30 | =R28-R26 | Formula | R28, R26 |
| S30 | =S28-S26 | Formula | S28, S26 |
| T30 | =T28-T26 | Formula | T28, T26 |
| U30 | =U28-U26 | Formula | U28, U26 |
| V30 | =V28-V26 | Formula | V28, V26 |
| W30 | =W28-W26 | Formula | W28, W26 |
| X30 | =X28-X26 | Formula | X28, X26 |
| Y30 | =Y28-Y26 | Formula | Y28, Y26 |
| Z30 | =Z28-Z26 | Formula | Z28, Z26 |

### Put Analysis

| Cell | Value/Formula | Type | Dependencies |
|------|---------------|------|--------------|
| AA32 | 40 | Value | - |
| AB32 | 44 | Value | - |
| AC32 | 48 | Value | - |
| C32 | shift in bp | Value | - |
| E32 | -48 | Value | - |
| F32 | -44 | Value | - |
| G32 | -40 | Value | - |
| H32 | -36 | Value | - |
| I32 | -32 | Value | - |
| J32 | -28 | Value | - |
| K32 | -24 | Value | - |
| L32 | -20 | Value | - |
| M32 | -16 | Value | - |
| N32 | -12 | Value | - |
| O32 | -8 | Value | - |
| P32 | -4 | Value | - |
| Q32 | 0 | Value | - |
| R32 | 4 | Value | - |
| S32 | 8 | Value | - |
| T32 | 12 | Value | - |
| U32 | 16 | Value | - |
| V32 | 20 | Value | - |
| W32 | 24 | Value | - |
| X32 | 28 | Value | - |
| Y32 | 32 | Value | - |
| Z32 | 36 | Value | - |
| AA33 | =AA15 | Formula | AA15 |
| AB33 | =AB15 | Formula | AB15 |
| AC33 | =AC15 | Formula | AC15 |
| C33 | Put Price ACTANT | Value | - |
| E33 | =E15 | Formula | E15 |
| F33 | =F15 | Formula | F15 |
| G33 | =G15 | Formula | G15 |
| H33 | =H15 | Formula | H15 |
| I33 | =I15 | Formula | I15 |
| J33 | =J15 | Formula | J15 |
| K33 | =K15 | Formula | K15 |
| L33 | =L15 | Formula | L15 |
| M33 | =M15 | Formula | M15 |
| N33 | =N15 | Formula | N15 |
| O33 | =O15 | Formula | O15 |
| P33 | =P15 | Formula | P15 |
| Q33 | =Q15 | Formula | Q15 |
| R33 | =R15 | Formula | R15 |
| S33 | =S15 | Formula | S15 |
| T33 | =T15 | Formula | T15 |
| U33 | =U15 | Formula | U15 |
| V33 | =V15 | Formula | V15 |
| W33 | =W15 | Formula | W15 |
| X33 | =X15 | Formula | X15 |
| Y33 | =Y15 | Formula | Y15 |
| Z33 | =Z15 | Formula | Z15 |
| AA34 | =$Q$34+$Q$5*(AA32-$Q$32)+0.5*$Q$6*(AA32-$Q$32)*(AA... | Formula | $Q$34, $Q$5, AA32, $Q$32, $Q$6 |
| AB34 | =$Q$34+$Q$5*(AB32-$Q$32)+0.5*$Q$6*(AB32-$Q$32)*(AB... | Formula | $Q$34, $Q$5, AB32, $Q$32, $Q$6 |
| AC34 | =$Q$34+$Q$5*(AC32-$Q$32)+0.5*$Q$6*(AC32-$Q$32)*(AC... | Formula | $Q$34, $Q$5, AC32, $Q$32, $Q$6 |
| C34 | TS Predicted from 0 | Value | - |
| E34 | =$Q$34+$Q$5*(E32-$Q$32)+0.5*$Q$6*(E32-$Q$32)*(E32-... | Formula | $Q$34, $Q$5, E32, $Q$32, $Q$6 |
| F34 | =$Q$34+$Q$5*(F32-$Q$32)+0.5*$Q$6*(F32-$Q$32)*(F32-... | Formula | $Q$34, $Q$5, F32, $Q$32, $Q$6 |
| G34 | =$Q$34+$Q$5*(G32-$Q$32)+0.5*$Q$6*(G32-$Q$32)*(G32-... | Formula | $Q$34, $Q$5, G32, $Q$32, $Q$6 |
| H34 | =$Q$34+$Q$5*(H32-$Q$32)+0.5*$Q$6*(H32-$Q$32)*(H32-... | Formula | $Q$34, $Q$5, H32, $Q$32, $Q$6 |
| I34 | =$Q$34+$Q$5*(I32-$Q$32)+0.5*$Q$6*(I32-$Q$32)*(I32-... | Formula | $Q$34, $Q$5, I32, $Q$32, $Q$6 |
| J34 | =$Q$34+$Q$5*(J32-$Q$32)+0.5*$Q$6*(J32-$Q$32)*(J32-... | Formula | $Q$34, $Q$5, J32, $Q$32, $Q$6 |
| K34 | =$Q$34+$Q$5*(K32-$Q$32)+0.5*$Q$6*(K32-$Q$32)*(K32-... | Formula | $Q$34, $Q$5, K32, $Q$32, $Q$6 |
| L34 | =$Q$34+$Q$5*(L32-$Q$32)+0.5*$Q$6*(L32-$Q$32)*(L32-... | Formula | $Q$34, $Q$5, L32, $Q$32, $Q$6 |
| M34 | =$Q$34+$Q$5*(M32-$Q$32)+0.5*$Q$6*(M32-$Q$32)*(M32-... | Formula | $Q$34, $Q$5, M32, $Q$32, $Q$6 |
| N34 | =$Q$34+$Q$5*(N32-$Q$32)+0.5*$Q$6*(N32-$Q$32)*(N32-... | Formula | $Q$34, $Q$5, N32, $Q$32, $Q$6 |
| O34 | =$Q$34+$Q$5*(O32-$Q$32)+0.5*$Q$6*(O32-$Q$32)*(O32-... | Formula | $Q$34, $Q$5, O32, $Q$32, $Q$6 |
| P34 | =$Q$34+$Q$5*(P32-$Q$32)+0.5*$Q$6*(P32-$Q$32)*(P32-... | Formula | $Q$34, $Q$5, P32, $Q$32, $Q$6 |
| Q34 | =Q15 | Formula | Q15 |
| R34 | =$Q$34+$Q$5*(R32-$Q$32)+0.5*$Q$6*(R32-$Q$32)*(R32-... | Formula | $Q$34, $Q$5, R32, $Q$32, $Q$6 |
| S34 | =$Q$34+$Q$5*(S32-$Q$32)+0.5*$Q$6*(S32-$Q$32)*(S32-... | Formula | $Q$34, $Q$5, S32, $Q$32, $Q$6 |
| T34 | =$Q$34+$Q$5*(T32-$Q$32)+0.5*$Q$6*(T32-$Q$32)*(T32-... | Formula | $Q$34, $Q$5, T32, $Q$32, $Q$6 |
| U34 | =$Q$34+$Q$5*(U32-$Q$32)+0.5*$Q$6*(U32-$Q$32)*(U32-... | Formula | $Q$34, $Q$5, U32, $Q$32, $Q$6 |
| V34 | =$Q$34+$Q$5*(V32-$Q$32)+0.5*$Q$6*(V32-$Q$32)*(V32-... | Formula | $Q$34, $Q$5, V32, $Q$32, $Q$6 |
| W34 | =$Q$34+$Q$5*(W32-$Q$32)+0.5*$Q$6*(W32-$Q$32)*(W32-... | Formula | $Q$34, $Q$5, W32, $Q$32, $Q$6 |
| X34 | =$Q$34+$Q$5*(X32-$Q$32)+0.5*$Q$6*(X32-$Q$32)*(X32-... | Formula | $Q$34, $Q$5, X32, $Q$32, $Q$6 |
| Y34 | =$Q$34+$Q$5*(Y32-$Q$32)+0.5*$Q$6*(Y32-$Q$32)*(Y32-... | Formula | $Q$34, $Q$5, Y32, $Q$32, $Q$6 |
| Z34 | =$Q$34+$Q$5*(Z32-$Q$32)+0.5*$Q$6*(Z32-$Q$32)*(Z32-... | Formula | $Q$34, $Q$5, Z32, $Q$32, $Q$6 |
| AA35 | =Z33+Z5*(AA32-Z32)+0.5*Z6*(AA32-Z32)*(AA32-Z32) | Formula | Z33, Z5, AA32, Z32, Z6 |
| AB35 | =AA33+AA5*(AB32-AA32)+0.5*AA6*(AB32-AA32)*(AB32-AA... | Formula | AA33, AA5, AB32, AA32, AA6 |
| AC35 | =AB33+AB5*(AC32-AB32)+0.5*AB6*(AC32-AB32)*(AC32-AB... | Formula | AB33, AB5, AC32, AB32, AB6 |
| C35 | TS Predicted from n-0.25 | Value | - |
| E35 | =F33+F5*(E32-F32)+0.5*F6*(E32-F32)*(E32-F32) | Formula | F33, F5, E32, F32, F6 |
| F35 | =G33+G5*(F32-G32)+0.5*G6*(F32-G32)*(F32-G32) | Formula | G33, G5, F32, G32, G6 |
| G35 | =H33+H5*(G32-H32)+0.5*H6*(G32-H32)*(G32-H32) | Formula | H33, H5, G32, H32, H6 |
| H35 | =I33+I5*(H32-I32)+0.5*I6*(H32-I32)*(H32-I32) | Formula | I33, I5, H32, I32, I6 |
| I35 | =J33+J5*(I32-J32)+0.5*J6*(I32-J32)*(I32-J32) | Formula | J33, J5, I32, J32, J6 |
| J35 | =K33+K5*(J32-K32)+0.5*K6*(J32-K32)*(J32-K32) | Formula | K33, K5, J32, K32, K6 |
| K35 | =L33+L5*(K32-L32)+0.5*L6*(K32-L32)*(K32-L32) | Formula | L33, L5, K32, L32, L6 |
| L35 | =M33+M5*(L32-M32)+0.5*M6*(L32-M32)*(L32-M32) | Formula | M33, M5, L32, M32, M6 |
| M35 | =N33+N5*(M32-N32)+0.5*N6*(M32-N32)*(M32-N32) | Formula | N33, N5, M32, N32, N6 |
| N35 | =O33+O5*(N32-O32)+0.5*O6*(N32-O32)*(N32-O32) | Formula | O33, O5, N32, O32, O6 |
| O35 | =P33+P5*(O32-P32)+0.5*P6*(O32-P32)*(O32-P32) | Formula | P33, P5, O32, P32, P6 |
| P35 | =Q33+Q5*(P32-Q32)+0.5*Q6*(P32-Q32)*(P32-Q32) | Formula | Q33, Q5, P32, Q32, Q6 |
| Q35 | =Q15 | Formula | Q15 |
| R35 | =Q33+Q5*(R32-Q32)+0.5*Q6*(R32-Q32)*(R32-Q32) | Formula | Q33, Q5, R32, Q32, Q6 |
| S35 | =R33+R5*(S32-R32)+0.5*R6*(S32-R32)*(S32-R32) | Formula | R33, R5, S32, R32, R6 |
| T35 | =S33+S5*(T32-S32)+0.5*S6*(T32-S32)*(T32-S32) | Formula | S33, S5, T32, S32, S6 |
| U35 | =T33+T5*(U32-T32)+0.5*T6*(U32-T32)*(U32-T32) | Formula | T33, T5, U32, T32, T6 |
| V35 | =U33+U5*(V32-U32)+0.5*U6*(V32-U32)*(V32-U32) | Formula | U33, U5, V32, U32, U6 |
| W35 | =V33+V5*(W32-V32)+0.5*V6*(W32-V32)*(W32-V32) | Formula | V33, V5, W32, V32, V6 |
| X35 | =W33+W5*(X32-W32)+0.5*W6*(X32-W32)*(X32-W32) | Formula | W33, W5, X32, W32, W6 |
| Y35 | =X33+X5*(Y32-X32)+0.5*X6*(Y32-X32)*(Y32-X32) | Formula | X33, X5, Y32, X32, X6 |
| Z35 | =Y33+Y5*(Z32-Y32)+0.5*Y6*(Z32-Y32)*(Z32-Y32) | Formula | Y33, Y5, Z32, Y32, Y6 |
| AA36 | =AA34-AA33 | Formula | AA34, AA33 |
| AB36 | =AB34-AB33 | Formula | AB34, AB33 |
| AC36 | =AC34-AC33 | Formula | AC34, AC33 |
| C36 | Call TS0vA Diff | Value | - |
| E36 | =E34-E33 | Formula | E34, E33 |
| F36 | =F34-F33 | Formula | F34, F33 |
| G36 | =G34-G33 | Formula | G34, G33 |
| H36 | =H34-H33 | Formula | H34, H33 |
| I36 | =I34-I33 | Formula | I34, I33 |
| J36 | =J34-J33 | Formula | J34, J33 |
| K36 | =K34-K33 | Formula | K34, K33 |
| L36 | =L34-L33 | Formula | L34, L33 |
| M36 | =M34-M33 | Formula | M34, M33 |
| N36 | =N34-N33 | Formula | N34, N33 |
| O36 | =O34-O33 | Formula | O34, O33 |
| P36 | =P34-P33 | Formula | P34, P33 |
| Q36 | =Q34-Q33 | Formula | Q34, Q33 |
| R36 | =R34-R33 | Formula | R34, R33 |
| S36 | =S34-S33 | Formula | S34, S33 |
| T36 | =T34-T33 | Formula | T34, T33 |
| U36 | =U34-U33 | Formula | U34, U33 |
| V36 | =V34-V33 | Formula | V34, V33 |
| W36 | =W34-W33 | Formula | W34, W33 |
| X36 | =X34-X33 | Formula | X34, X33 |
| Y36 | =Y34-Y33 | Formula | Y34, Y33 |
| Z36 | =Z34-Z33 | Formula | Z34, Z33 |
| AA37 | 40 | Value | - |
| AB37 | 44 | Value | - |
| AC37 | 48 | Value | - |
| C37 | shift in bp | Value | - |
| E37 | -48 | Value | - |
| F37 | -44 | Value | - |
| G37 | -40 | Value | - |
| H37 | -36 | Value | - |
| I37 | -32 | Value | - |
| J37 | -28 | Value | - |
| K37 | -24 | Value | - |
| L37 | -20 | Value | - |
| M37 | -16 | Value | - |
| N37 | -12 | Value | - |
| O37 | -8 | Value | - |
| P37 | -4 | Value | - |
| Q37 | 0 | Value | - |
| R37 | 4 | Value | - |
| S37 | 8 | Value | - |
| T37 | 12 | Value | - |
| U37 | 16 | Value | - |
| V37 | 20 | Value | - |
| W37 | 24 | Value | - |
| X37 | 28 | Value | - |
| Y37 | 32 | Value | - |
| Z37 | 36 | Value | - |
| AA39 | 40 | Value | - |
| AB39 | 44 | Value | - |
| AC39 | 48 | Value | - |
| C39 | shift in bp | Value | - |
| E39 | -48 | Value | - |
| F39 | -44 | Value | - |
| G39 | -40 | Value | - |
| H39 | -36 | Value | - |
| I39 | -32 | Value | - |
| J39 | -28 | Value | - |
| K39 | -24 | Value | - |
| L39 | -20 | Value | - |
| M39 | -16 | Value | - |
| N39 | -12 | Value | - |
| O39 | -8 | Value | - |
| P39 | -4 | Value | - |
| Q39 | 0 | Value | - |
| R39 | 4 | Value | - |
| S39 | 8 | Value | - |
| T39 | 12 | Value | - |
| U39 | 16 | Value | - |
| V39 | 20 | Value | - |
| W39 | 24 | Value | - |
| X39 | 28 | Value | - |
| Y39 | 32 | Value | - |
| Z39 | 36 | Value | - |
| AA40 | =AA15-$Q$15 | Formula | AA15, $Q$15 |
| AB40 | =AB15-$Q$15 | Formula | AB15, $Q$15 |
| AC40 | =AC15-$Q$15 | Formula | AC15, $Q$15 |
| C40 | ACTANT PNL | Value | - |
| E40 | =E15-$Q$15 | Formula | E15, $Q$15 |
| F40 | =F15-$Q$15 | Formula | F15, $Q$15 |
| G40 | =G15-$Q$15 | Formula | G15, $Q$15 |
| H40 | =H15-$Q$15 | Formula | H15, $Q$15 |
| I40 | =I15-$Q$15 | Formula | I15, $Q$15 |
| J40 | =J15-$Q$15 | Formula | J15, $Q$15 |
| K40 | =K15-$Q$15 | Formula | K15, $Q$15 |
| L40 | =L15-$Q$15 | Formula | L15, $Q$15 |
| M40 | =M15-$Q$15 | Formula | M15, $Q$15 |
| N40 | =N15-$Q$15 | Formula | N15, $Q$15 |
| O40 | =O15-$Q$15 | Formula | O15, $Q$15 |
| P40 | =P15-$Q$15 | Formula | P15, $Q$15 |
| Q40 | =Q15-$Q$15 | Formula | Q15, $Q$15 |
| R40 | =R15-$Q$15 | Formula | R15, $Q$15 |
| S40 | =S15-$Q$15 | Formula | S15, $Q$15 |
| T40 | =T15-$Q$15 | Formula | T15, $Q$15 |
| U40 | =U15-$Q$15 | Formula | U15, $Q$15 |
| V40 | =V15-$Q$15 | Formula | V15, $Q$15 |
| W40 | =W15-$Q$15 | Formula | W15, $Q$15 |
| X40 | =X15-$Q$15 | Formula | X15, $Q$15 |
| Y40 | =Y15-$Q$15 | Formula | Y15, $Q$15 |
| Z40 | =Z15-$Q$15 | Formula | Z15, $Q$15 |
| AA41 | =AA34-$Q$34 | Formula | AA34, $Q$34 |
| AB41 | =AB34-$Q$34 | Formula | AB34, $Q$34 |
| AC41 | =AC34-$Q$34 | Formula | AC34, $Q$34 |
| C41 | TS0 PNL (cumlv) | Value | - |
| E41 | =E34-$Q$34 | Formula | E34, $Q$34 |
| F41 | =F34-$Q$34 | Formula | F34, $Q$34 |
| G41 | =G34-$Q$34 | Formula | G34, $Q$34 |
| H41 | =H34-$Q$34 | Formula | H34, $Q$34 |
| I41 | =I34-$Q$34 | Formula | I34, $Q$34 |
| J41 | =J34-$Q$34 | Formula | J34, $Q$34 |
| K41 | =K34-$Q$34 | Formula | K34, $Q$34 |
| L41 | =L34-$Q$34 | Formula | L34, $Q$34 |
| M41 | =M34-$Q$34 | Formula | M34, $Q$34 |
| N41 | =N34-$Q$34 | Formula | N34, $Q$34 |
| O41 | =O34-$Q$34 | Formula | O34, $Q$34 |
| P41 | =P34-$Q$34 | Formula | P34, $Q$34 |
| Q41 | =Q34-$Q$34 | Formula | Q34, $Q$34 |
| R41 | =R34-$Q$34 | Formula | R34, $Q$34 |
| S41 | =S34-$Q$34 | Formula | S34, $Q$34 |
| T41 | =T34-$Q$34 | Formula | T34, $Q$34 |
| U41 | =U34-$Q$34 | Formula | U34, $Q$34 |
| V41 | =V34-$Q$34 | Formula | V34, $Q$34 |
| W41 | =W34-$Q$34 | Formula | W34, $Q$34 |
| X41 | =X34-$Q$34 | Formula | X34, $Q$34 |
| Y41 | =Y34-$Q$34 | Formula | Y34, $Q$34 |
| Z41 | =Z34-$Q$34 | Formula | Z34, $Q$34 |
| AA42 | =AA35-$Q$35 | Formula | AA35, $Q$35 |
| AB42 | =AB35-$Q$35 | Formula | AB35, $Q$35 |
| AC42 | =AC35-$Q$35 | Formula | AC35, $Q$35 |
| C42 | TS-0.25 PNL (cumlv) | Value | - |
| E42 | =E35-$Q$35 | Formula | E35, $Q$35 |
| F42 | =F35-$Q$35 | Formula | F35, $Q$35 |
| G42 | =G35-$Q$35 | Formula | G35, $Q$35 |
| H42 | =H35-$Q$35 | Formula | H35, $Q$35 |
| I42 | =I35-$Q$35 | Formula | I35, $Q$35 |
| J42 | =J35-$Q$35 | Formula | J35, $Q$35 |
| K42 | =K35-$Q$35 | Formula | K35, $Q$35 |
| L42 | =L35-$Q$35 | Formula | L35, $Q$35 |
| M42 | =M35-$Q$35 | Formula | M35, $Q$35 |
| N42 | =N35-$Q$35 | Formula | N35, $Q$35 |
| O42 | =O35-$Q$35 | Formula | O35, $Q$35 |
| P42 | =P35-$Q$35 | Formula | P35, $Q$35 |
| Q42 | =Q35-$Q$35 | Formula | Q35, $Q$35 |
| R42 | =R35-$Q$35 | Formula | R35, $Q$35 |
| S42 | =S35-$Q$35 | Formula | S35, $Q$35 |
| T42 | =T35-$Q$35 | Formula | T35, $Q$35 |
| U42 | =U35-$Q$35 | Formula | U35, $Q$35 |
| V42 | =V35-$Q$35 | Formula | V35, $Q$35 |
| W42 | =W35-$Q$35 | Formula | W35, $Q$35 |
| X42 | =X35-$Q$35 | Formula | X35, $Q$35 |
| Y42 | =Y35-$Q$35 | Formula | Y35, $Q$35 |
| Z42 | =Z35-$Q$35 | Formula | Z35, $Q$35 |
| AA43 | =AA41-AA40 | Formula | AA41, AA40 |
| AB43 | =AB41-AB40 | Formula | AB41, AB40 |
| AC43 | =AC41-AC40 | Formula | AC41, AC40 |
| C43 | 0DIFF | Value | - |
| E43 | =E41-E40 | Formula | E41, E40 |
| F43 | =F41-F40 | Formula | F41, F40 |
| G43 | =G41-G40 | Formula | G41, G40 |
| H43 | =H41-H40 | Formula | H41, H40 |
| I43 | =I41-I40 | Formula | I41, I40 |
| J43 | =J41-J40 | Formula | J41, J40 |
| K43 | =K41-K40 | Formula | K41, K40 |
| L43 | =L41-L40 | Formula | L41, L40 |
| M43 | =M41-M40 | Formula | M41, M40 |
| N43 | =N41-N40 | Formula | N41, N40 |
| O43 | =O41-O40 | Formula | O41, O40 |
| P43 | =P41-P40 | Formula | P41, P40 |
| Q43 | =Q41-Q40 | Formula | Q41, Q40 |
| R43 | =R41-R40 | Formula | R41, R40 |
| S43 | =S41-S40 | Formula | S41, S40 |
| T43 | =T41-T40 | Formula | T41, T40 |
| U43 | =U41-U40 | Formula | U41, U40 |
| V43 | =V41-V40 | Formula | V41, V40 |
| W43 | =W41-W40 | Formula | W41, W40 |
| X43 | =X41-X40 | Formula | X41, X40 |
| Y43 | =Y41-Y40 | Formula | Y41, Y40 |
| Z43 | =Z41-Z40 | Formula | Z41, Z40 |
| AA44 | =AA42-AA40 | Formula | AA42, AA40 |
| AB44 | =AB42-AB40 | Formula | AB42, AB40 |
| AC44 | =AC42-AC40 | Formula | AC42, AC40 |
| C44 | -0.25DIFF | Value | - |
| E44 | =E42-E40 | Formula | E42, E40 |
| F44 | =F42-F40 | Formula | F42, F40 |
| G44 | =G42-G40 | Formula | G42, G40 |
| H44 | =H42-H40 | Formula | H42, H40 |
| I44 | =I42-I40 | Formula | I42, I40 |
| J44 | =J42-J40 | Formula | J42, J40 |
| K44 | =K42-K40 | Formula | K42, K40 |
| L44 | =L42-L40 | Formula | L42, L40 |
| M44 | =M42-M40 | Formula | M42, M40 |
| N44 | =N42-N40 | Formula | N42, N40 |
| O44 | =O42-O40 | Formula | O42, O40 |
| P44 | =P42-P40 | Formula | P42, P40 |
| Q44 | =Q42-Q40 | Formula | Q42, Q40 |
| R44 | =R42-R40 | Formula | R42, R40 |
| S44 | =S42-S40 | Formula | S42, S40 |
| T44 | =T42-T40 | Formula | T42, T40 |
| U44 | =U42-U40 | Formula | U42, U40 |
| V44 | =V42-V40 | Formula | V42, V40 |
| W44 | =W42-W40 | Formula | W42, W40 |
| X44 | =X42-X40 | Formula | X42, X40 |
| Y44 | =Y42-Y40 | Formula | Y42, Y40 |
| Z44 | =Z42-Z40 | Formula | Z42, Z40 |