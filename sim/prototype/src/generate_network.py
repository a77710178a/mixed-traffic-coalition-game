from __future__ import annotations

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import PROTOTYPE_ROOT, ensure_dirs, load_config
from route_geometry import write_route_geometry
from topology import active_approaches, connection_specs, edge_specs, node_specs


def _indent(tree: ET.ElementTree) -> None:
    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass


def write_xml(path: Path, root: ET.Element) -> None:
    tree = ET.ElementTree(root)
    _indent(tree)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def generate_network(config_path: str) -> dict[str, Path]:
    cfg = load_config(config_path)
    ensure_dirs()
    network_dir = PROTOTYPE_ROOT / "networks"
    length = float(cfg["approach_length_m"])
    speed = float(cfg["speed_limit_mps"])
    approaches = active_approaches(cfg)

    nodes = ET.Element("nodes")
    for node_id, x, y in node_specs(approaches, length):
        node_type = "priority" if node_id == "C" else "dead_end"
        ET.SubElement(nodes, "node", id=node_id, x=str(x), y=str(y), type=node_type)

    edges = ET.Element("edges")
    for edge_id, from_node, to_node in edge_specs(approaches):
        ET.SubElement(
            edges,
            "edge",
            id=edge_id,
            from_=from_node,
            to=to_node,
            numLanes="1",
            speed=f"{speed:.2f}",
        )
    for edge in edges:
        edge.attrib["from"] = edge.attrib.pop("from_")

    connections = ET.Element("connections")
    for from_edge, to_edge in connection_specs(approaches):
        ET.SubElement(connections, "connection", from_=from_edge, to=to_edge)
    for conn in connections:
        conn.attrib["from"] = conn.attrib.pop("from_")

    nod = network_dir / "four_leg.nod.xml"
    edg = network_dir / "four_leg.edg.xml"
    con = network_dir / "four_leg.con.xml"
    net = network_dir / "four_leg.net.xml"
    write_xml(nod, nodes)
    write_xml(edg, edges)
    write_xml(con, connections)

    cmd = [
        "netconvert",
        "--node-files", str(nod),
        "--edge-files", str(edg),
        "--connection-files", str(con),
        "--output-file", str(net),
        "--junctions.join", "false",
        "--no-turnarounds", "true",
    ]
    subprocess.run(cmd, check=True)
    outputs = {"nodes": nod, "edges": edg, "connections": con, "network": net}
    if cfg.get("geometry_mode"):
        outputs["route_geometry"] = write_route_geometry(cfg)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "default_scenario.json"))
    args = parser.parse_args()
    outputs = generate_network(args.config)
    for key, path in outputs.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
