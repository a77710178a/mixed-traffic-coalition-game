from __future__ import annotations

import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from common import APPROACHES, PROTOTYPE_ROOT, ensure_dirs, load_config


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

    nodes = ET.Element("nodes")
    ET.SubElement(nodes, "node", id="C", x="0.0", y="0.0", type="priority")
    ET.SubElement(nodes, "node", id="N0", x="0.0", y=str(length), type="dead_end")
    ET.SubElement(nodes, "node", id="E0", x=str(length), y="0.0", type="dead_end")
    ET.SubElement(nodes, "node", id="S0", x="0.0", y=str(-length), type="dead_end")
    ET.SubElement(nodes, "node", id="W0", x=str(-length), y="0.0", type="dead_end")

    edges = ET.Element("edges")
    edge_specs = [
        ("N_in", "N0", "C"), ("N_out", "C", "N0"),
        ("E_in", "E0", "C"), ("E_out", "C", "E0"),
        ("S_in", "S0", "C"), ("S_out", "C", "S0"),
        ("W_in", "W0", "C"), ("W_out", "C", "W0"),
    ]
    for edge_id, from_node, to_node in edge_specs:
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
    for origin, mapping in APPROACHES.items():
        for dest, dest_mapping in APPROACHES.items():
            if dest == origin:
                continue
            ET.SubElement(connections, "connection", from_=mapping["in"], to=dest_mapping["out"])
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
    return {"nodes": nod, "edges": edg, "connections": con, "network": net}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(PROTOTYPE_ROOT / "config" / "default_scenario.json"))
    args = parser.parse_args()
    outputs = generate_network(args.config)
    for key, path in outputs.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()

