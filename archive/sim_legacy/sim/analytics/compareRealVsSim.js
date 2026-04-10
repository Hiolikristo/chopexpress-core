#!/usr/bin/env node

/**
 * ChopExpress Real-vs-Sim Comparison Tool
 *
 * Compares:
 * - simulation summary JSON
 * against
 * - real driving CSV
 *
 * Real CSV expected columns:
 * date,platform,zone,hour,completed_orders,driver_pay,tips,total_miles,online_hours
 *
 * Example row:
 * 2026-03-08,DoorDash,Polaris,12,8,126.50,24.00,41.2,3.5
 *
 * Usage:
 *   node analytics/compareRealVsSim.js
 *   node analytics/compareRealVsSim.js "E:/ChopExpress/sim/output/latest_console_summary.json" "E:/ChopExpress/sim/input/real_driving_log.csv"
 */

const fs = require("fs");
const path = require("path");

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf8");
}

function writeText(filePath, text) {
  fs.writeFileSync(filePath, text, "utf8");
}

function round(value, digits = 2) {
  if (!Number.isFinite(value)) return 0;
  const factor = Math.pow(10, digits);
  return Math.round(value * factor) / factor;
}

function safeDivide(a, b) {
  if (!b || !Number.isFinite(a) || !Number.isFinite(b)) return 0;
  return a / b;
}

function toCurrency(value) {
  return `$${round(value, 2).toFixed(2)}`;
}

function toPercent(value) {
  return `${round(value * 100, 2).toFixed(2)}%`;
}

function parseCsv(text) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) return [];

  const headers = lines[0].split(",").map((h) => h.trim());
  const rows = [];

  for (let i = 1; i < lines.length; i += 1) {
    const values = lines[i].split(",").map((v) => v.trim());
    const row = {};
    for (let j = 0; j < headers.length; j += 1) {
      row[headers[j]] = values[j] ?? "";
    }
    rows.push(row);
  }

  return rows;
}

function normalizeOrders(summary) {
  if (Array.isArray(summary.orders)) return summary.orders;
  if (Array.isArray(summary.orderResults)) return summary.orderResults;
  return [];
}

function extractSimMetrics(summary) {
  const orders = normalizeOrders(summary);

  const totalOrders =
    summary.totalOrders ??
    summary.ordersGenerated ??
    summary.ordersCount ??
    orders.length ??
    0;

  const completedOrders =
    summary.completedOrdersCount ??
    summary.completed ??
    orders.filter((o) => (o.status || "").toLowerCase() === "completed").length;

  const unclaimedOrders =
    summary.unclaimedOrdersCount ??
    summary.unclaimed ??
    Math.max(0, totalOrders - completedOrders);

  const totalDriverPay =
    summary.totalDriverPay ??
    summary.driverPayTotal ??
    orders.reduce((sum, o) => sum + (Number(o.driverPay) || 0), 0);

  const totalTips =
    summary.totalTips ??
    summary.tipsTotal ??
    orders.reduce((sum, o) => sum + (Number(o.tip) || 0), 0);

  const totalMiles =
    summary.totalMiles ??
    summary.milesTotal ??
    orders.reduce((sum, o) => sum + (Number(o.totalMiles) || Number(o.miles) || 0), 0);

  const marketHours =
    summary.marketHours ??
    summary.windowHours ??
    summary.simulationHours ??
    0;

  return {
    totalOrders,
    completedOrders,
    unclaimedOrders,
    totalDriverPay,
    totalTips,
    totalMiles,
    marketHours,
    completionRate: round(safeDivide(completedOrders, totalOrders), 4),
    avgPayoutPerOrder: round(
      safeDivide(totalDriverPay + totalTips, completedOrders),
      2
    ),
    dollarsPerMile: round(
      safeDivide(totalDriverPay + totalTips, totalMiles),
      2
    ),
    hourlyEquivalent: round(
      safeDivide(totalDriverPay + totalTips, marketHours),
      2
    ),
  };
}

function extractRealMetrics(csvRows) {
  let completedOrders = 0;
  let totalDriverPay = 0;
  let totalTips = 0;
  let totalMiles = 0;
  let onlineHours = 0;

  const zones = new Map();
  const platforms = new Map();

  for (const row of csvRows) {
    const zone = row.zone || "UNKNOWN";
    const platform = row.platform || "UNKNOWN";

    const rowCompleted = Number(row.completed_orders) || 0;
    const rowPay = Number(row.driver_pay) || 0;
    const rowTips = Number(row.tips) || 0;
    const rowMiles = Number(row.total_miles) || 0;
    const rowHours = Number(row.online_hours) || 0;

    completedOrders += rowCompleted;
    totalDriverPay += rowPay;
    totalTips += rowTips;
    totalMiles += rowMiles;
    onlineHours += rowHours;

    if (!zones.has(zone)) {
      zones.set(zone, {
        zone,
        completedOrders: 0,
        totalDriverPay: 0,
        totalTips: 0,
        totalMiles: 0,
        onlineHours: 0,
      });
    }

    if (!platforms.has(platform)) {
      platforms.set(platform, {
        platform,
        completedOrders: 0,
        totalDriverPay: 0,
        totalTips: 0,
        totalMiles: 0,
        onlineHours: 0,
      });
    }

    const z = zones.get(zone);
    z.completedOrders += rowCompleted;
    z.totalDriverPay += rowPay;
    z.totalTips += rowTips;
    z.totalMiles += rowMiles;
    z.onlineHours += rowHours;

    const p = platforms.get(platform);
    p.completedOrders += rowCompleted;
    p.totalDriverPay += rowPay;
    p.totalTips += rowTips;
    p.totalMiles += rowMiles;
    p.onlineHours += rowHours;
  }

  const zoneBreakdown = Array.from(zones.values()).map((z) => ({
    zone: z.zone,
    completedOrders: z.completedOrders,
    totalDriverPay: round(z.totalDriverPay, 2),
    totalTips: round(z.totalTips, 2),
    totalMiles: round(z.totalMiles, 2),
    onlineHours: round(z.onlineHours, 2),
    avgPayoutPerOrder: round(
      safeDivide(z.totalDriverPay + z.totalTips, z.completedOrders),
      2
    ),
    dollarsPerMile: round(
      safeDivide(z.totalDriverPay + z.totalTips, z.totalMiles),
      2
    ),
    hourlyEquivalent: round(
      safeDivide(z.totalDriverPay + z.totalTips, z.onlineHours),
      2
    ),
  }));

  const platformBreakdown = Array.from(platforms.values()).map((p) => ({
    platform: p.platform,
    completedOrders: p.completedOrders,
    totalDriverPay: round(p.totalDriverPay, 2),
    totalTips: round(p.totalTips, 2),
    totalMiles: round(p.totalMiles, 2),
    onlineHours: round(p.onlineHours, 2),
    avgPayoutPerOrder: round(
      safeDivide(p.totalDriverPay + p.totalTips, p.completedOrders),
      2
    ),
    dollarsPerMile: round(
      safeDivide(p.totalDriverPay + p.totalTips, p.totalMiles),
      2
    ),
    hourlyEquivalent: round(
      safeDivide(p.totalDriverPay + p.totalTips, p.onlineHours),
      2
    ),
  }));

  return {
    completedOrders,
    totalDriverPay: round(totalDriverPay, 2),
    totalTips: round(totalTips, 2),
    totalMiles: round(totalMiles, 2),
    onlineHours: round(onlineHours, 2),
    avgPayoutPerOrder: round(
      safeDivide(totalDriverPay + totalTips, completedOrders),
      2
    ),
    dollarsPerMile: round(
      safeDivide(totalDriverPay + totalTips, totalMiles),
      2
    ),
    hourlyEquivalent: round(
      safeDivide(totalDriverPay + totalTips, onlineHours),
      2
    ),
    zoneBreakdown,
    platformBreakdown,
  };
}

function compareMetrics(sim, real) {
  return {
    avgPayoutPerOrder: {
      sim: sim.avgPayoutPerOrder,
      real: real.avgPayoutPerOrder,
      delta: round(sim.avgPayoutPerOrder - real.avgPayoutPerOrder, 2),
      verdict:
        sim.avgPayoutPerOrder > real.avgPayoutPerOrder
          ? "SIM HIGHER"
          : sim.avgPayoutPerOrder < real.avgPayoutPerOrder
          ? "REAL HIGHER"
          : "MATCHED",
    },
    dollarsPerMile: {
      sim: sim.dollarsPerMile,
      real: real.dollarsPerMile,
      delta: round(sim.dollarsPerMile - real.dollarsPerMile, 2),
      verdict:
        sim.dollarsPerMile > real.dollarsPerMile
          ? "SIM HIGHER"
          : sim.dollarsPerMile < real.dollarsPerMile
          ? "REAL HIGHER"
          : "MATCHED",
    },
    hourlyEquivalent: {
      sim: sim.hourlyEquivalent,
      real: real.hourlyEquivalent,
      delta: round(sim.hourlyEquivalent - real.hourlyEquivalent, 2),
      verdict:
        sim.hourlyEquivalent > real.hourlyEquivalent
          ? "SIM HIGHER"
          : sim.hourlyEquivalent < real.hourlyEquivalent
          ? "REAL HIGHER"
          : "MATCHED",
    },
  };
}

function buildInterpretation(sim, real, comparison) {
  const notes = [];

  if (comparison.avgPayoutPerOrder.delta > 0) {
    notes.push("ChopExpress simulated per-order payout exceeds observed real-market benchmark.");
  } else {
    notes.push("Observed real-market per-order payout meets or exceeds current simulation.");
  }

  if (comparison.dollarsPerMile.delta > 0) {
    notes.push("ChopExpress simulated $/mile is stronger than real driving results.");
  } else {
    notes.push("Real-market $/mile is stronger than current simulation assumptions.");
  }

  if (comparison.hourlyEquivalent.delta > 0) {
    notes.push("ChopExpress simulated hourly economics exceed real observed driving performance.");
  } else {
    notes.push("Real observed hourly performance exceeds current simulation output.");
  }

  if (sim.completionRate && sim.completionRate < 0.9) {
    notes.push("Even if payout is strong, sub-90% completion means operational reliability still limits pilot readiness.");
  }

  return notes;
}

function buildMarkdown(simPath, realPath, sim, real, comparison, interpretation) {
  const lines = [];
  lines.push("# ChopExpress Real-vs-Sim Comparison");
  lines.push("");
  lines.push(`**Simulation Source:** \`${simPath}\``);
  lines.push(`**Real Driving Source:** \`${realPath}\``);
  lines.push("");
  lines.push("## Core Comparison");
  lines.push("");
  lines.push("| Metric | ChopExpress Sim | Real Driving | Delta | Verdict |");
  lines.push("|---|---:|---:|---:|---|");
  lines.push(
    `| Avg Payout / Order | ${toCurrency(comparison.avgPayoutPerOrder.sim)} | ${toCurrency(comparison.avgPayoutPerOrder.real)} | ${toCurrency(comparison.avgPayoutPerOrder.delta)} | ${comparison.avgPayoutPerOrder.verdict} |`
  );
  lines.push(
    `| Dollars / Mile | ${toCurrency(comparison.dollarsPerMile.sim)} | ${toCurrency(comparison.dollarsPerMile.real)} | ${toCurrency(comparison.dollarsPerMile.delta)} | ${comparison.dollarsPerMile.verdict} |`
  );
  lines.push(
    `| Hourly Equivalent | ${toCurrency(comparison.hourlyEquivalent.sim)} | ${toCurrency(comparison.hourlyEquivalent.real)} | ${toCurrency(comparison.hourlyEquivalent.delta)} | ${comparison.hourlyEquivalent.verdict} |`
  );
  lines.push("");
  lines.push("## Simulation Snapshot");
  lines.push("");
  lines.push(`- Total Orders: **${sim.totalOrders}**`);
  lines.push(`- Completed Orders: **${sim.completedOrders}**`);
  lines.push(`- Unclaimed Orders: **${sim.unclaimedOrders}**`);
  lines.push(`- Completion Rate: **${toPercent(sim.completionRate)}**`);
  lines.push("");
  lines.push("## Real Driving Snapshot");
  lines.push("");
  lines.push(`- Completed Orders: **${real.completedOrders}**`);
  lines.push(`- Total Driver Pay: **${toCurrency(real.totalDriverPay)}**`);
  lines.push(`- Total Tips: **${toCurrency(real.totalTips)}**`);
  lines.push(`- Total Miles: **${real.totalMiles}**`);
  lines.push(`- Online Hours: **${real.onlineHours}**`);
  lines.push("");
  lines.push("## Interpretation");
  lines.push("");
  for (const note of interpretation) {
    lines.push(`- ${note}`);
  }
  lines.push("");
  lines.push("## Real Market by Platform");
  lines.push("");
  lines.push("| Platform | Orders | Avg Payout | $/Mile | Hourly |");
  lines.push("|---|---:|---:|---:|---:|");
  for (const row of real.platformBreakdown) {
    lines.push(
      `| ${row.platform} | ${row.completedOrders} | ${toCurrency(row.avgPayoutPerOrder)} | ${toCurrency(row.dollarsPerMile)} | ${toCurrency(row.hourlyEquivalent)} |`
    );
  }
  lines.push("");
  lines.push("## Real Market by Zone");
  lines.push("");
  lines.push("| Zone | Orders | Avg Payout | $/Mile | Hourly |");
  lines.push("|---|---:|---:|---:|---:|");
  for (const row of real.zoneBreakdown) {
    lines.push(
      `| ${row.zone} | ${row.completedOrders} | ${toCurrency(row.avgPayoutPerOrder)} | ${toCurrency(row.dollarsPerMile)} | ${toCurrency(row.hourlyEquivalent)} |`
    );
  }
  lines.push("");

  return lines.join("\n");
}

function main() {
  const simPath =
    process.argv[2] || "E:/ChopExpress/sim/output/latest_console_summary.json";
  const realPath =
    process.argv[3] || "E:/ChopExpress/sim/input/real_driving_log.csv";

  if (!fs.existsSync(simPath)) {
    console.error(`Simulation JSON not found: ${simPath}`);
    process.exit(1);
  }

  if (!fs.existsSync(realPath)) {
    console.error(`Real driving CSV not found: ${realPath}`);
    process.exit(1);
  }

  const simSummary = readJson(simPath);
  const simMetrics = extractSimMetrics(simSummary);

  const csvText = fs.readFileSync(realPath, "utf8");
  const csvRows = parseCsv(csvText);
  const realMetrics = extractRealMetrics(csvRows);

  const comparison = compareMetrics(simMetrics, realMetrics);
  const interpretation = buildInterpretation(
    simMetrics,
    realMetrics,
    comparison
  );

  const outputDir = path.resolve(path.dirname(simPath), "comparison");
  ensureDir(outputDir);

  const result = {
    generatedAt: new Date().toISOString(),
    simulationSource: simPath,
    realDrivingSource: realPath,
    simulation: simMetrics,
    real: realMetrics,
    comparison,
    interpretation,
  };

  const markdown = buildMarkdown(
    simPath,
    realPath,
    simMetrics,
    realMetrics,
    comparison,
    interpretation
  );

  writeJson(path.join(outputDir, "real_vs_sim_comparison.json"), result);
  writeText(path.join(outputDir, "real_vs_sim_comparison.md"), markdown);

  console.log("Real-vs-sim comparison generated successfully.");
  console.log(`Simulation input: ${simPath}`);
  console.log(`Real driving input: ${realPath}`);
  console.log(`Output: ${outputDir}`);
}

main();