from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

from common import PROTOTYPE_ROOT, load_config
from route_geometry import build_route_geometry
from topology import active_approaches, route_specs


def _svg_arrow(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 3.0) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width}" marker-end="url(#arrow)" />'
    )


def _scale(
    point: tuple[float, float],
    origin: tuple[float, float],
    canvas: int,
    margin: int,
    length: float,
) -> tuple[float, float]:
    x, y = point
    origin_x, origin_y = origin
    factor = (canvas / 2 - margin) / length
    return canvas / 2 + (x - origin_x) * factor, canvas / 2 - (y - origin_y) * factor


def _road_lines(approaches: tuple[str, ...], points: dict[str, tuple[float, float]], center: tuple[float, float]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    lines = []
    if "N" in approaches and "S" in approaches:
        lines.append((points["N"], points["S"]))
    if "E" in approaches and "W" in approaches:
        lines.append((points["W"], points["E"]))
    for approach in approaches:
        if not any(points[approach] in line for line in lines):
            lines.append((points[approach], center))
    return lines


def _label_offset(approach: str) -> tuple[float, float]:
    return {
        "N": (0.0, -42.0),
        "E": (54.0, 38.0),
        "S": (0.0, 68.0),
        "W": (-54.0, 38.0),
    }[approach]


def _approach_arrow(point: tuple[float, float], center: tuple[float, float], color: str, inbound: bool) -> str:
    px, py = point
    cx, cy = center
    dx = cx - px
    dy = cy - py
    length = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / length, dy / length
    if inbound:
        start = (px + ux * 58.0, py + uy * 58.0)
        end = (cx - ux * 35.0, cy - uy * 35.0)
    else:
        start = (cx + ux * 35.0, cy + uy * 35.0)
        end = (px - ux * 58.0, py - uy * 58.0)
    return _svg_arrow(start[0], start[1], end[0], end[1], color, 4)


def _route_geometry_overlay(cfg: dict, canvas: int, margin: int, length: float) -> str:
    if not cfg.get("geometry_mode"):
        return ""
    geometry = build_route_geometry(cfg)
    elements = []
    for zone in geometry.get("zones", []):
        center = zone.get("centroid", {})
        x, y = _scale((float(center["x"]), float(center["y"])), (0.0, 0.0), canvas, margin, length)
        radius_px = float(zone["radius_m"]) * (canvas / 2 - margin) / length
        label = "/".join(zone["route_ids"])
        elements.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius_px:.1f}" fill="#fca5a5" stroke="#b91c1c" stroke-width="2" opacity="0.55" />'
        )
        elements.append(
            f'<text x="{x:.1f}" y="{y - radius_px - 4:.1f}" text-anchor="middle" font-family="Arial" font-size="10" fill="#7f1d1d">{label}</text>'
        )

    if not elements:
        return ""
    return "\n  ".join(
        [
            '<g id="route-geometry-zones">',
            '<text x="450" y="96" text-anchor="middle" font-family="Arial" font-size="13" fill="#7f1d1d">route geometry zones</text>',
            *elements,
            "</g>",
        ]
    )


def render_preview(config_path: str | Path, net_path: str | Path, output_path: str | Path) -> Path:
    cfg = load_config(config_path)
    approaches = active_approaches(cfg)
    length = float(cfg["approach_length_m"])
    radius = float(cfg["conflict_zones"][0]["radius_m"])
    canvas = 900
    margin = 155
    center = (canvas / 2, canvas / 2)

    tree = ET.parse(net_path)
    nodes = {}
    for node in tree.getroot().iter("junction"):
        node_id = node.attrib.get("id", "")
        if node_id == "C" or node_id in {f"{approach}0" for approach in approaches}:
            nodes[node_id] = (float(node.attrib["x"]), float(node.attrib["y"]))

    center_origin = nodes["C"]

    def p(node_id: str) -> tuple[float, float]:
        return _scale(nodes[node_id], center_origin, canvas, margin, length)

    c = p("C")
    radius_px = radius * (canvas / 2 - margin) / length
    route_points = {
        approach: p(f"{approach}0")
        for approach in approaches
    }
    road_lines = _road_lines(approaches, route_points, c)

    colors = {
        "left": "#ef4444",
        "through": "#2563eb",
        "right": "#16a34a",
    }
    curves = []
    for spec in route_specs(approaches):
        x1, y1 = route_points[spec.origin]
        x2, y2 = route_points[spec.destination]
        cx, cy = c
        curves.append(
            f'<path class="route-example" data-route-id="{spec.route_id}" d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" '
            f'fill="none" stroke="{colors.get(spec.movement, "#7c3aed")}" stroke-width="2.5" stroke-dasharray="8 8" marker-end="url(#arrow)" />'
        )

    road_svg = "\n  ".join(
        f'<line x1="{start[0]:.1f}" y1="{start[1]:.1f}" x2="{end[0]:.1f}" y2="{end[1]:.1f}" stroke="#334155" stroke-width="34" stroke-linecap="round" />'
        for start, end in road_lines
    )
    lane_svg = "\n  ".join(
        f'<line x1="{start[0]:.1f}" y1="{start[1]:.1f}" x2="{end[0]:.1f}" y2="{end[1]:.1f}" stroke="#e2e8f0" stroke-width="3" stroke-dasharray="16 14" />'
        for start, end in road_lines
    )
    arrow_svg = "\n  ".join(
        _approach_arrow(route_points[approach], c, "#f97316", inbound=True)
        + "\n  "
        + _approach_arrow(route_points[approach], c, "#0ea5e9", inbound=False)
        for approach in approaches
    )
    label_svg = "\n  ".join(
        f'<text x="{route_points[approach][0] + _label_offset(approach)[0]:.1f}" y="{route_points[approach][1] + _label_offset(approach)[1]:.1f}" text-anchor="middle" font-family="Arial" font-size="24" font-weight="700">{approach}</text>'
        for approach in approaches
    )
    geometry_overlay_svg = _route_geometry_overlay(cfg, canvas, margin, length)
    title = "T-junction Unsignalized Intersection Preview" if len(approaches) == 3 else "Four-leg Unsignalized Intersection Preview"
    approach_text = ", ".join(approaches)

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{canvas}" height="{canvas}" viewBox="0 0 {canvas} {canvas}">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#111827" />
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="450" y="42" text-anchor="middle" font-family="Arial" font-size="26" font-weight="700" fill="#111827">{title}</text>
  <text x="450" y="72" text-anchor="middle" font-family="Arial" font-size="15" fill="#475569">active approaches: {approach_text}; one incoming lane and one outgoing lane per approach</text>

  {road_svg}
  {lane_svg}
  {arrow_svg}

  <circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{radius_px:.1f}" fill="#fef3c7" stroke="#d97706" stroke-width="3" opacity="0.85" />
  <text x="{c[0]:.1f}" y="{c[1] + 5:.1f}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700" fill="#92400e">conflict zone</text>
  {geometry_overlay_svg}

  {' '.join(curves)}

  {label_svg}

  <rect x="42" y="764" width="330" height="98" rx="6" fill="#ffffff" stroke="#cbd5e1" />
  <text x="62" y="792" font-family="Arial" font-size="15" font-weight="700" fill="#111827">Current scenario</text>
  <text x="62" y="816" font-family="Arial" font-size="13" fill="#334155">approach length: {length:.0f} m</text>
  <text x="62" y="838" font-family="Arial" font-size="13" fill="#334155">speed limit: {float(cfg["speed_limit_mps"]):.2f} m/s</text>
  <text x="62" y="860" font-family="Arial" font-size="13" fill="#334155">stress conflict radius: {radius:.0f} m</text>

  <rect x="548" y="764" width="310" height="98" rx="6" fill="#ffffff" stroke="#cbd5e1" />
  <text x="568" y="792" font-family="Arial" font-size="15" font-weight="700" fill="#111827">Movement examples</text>
  <text x="568" y="816" font-family="Arial" font-size="13" fill="#ef4444">red dashed: left turn</text>
  <text x="568" y="838" font-family="Arial" font-size="13" fill="#2563eb">blue dashed: through</text>
  <text x="568" y="860" font-family="Arial" font-size="13" fill="#16a34a">green dashed: right turn</text>
</svg>
'''
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "stress_scenario.json"))
    parser.add_argument("--net", default=str(PROTOTYPE_ROOT / "networks" / "four_leg.net.xml"))
    parser.add_argument("--output", default=str(PROTOTYPE_ROOT / "reports" / "four_leg_network_preview.svg"))
    args = parser.parse_args()
    print(render_preview(args.config, args.net, args.output))


if __name__ == "__main__":
    main()
