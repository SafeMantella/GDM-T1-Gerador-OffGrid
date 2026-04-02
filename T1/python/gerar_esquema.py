"""
gerar_esquema.py - Diagrama de blocos do sistema GD-FV com MPPT
Layout: barramento CC no topo, blocos abaixo, MPPT no rodapé
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Arc
from pathlib import Path

OUT_DIR  = Path(__file__).parent.parent / "figuras"
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE = OUT_DIR / "fig00_esquema_sistema.png"

# ── Cores ────────────────────────────────────────────────────────────────
C = dict(
    bg    = "#F4F6F8",
    pv    = "#1A6B9A",
    conv  = "#C0392B",
    mppt  = "#1E8449",
    bat   = "#CA6F1E",
    load  = "#5D6D7E",
    inmet = "#6C3483",
    bus   = "#1C2833",
    arrow = "#424949",
)

fig, ax = plt.subplots(figsize=(16, 8.5))
ax.set_xlim(0, 16); ax.set_ylim(0, 8.5)
ax.axis("off")
fig.patch.set_facecolor(C["bg"])
ax.set_facecolor(C["bg"])

# ── Utilidades ────────────────────────────────────────────────────────────

def bloco(x, y, w, h, cor, titulo, sub="", fs=12):
    ax.add_patch(FancyBboxPatch((x+.09, y-.09), w, h,
        boxstyle="round,pad=0,rounding_size=.3",
        fc="#00000018", ec="none", zorder=2))
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0,rounding_size=.3",
        fc=cor, ec="white", lw=2, zorder=3))
    dy = .18 if sub else 0
    ax.text(x+w/2, y+h/2+dy, titulo,
            ha="center", va="center", fontsize=fs,
            fontweight="bold", color="white", zorder=4)
    if sub:
        ax.text(x+w/2, y+h/2-.30, sub,
                ha="center", va="center", fontsize=9.5,
                color="white", alpha=.90, zorder=4)


def seta_v(x, y1, y2, cor, lw=2.0, label="", lado="right"):
    """Seta vertical de y1 → y2."""
    dy = .02 if y2 > y1 else -.02
    ax.annotate("", xy=(x, y2-dy), xytext=(x, y1+dy),
        arrowprops=dict(arrowstyle="-|>", color=cor, lw=lw, mutation_scale=16),
        zorder=6)
    if label:
        off = .35 if lado == "right" else -.35
        ax.text(x+off, (y1+y2)/2, label,
                ha="left" if lado=="right" else "right",
                va="center", fontsize=8.5, color=cor, style="italic",
                zorder=7, bbox=dict(fc=C["bg"], ec="none", pad=1.5))


def seta_h(x1, x2, y, cor, lw=2.0, label="", lado="top"):
    """Seta horizontal de x1 → x2."""
    dx = .02 if x2 > x1 else -.02
    ax.annotate("", xy=(x2-dx, y), xytext=(x1+dx, y),
        arrowprops=dict(arrowstyle="-|>", color=cor, lw=lw, mutation_scale=16),
        zorder=6)
    if label:
        off = .22 if lado == "top" else -.25
        ax.text((x1+x2)/2, y+off, label,
                ha="center", va="center", fontsize=8.5,
                color=cor, style="italic", zorder=7,
                bbox=dict(fc=C["bg"], ec="none", pad=1.5))


def linha_v(x, y1, y2, cor, lw=2.0, ls="-"):
    ax.plot([x, x], [y1, y2], color=cor, lw=lw, ls=ls,
            zorder=5, solid_capstyle="round")


def linha_h(x1, x2, y, cor, lw=2.0, ls="-"):
    ax.plot([x1, x2], [y, y], color=cor, lw=lw, ls=ls,
            zorder=5, solid_capstyle="round")


# ══════════════════════════════════════════════════════════════════════════
# TÍTULO
# ══════════════════════════════════════════════════════════════════════════
ax.text(8, 8.20,
        "Sistema de Geração Distribuída Fotovoltaica - 200 Wp\n"
        "Estação INMET A702  •  Campo Grande / MS  •  2025",
        ha="center", va="center", fontsize=13, fontweight="bold",
        color=C["bus"],
        bbox=dict(fc="white", ec="#CCCCCC", boxstyle="round,pad=.4", lw=1.2))

# ══════════════════════════════════════════════════════════════════════════
# BARRAMENTO CC (linha horizontal no topo)
# ══════════════════════════════════════════════════════════════════════════
BUS_Y = 6.85
BUS_X1, BUS_X2 = 1.8, 14.6
ax.plot([BUS_X1, BUS_X2], [BUS_Y,     BUS_Y    ], color=C["bus"], lw=5, zorder=4, solid_capstyle="round")
ax.plot([BUS_X1, BUS_X2], [BUS_Y-.20, BUS_Y-.20], color=C["bus"], lw=1.5, zorder=4, alpha=.5, solid_capstyle="round")
ax.text(8, BUS_Y+.35, "Barramento CC  -  48 V",
        ha="center", va="center", fontsize=10, fontweight="bold", color=C["bus"])

# ══════════════════════════════════════════════════════════════════════════
# 1. PAINEL FV  (x ≈ 0.6-3.6)
# ══════════════════════════════════════════════════════════════════════════
PV_X, PV_Y, PV_W, PV_H = 0.6, 3.3, 3.0, 3.0
bloco(PV_X, PV_Y, PV_W, PV_H, C["pv"], "Painel FV", "200 Wp", fs=13)

# Grade de células
for xi in np.linspace(PV_X+.3, PV_X+PV_W-.3, 5):
    ax.plot([xi,xi],[PV_Y+.3, PV_Y+PV_H-.3], color="white", lw=.7, alpha=.28, zorder=4)
for yi in np.linspace(PV_Y+.3, PV_Y+PV_H-.3, 5):
    ax.plot([PV_X+.3,PV_X+PV_W-.3],[yi,yi], color="white", lw=.7, alpha=.28, zorder=4)

ax.text(PV_X+PV_W/2, PV_Y-.42,
        r"$V_{oc}=32{,}9\,\mathrm{V}\quad I_{sc}=8{,}21\,\mathrm{A}$",
        ha="center", va="center", fontsize=8.5, color=C["pv"],
        bbox=dict(fc="white", ec="#AAAAAA", pad=2.5, lw=.8))

# Seta PV → barramento
PV_MX = PV_X + PV_W/2
linha_v(PV_MX, PV_Y+PV_H, BUS_Y, C["pv"])
seta_v(PV_MX, PV_Y+PV_H-.01, BUS_Y+.01, C["pv"], label=r"$i_{pv},\;V_{pv}$", lado="right")

# ══════════════════════════════════════════════════════════════════════════
# 2. CONVERSOR BUCK-BOOST  (x ≈ 5.5-9.0)
# ══════════════════════════════════════════════════════════════════════════
CO_X, CO_Y, CO_W, CO_H = 5.4, 3.3, 3.6, 3.0
bloco(CO_X, CO_Y, CO_W, CO_H, C["conv"], "Conversor", "Buck-Boost", fs=13)

# Símbolo indutor
for xi in [6.1, 6.45, 6.80]:
    ax.add_patch(Arc((xi, 4.70), .32, .32, angle=0, theta1=0, theta2=180,
                     color="white", lw=1.8, zorder=5))
ax.text(6.5, 4.30, "L", color="white", fontsize=9.5, ha="center",
        alpha=.8, zorder=5)
# Capacitor
for yc in [4.65, 4.90]:
    ax.plot([7.5, 8.1],[yc, yc], color="white", lw=2.0, zorder=5, alpha=.8)
ax.text(7.8, 4.25, "C", color="white", fontsize=9.5, ha="center",
        alpha=.8, zorder=5)

# Seta conversor → barramento
CO_MX = CO_X + CO_W/2
linha_v(CO_MX, CO_Y+CO_H, BUS_Y, C["conv"])
seta_v(CO_MX, CO_Y+CO_H-.01, BUS_Y+.01, C["conv"], label=r"$V_{dc}$", lado="right")

# ══════════════════════════════════════════════════════════════════════════
# 3. CONTROLADOR MPPT  (abaixo do conversor)
# ══════════════════════════════════════════════════════════════════════════
MP_X, MP_Y, MP_W, MP_H = 5.2, 0.6, 4.0, 1.8
bloco(MP_X, MP_Y, MP_W, MP_H, C["mppt"], "Controlador MPPT", "P&O  |  Beta (β)", fs=12)

# Seta I_ref: MPPT → conversor
MP_MX = MP_X + MP_W/2
seta_v(CO_MX, MP_Y+MP_H, CO_Y, C["mppt"], lw=2.0,
       label=r"$I_{ref}$", lado="left")

# Seta medição: nó entrada conversor → MPPT (v_pv, i_pv)
MEAS_X = CO_X + .55
linha_v(MEAS_X, CO_Y, MP_Y+MP_H, C["arrow"], lw=1.4, ls="--")
ax.annotate("", xy=(MEAS_X, MP_Y+MP_H+.02), xytext=(MEAS_X, CO_Y-.02),
    arrowprops=dict(arrowstyle="-|>", color=C["arrow"], lw=1.4, mutation_scale=14),
    zorder=6)
ax.text(MEAS_X-.38, (CO_Y+MP_Y+MP_H)/2,
        r"$V_{pv},\;I_{pv}$",
        ha="right", va="center", fontsize=8.5, color=C["arrow"],
        style="italic", bbox=dict(fc=C["bg"], ec="none", pad=1.5))

# ══════════════════════════════════════════════════════════════════════════
# 4. BANCO DE BATERIAS  (x ≈ 10.5-13.5)
# ══════════════════════════════════════════════════════════════════════════
BA_X, BA_Y, BA_W, BA_H = 10.5, 3.3, 3.0, 3.0
bloco(BA_X, BA_Y, BA_W, BA_H, C["bat"], "Bateria", "48 V / 100 Ah", fs=13)

# Símbolo bateria
for yb, lw_b in [(5.5,.8),(5.25,2.2),(5.0,.8),(4.75,2.2),(4.5,.8)]:
    ax.plot([10.9, 13.1],[yb,yb], color="white", lw=lw_b, alpha=.65, zorder=5)
ax.text(10.72, 5.62, "+", color="white", fontsize=11, fontweight="bold",
        ha="center", zorder=6, alpha=.9)
ax.text(10.72, 4.36, "−", color="white", fontsize=14, fontweight="bold",
        ha="center", zorder=6, alpha=.9)

ax.text(BA_X+BA_W/2, BA_Y-.42,
        r"$\eta=95\%\quad SOC_0=50\%\quad[20\%-100\%]$",
        ha="center", va="center", fontsize=8.5, color=C["bat"],
        bbox=dict(fc="white", ec="#AAAAAA", pad=2.5, lw=.8))

# Seta barramento → bateria
BA_MX = BA_X + BA_W/2
linha_v(BA_MX, BUS_Y, BA_Y+BA_H, C["bat"])
seta_v(BA_MX, BUS_Y-.01, BA_Y+BA_H+.01, C["bat"], label=r"$P_{bat}$", lado="right")

# Seta feedback SOC → MPPT (tracejada, curvada)
ax.annotate("", xy=(MP_X+MP_W-.3, MP_Y+.5), xytext=(BA_MX, BA_Y-.01),
    arrowprops=dict(arrowstyle="-|>", color=C["bat"], lw=1.4,
                    connectionstyle="arc3,rad=0.35", linestyle="dashed"),
    zorder=5)
ax.text(10.1, 1.55, "SOC",
        ha="center", va="center", fontsize=8.5, color=C["bat"],
        style="italic", bbox=dict(fc=C["bg"], ec="none", pad=1.5))

# ══════════════════════════════════════════════════════════════════════════
# 5. CARGA DC  (x ≈ 13.5-15.5)
# ══════════════════════════════════════════════════════════════════════════
LD_X, LD_Y, LD_W, LD_H = 13.6, 3.6, 2.0, 2.4
bloco(LD_X, LD_Y, LD_W, LD_H, C["load"], "Carga", "DC", fs=12)

# Zigzag
zx = np.array([13.9,14.02,14.15,14.28,14.41,14.54,14.67,14.80,14.93])
zy = np.array([4.8, 5.10, 4.50, 5.10, 4.50, 5.10, 4.50, 5.10, 4.80])
ax.plot(zx, zy, color="white", lw=1.8, alpha=.7, zorder=5)

# Seta barramento → carga
LD_MX = LD_X + LD_W/2
linha_v(LD_MX, BUS_Y, LD_Y+LD_H, C["load"])
seta_v(LD_MX, BUS_Y-.01, LD_Y+LD_H+.01, C["load"],
       label=r"$P_{load}$", lado="right")

# ══════════════════════════════════════════════════════════════════════════
# 6. INMET A702  (entrada climática, acima do painel)
# ══════════════════════════════════════════════════════════════════════════
IN_X, IN_Y, IN_W, IN_H = 0.3, 7.15, 3.2, .90
bloco(IN_X, IN_Y, IN_W, IN_H, C["inmet"],
      "INMET A702", r"G [W/m²]  |  $T_{amb}$ [°C]", fs=9.5)

# Sol
sx, sy = 1.88, 7.62
for ang in np.linspace(0, 2*np.pi, 9)[:-1]:
    ax.plot([sx+.42*np.cos(ang), sx+.56*np.cos(ang)],
            [sy+.42*np.sin(ang), sy+.56*np.sin(ang)],
            color="#FFD166", lw=2.0, zorder=5)
ax.add_patch(plt.Circle((sx, sy), .32, color="#FFD166", zorder=5))

# Seta INMET → painel
ax.annotate("", xy=(PV_MX, PV_Y+PV_H+.02), xytext=(PV_MX, IN_Y-.02),
    arrowprops=dict(arrowstyle="-|>", color=C["inmet"], lw=1.8,
                    mutation_scale=14),
    zorder=6)

# ══════════════════════════════════════════════════════════════════════════
# Legenda
# ══════════════════════════════════════════════════════════════════════════
legend_handles = [
    mpatches.Patch(fc=C["pv"],    label="Painel FV (200 Wp)"),
    mpatches.Patch(fc=C["conv"],  label="Conversor Buck-Boost"),
    mpatches.Patch(fc=C["mppt"],  label="Controlador MPPT"),
    mpatches.Patch(fc=C["bat"],   label="Banco de Baterias"),
    mpatches.Patch(fc=C["load"],  label="Carga DC"),
    mpatches.Patch(fc=C["inmet"], label="Dados INMET A702"),
]
ax.legend(handles=legend_handles, loc="lower center",
          ncol=6, fontsize=9, framealpha=.97,
          bbox_to_anchor=(.5, -.01),
          edgecolor="#CCCCCC", columnspacing=1.2, handlelength=1.2)

plt.tight_layout(pad=.4)
fig.savefig(OUT_FILE, dpi=200, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
plt.close(fig)
print(f"[salvo] {OUT_FILE}")
