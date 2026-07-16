import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import os


def _draw_satellite(ax, x, y, color="#22d3ee"):
    """Draws one satellite icon (glow + body + panels + antenna) at (x, y)."""

    # Glow
    ax.scatter(x, y, s=450, color=color, alpha=0.15, zorder=5)

    # --- Satellite Body (two-tone for depth) ---
    body_back = plt.Rectangle(
        (x - 0.09, y - 0.065), 0.18, 0.13,
        color="#94a3b8", ec="white", linewidth=1.3, zorder=7
    )
    ax.add_patch(body_back)

    body_front = plt.Rectangle(
        (x - 0.09, y - 0.005), 0.18, 0.07,
        color="#e2e8f0", linewidth=0, zorder=8
    )
    ax.add_patch(body_front)

    # small blinking status light
    status_light = plt.Circle((x + 0.07, y + 0.05), 0.012, color="#f87171", zorder=9)
    ax.add_patch(status_light)

    # --- Solar Panels (with cell grid lines) ---
    PANEL_W = 0.22
    PANEL_H = 0.09
    PANEL_GAP = 0.035

    for side in (-1, 1):
        panel_x = x + side * (0.09 + PANEL_GAP) + (0 if side == 1 else -PANEL_W)

        panel = plt.Rectangle(
            (panel_x, y - 0.045), PANEL_W, PANEL_H,
            facecolor="#1e3a8a", edgecolor="#93c5fd", linewidth=1.2, zorder=6
        )
        ax.add_patch(panel)

        n_cells = 4
        for c in range(1, n_cells):
            cell_x = panel_x + (PANEL_W / n_cells) * c
            ax.plot(
                [cell_x, cell_x], [y - 0.045, y - 0.045 + PANEL_H],
                color="#93c5fd", linewidth=0.6, alpha=0.6, zorder=6
            )

    # --- Antenna ---
    ax.plot([x, x], [y - 0.065, y - 0.17], color="white", linewidth=1.4, zorder=7)

    dish = plt.Circle((x, y - 0.19), 0.022, color="gold", ec="#fde68a", linewidth=0.8, zorder=8)
    ax.add_patch(dish)


def draw_earth_and_orbit(satellites, moon_angle=0):
    """
    satellites: list of dicts, one per satellite, each shaped like:
        {
            "label": "LEO",
            "angle": 123.4,          # degrees
            "radius": 1.8,           # orbit radius on the plot
            "color": "#22d3ee",      # marker / orbit-path / trail color
            "trail": [(x, y), ...],  # optional, oldest -> newest, current pos NOT included
            "focused": True          # optional, draws a highlight ring if True
        }
    moon_angle: current angle (degrees) of the Moon along its own orbit.
    """

    fig, ax = plt.subplots(figsize=(7, 7))

    # -------------------------
    # SPACE BACKGROUND
    # -------------------------

    fig.patch.set_facecolor("#020617")
    ax.set_facecolor("#020617")

    # -------------------------
    # STAR FIELD
    # -------------------------

    np.random.seed(10)

    stars_x = np.random.uniform(-3.5, 3.5, 200)
    stars_y = np.random.uniform(-3.5, 3.5, 200)

    ax.scatter(stars_x, stars_y, color="white", s=5, alpha=0.8, zorder=1)

    # -------------------------
    # EARTH ATMOSPHERE GLOW
    # -------------------------

    atmosphere = plt.Circle((0, 0), 1.15, color="#22d3ee", alpha=0.18, zorder=2)
    ax.add_patch(atmosphere)

    # -------------------------
    # EARTH IMAGE
    # -------------------------

    image_path = os.path.join("images", "earth.png")

    if os.path.exists(image_path):
        earth_img = mpimg.imread(image_path)
        ax.imshow(earth_img, extent=(-1, 1, -1, 1), zorder=3)
    else:
        earth = plt.Circle((0, 0), 1, color="#1e90ff", ec="#7dd3fc", linewidth=2, zorder=3)
        ax.add_patch(earth)
        ax.text(0, 0, "\U0001F30D", fontsize=35, ha="center", va="center", zorder=4)

    # -------------------------
    # DAY / NIGHT SHADING (3D look)
    # -------------------------

    SUN_DIRECTION = 0  # degrees; the lit side faces this direction

    night_start = SUN_DIRECTION + 90
    night_end = SUN_DIRECTION + 270

    night_side = plt.matplotlib.patches.Wedge(
        (0, 0), 1.0, night_start, night_end,
        facecolor="black", alpha=0.45, zorder=4, linewidth=0
    )
    ax.add_patch(night_side)

    terminator_glow = plt.matplotlib.patches.Wedge(
        (0, 0), 1.0, night_start - 6, night_start + 6,
        facecolor="black", alpha=0.15, zorder=4, linewidth=0
    )
    ax.add_patch(terminator_glow)

    # -------------------------
    # ORBIT PATHS (one dashed ring per satellite radius)
    # -------------------------

    drawn_radii = set()
    for sat in satellites:
        r = sat["radius"]
        if r in drawn_radii:
            continue
        drawn_radii.add(r)

        orbit = plt.Circle(
            (0, 0), r, fill=False,
            color=sat.get("color", "#22d3ee"),
            linewidth=2, linestyle="--", alpha=0.5, zorder=4
        )
        ax.add_patch(orbit)

    # -------------------------
    # MOON ORBIT + MOON
    # -------------------------

    MOON_ORBIT_RADIUS = 3.1  # sits outside all satellite orbits (LEO/MEO/GEO)

    moon_orbit = plt.Circle(
        (0, 0), MOON_ORBIT_RADIUS, fill=False,
        color="gray", linewidth=1, linestyle=":", alpha=0.4, zorder=2
    )
    ax.add_patch(moon_orbit)

    moon_theta = np.deg2rad(moon_angle)
    moon_x = MOON_ORBIT_RADIUS * np.cos(moon_theta)
    moon_y = MOON_ORBIT_RADIUS * np.sin(moon_theta)

    ax.scatter(moon_x, moon_y, s=300, color="#d1d5db", alpha=0.15, zorder=3)

    moon = plt.Circle((moon_x, moon_y), 0.12, color="#cbd5e1", ec="#94a3b8", linewidth=1, zorder=4)
    ax.add_patch(moon)

    # -------------------------
    # GROUND STATION
    # -------------------------

    GROUND_STATION_ANGLE = -60  # fixed point on Earth's surface (degrees)

    gs_theta = np.deg2rad(GROUND_STATION_ANGLE)
    gs_x = 1.0 * np.cos(gs_theta)
    gs_y = 1.0 * np.sin(gs_theta)

    ax.scatter(gs_x, gs_y, s=150, color="#facc15", alpha=0.2, zorder=5)
    ax.scatter(gs_x, gs_y, s=60, color="#facc15", marker="^", edgecolors="white", linewidth=1, zorder=6)

    station_unit = np.array([gs_x, gs_y]) / np.linalg.norm([gs_x, gs_y])

    # -------------------------
    # PER-SATELLITE: trail, communication link, icon, label
    # -------------------------

    for sat in satellites:

        angle = sat["angle"]
        radius = sat["radius"]
        color = sat.get("color", "#22d3ee")
        label = sat.get("label", "")
        trail = sat.get("trail")
        focused = sat.get("focused", False)

        theta = np.deg2rad(angle)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        # --- Orbit trail (fading comet tail) ---
        if trail:
            n = len(trail)
            for i, (tx, ty) in enumerate(trail):
                progress = (i + 1) / n
                ax.scatter(
                    tx, ty, s=60 * progress, color=color,
                    alpha=0.15 + 0.55 * progress, zorder=5, edgecolors="none"
                )

        # --- Communication link (only when on the visible side of Earth) ---
        satellite_unit = np.array([x, y]) / np.linalg.norm([x, y])
        visibility = np.dot(station_unit, satellite_unit)

        if visibility > 0:
            ax.plot(
                [gs_x, x], [gs_y, y],
                color="#4ade80", linewidth=1.2, linestyle=(0, (2, 3)),
                alpha=0.4 + 0.6 * visibility, zorder=5
            )

        # --- Focus highlight ring (shows which satellite the telemetry panel is watching) ---
        if focused:
            highlight = plt.Circle(
                (x, y), 0.28, fill=False, color="white",
                linewidth=1.2, alpha=0.6, zorder=6
            )
            ax.add_patch(highlight)

        # --- Satellite icon ---
        _draw_satellite(ax, x, y, color=color)

        # --- Label ---
        if label:
            ax.text(
                x, y + 0.28, label, fontsize=9, color=color,
                ha="center", va="bottom", fontweight="bold", zorder=9
            )

    # -------------------------
    # GRAPH SETTINGS
    # -------------------------

    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-3.5, 3.5)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.set_title("ORBITVISION | SPACE SIMULATION", fontsize=16, color="white", fontweight="bold")

    return fig


if __name__ == "__main__":
    fig = draw_earth_and_orbit(
        satellites=[
            {"label": "LEO", "angle": 45, "radius": 1.8, "color": "#22d3ee", "focused": True},
            {"label": "MEO", "angle": 120, "radius": 2.3, "color": "#facc15"},
            {"label": "GEO", "angle": 200, "radius": 2.8, "color": "#a78bfa"},
        ],
        moon_angle=30
    )
    fig.savefig("orbit_test.png", dpi=150, facecolor=fig.get_facecolor())
    print("Saved orbit_test.png")