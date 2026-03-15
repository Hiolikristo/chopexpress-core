import json
import os
from typing import Dict, Any


ZONE_LAYOUT = {
    "Polaris": {"x": 520, "y": 120},
    "Westerville": {"x": 610, "y": 180},
    "Easton": {"x": 640, "y": 320},
    "Clintonville": {"x": 430, "y": 260},
    "Gahanna": {"x": 720, "y": 380},
    "Downtown": {"x": 500, "y": 430},
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def compute_zone_visuals(zone_order_counts: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
    max_orders = max(zone_order_counts.values()) if zone_order_counts else 1
    visuals: Dict[str, Dict[str, Any]] = {}

    for zone, orders in zone_order_counts.items():
        ratio = orders / max_orders if max_orders > 0 else 0.0
        radius = round(28 + (ratio * 42), 2)

        red = int(255 * ratio)
        green = int(180 * (1 - ratio) + 40)
        blue = int(90 * (1 - ratio) + 30)

        opacity = round(clamp(0.35 + (ratio * 0.55), 0.35, 0.9), 2)

        visuals[zone] = {
            "orders": orders,
            "ratio": round(ratio, 4),
            "radius": radius,
            "color": f"rgba({red}, {green}, {blue}, {opacity})",
            "x": ZONE_LAYOUT.get(zone, {}).get("x", 100),
            "y": ZONE_LAYOUT.get(zone, {}).get("y", 100),
        }

    return visuals


def write_visual_map_outputs(
    result: Dict[str, Any],
    analytics_dir: str = os.path.join("sim", "analytics"),
) -> Dict[str, str]:
    os.makedirs(analytics_dir, exist_ok=True)

    zone_counts = result.get("zone_order_counts", {})
    visuals = compute_zone_visuals(zone_counts)

    json_path = os.path.join(analytics_dir, "visual_zone_map.json")
    html_path = os.path.join(analytics_dir, "visual_zone_map.html")

    payload = {
        "summary": {
            "orders": result.get("orders", 0),
            "miles": result.get("miles", 0.0),
            "total_pay": result.get("total_pay", 0.0),
            "pay_per_mile": result.get("pay_per_mile", 0.0),
        },
        "zones": visuals,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>ChopExpress Visual Zone Map</title>
  <style>
    body {{
      margin: 0;
      background: #0b1020;
      color: #f2f5ff;
      font-family: Arial, sans-serif;
    }}
    .wrap {{
      width: 100%;
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px;
    }}
    .top {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .card {{
      background: #121936;
      border: 1px solid #24305f;
      border-radius: 14px;
      padding: 14px 16px;
      min-width: 180px;
    }}
    .title {{
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 12px;
    }}
    .subtitle {{
      color: #c7d2ff;
      margin-bottom: 18px;
    }}
    canvas {{
      width: 100%;
      max-width: 1000px;
      background: linear-gradient(180deg, #101833 0%, #0a1125 100%);
      border: 1px solid #24305f;
      border-radius: 18px;
      display: block;
      margin: 0 auto 18px auto;
    }}
    .legend {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .legend-item {{
      background: #121936;
      border: 1px solid #24305f;
      border-radius: 12px;
      padding: 12px;
    }}
    .small {{
      color: #b6c2ef;
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="title">ChopExpress Visual Zone Map</div>
    <div class="subtitle">Lightweight market visualization for pilot and investor review.</div>

    <div class="top">
      <div class="card"><strong>Orders</strong><br>{payload["summary"]["orders"]}</div>
      <div class="card"><strong>Miles</strong><br>{payload["summary"]["miles"]}</div>
      <div class="card"><strong>Total Pay</strong><br>${payload["summary"]["total_pay"]}</div>
      <div class="card"><strong>Pay / Mile</strong><br>${payload["summary"]["pay_per_mile"]}</div>
    </div>

    <canvas id="map" width="1000" height="650"></canvas>

    <div class="legend" id="legend"></div>
  </div>

  <script>
    const data = {json.dumps(payload)};
    const canvas = document.getElementById("map");
    const ctx = canvas.getContext("2d");
    const legend = document.getElementById("legend");

    function drawBackground() {{
      ctx.fillStyle = "#0d1530";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.strokeStyle = "#20305c";
      ctx.lineWidth = 1;
      for (let x = 60; x < canvas.width; x += 80) {{
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }}
      for (let y = 60; y < canvas.height; y += 80) {{
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }}

      ctx.fillStyle = "#7f92d8";
      ctx.font = "16px Arial";
      ctx.fillText("North Columbus Pilot Market Layout (abstracted)", 28, 34);
    }}

    function drawLinks(zones) {{
      const links = [
        ["Polaris", "Westerville"],
        ["Polaris", "Clintonville"],
        ["Westerville", "Easton"],
        ["Easton", "Gahanna"],
        ["Clintonville", "Downtown"],
        ["Downtown", "Gahanna"],
        ["Easton", "Downtown"]
      ];

      ctx.strokeStyle = "rgba(120, 150, 255, 0.25)";
      ctx.lineWidth = 3;

      links.forEach(([a, b]) => {{
        if (!zones[a] || !zones[b]) return;
        ctx.beginPath();
        ctx.moveTo(zones[a].x, zones[a].y);
        ctx.lineTo(zones[b].x, zones[b].y);
        ctx.stroke();
      }});
    }}

    function drawZones(zones) {{
      Object.entries(zones).forEach(([zone, info]) => {{
        ctx.beginPath();
        ctx.arc(info.x, info.y, info.radius, 0, Math.PI * 2);
        ctx.fillStyle = info.color;
        ctx.fill();

        ctx.strokeStyle = "rgba(255,255,255,0.25)";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 16px Arial";
        ctx.fillText(zone, info.x - 34, info.y - info.radius - 10);

        ctx.font = "14px Arial";
        ctx.fillText(`${{info.orders}} orders`, info.x - 28, info.y + 5);
      }});
    }}

    function buildLegend(zones) {{
      legend.innerHTML = "";
      Object.entries(zones)
        .sort((a, b) => b[1].orders - a[1].orders)
        .forEach(([zone, info]) => {{
          const div = document.createElement("div");
          div.className = "legend-item";
          div.innerHTML = `
            <strong>${{zone}}</strong><br>
            Orders: ${{info.orders}}<br>
            Demand Ratio: ${{info.ratio}}<br>
            <span class="small">Bubble size reflects relative demand intensity.</span>
          `;
          legend.appendChild(div);
        }});
    }}

    drawBackground();
    drawLinks(data.zones);
    drawZones(data.zones);
    buildLegend(data.zones);
  </script>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "json_path": json_path,
        "html_path": html_path,
    }