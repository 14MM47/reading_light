"""Direct + inter-reflected illuminance on the inside of the moon sphere from LEDs in its base.

Model: sphere inner radius R; bottom opening of half-angle phi_o (the LED base sits in it);
Lambertian LEDs (I = I0 cos a) on a horizontal board at height zb (sphere centre = 0), facing +z,
arranged in a ring of radius rr plus one at the centre. Wall: transmittance tau, reflectance rho
(white PLA, diffuse). Inter-reflection is treated as a uniform integrating-sphere term
E_ind = rho * Phi_wall / (A * (1 - rho * f_wall)), f_wall = wall area fraction.
Prints uniformity of total wall illuminance over the visible wall (theta > phi_o).
Usage: python sphere_illum.py  (no arguments; writes sphere_illum.csv beside this file)
"""
import csv
import math
import pathlib

import numpy as np

R = 23.6          # mm, inner radius (50 mm outer, ~1.4 mm mean wall)
RHO, TAU = 0.55, 0.35   # assumed white-PLA lithophane reflectance / transmittance (VERIFY on a coupon)


def leds(zb, rr, n=8):
    pts = [(0.0, 0.0, zb)]
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append((rr * math.cos(a), rr * math.sin(a), zb))
    return np.array(pts)


def wall_points(phi_o, n_theta=180, n_phi=72):
    th = np.linspace(phi_o + 1e-3, math.pi, n_theta)   # theta from the bottom pole
    ph = np.linspace(0, 2 * math.pi, n_phi, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing="ij")
    x = R * np.sin(T) * np.cos(P)
    y = R * np.sin(T) * np.sin(P)
    z = -R * np.cos(T)
    return th, np.stack([x, y, z], -1)


def direct(Pw, L):
    E = np.zeros(Pw.shape[:-1])
    for l in L:
        v = Pw - l                       # LED -> wall
        d2 = (v ** 2).sum(-1)
        d = np.sqrt(d2)
        cos_a = v[..., 2] / d            # LED normal +z
        n_in = -Pw / R                   # inward normal at wall
        cos_b = (-(v) * n_in).sum(-1) / d
        E += np.where((cos_a > 0) & (cos_b > 0), cos_a * cos_b / d2, 0.0)
    return E / len(L)


def run(phi_o_deg, zb, rr):
    phi_o = math.radians(phi_o_deg)
    th, Pw = wall_points(phi_o)
    L = leds(zb, rr)
    Ed = direct(Pw, L)
    # flux reaching wall (per unit I0), via ring-area weights
    dth = th[1] - th[0]
    w = 2 * math.pi * R ** 2 * np.sin(th) * dth / Pw.shape[1]
    phi_wall = (Ed * w[:, None]).sum()
    A_wall = 2 * math.pi * R ** 2 * (1 + math.cos(phi_o))
    f_wall = A_wall / (4 * math.pi * R ** 2)
    E_ind = RHO * phi_wall / (A_wall * (1 - RHO * f_wall))
    Et = Ed + E_ind
    prof = Et.mean(1)
    vis = th > math.radians(phi_o_deg + 10)   # ignore the 10 deg band hidden by the base rim
    return th, prof, prof[vis].max() / prof[vis].min(), phi_wall / math.pi


if __name__ == "__main__":
    out = pathlib.Path(__file__).with_suffix(".csv")
    rows = []
    for phi_o in (25.0, 30.0):
        z_open = -R * math.cos(math.radians(phi_o))
        for dz in (-4.0, -3.0, -2.0, -1.0, 0.0, 1.5, 3.0, 6.0, 10.0):
            zb = z_open + dz
            th, prof, U, eta = run(phi_o, zb, 6.5)
            rows.append([phi_o, round(zb, 2), round(dz, 2), round(U, 3), round(eta, 3)])
            print(f"opening {phi_o:4.1f} deg  board z={zb:6.2f} mm (dz {dz:+5.1f} from opening plane)"
                  f"  max/min wall illuminance {U:5.2f}   fraction of LED flux hitting wall {eta:4.2f}")
    with out.open("w", newline="") as f:
        csv.writer(f).writerows([["opening_deg", "board_z_mm", "dz_mm", "max_over_min", "flux_to_wall"]] + rows)
