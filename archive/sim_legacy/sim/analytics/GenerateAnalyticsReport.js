#!/usr/bin/env node

/**
 * ChopExpress Simulation Analytics Report Generator
 *
 * Reads simulation output JSON and produces:
 * - analytics_summary.json
 * - analytics_by_zone.json
 * - analytics_by_hour.json
 * - analytics_report.md
 *
 * Usage:
 *   node analytics/generateAnalyticsReport.js
 *   node analytics/generateAnalyticsReport.js "E:/ChopExpress/sim/output/latest_console_summary.json"
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

function getHourBucket(hourValue) {
  const hour = Math.max(0, Math.min(23, Math.floor(Number(hourValue) || 0)));
  return `${String(hour).padStart(2, "0")}:00`;
}

function normalizeOrdersFromSummary(summary) {
  if (Array.isArray(summary.orders)) return summary.orders;
  if (Array.isArray(summary.orderResults)) return summary.orderResults;
  if (Array.isArray(summary.completedOrders) || Array.isArray(summary.unclaimedOrders)) {
    const completed = Array.isArray(summary.completedOrders)
      ? summary.completedOrders.map((o) => ({ ...o, status: o.status || "completed" }))
      : [];
    const unclaimed = Array.isArray(summary.unclaimedOrders)
      ? summary.unclaimedOrders.map((o) => ({ ...o, status: o.status || "unclaimed" }))
      : [];
    return [...completed, ...unclaimed];
  }
  return [];
}

function detectTopLevelMetrics(summary, orders) {
  const totalOrders =
    summary.totalOrders ??
    summary.ordersGenerated ??
    summary.ordersCount ??
    orders.length ??
    0;

  const completedOrders =
    summary.completedOrdersCount ??
    summary.completed ??
    summary.fulfilled ??
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

  const driverCount =
    summary.totalDrivers ??
    summary.driverCount ??
    summary.drivers ??
    0;

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
    driverCount,
    marketHours,
  };
}

function buildZoneAnalytics(orders) {
  const zones = new Map();

  for (const order of orders) {
    const zone = order.zone || order.marketZone || order.pickupZone || "UNKNOWN";
    const status = (order.status || "unknown").toLowerCase();
    const driverPay = Number(order.driverPay) || 0;
    const tip = Number(order.tip) || 0;
    const miles = Number(order.totalMiles) || Number(order.miles) || 0;
    const createdHour =
      order.createdHour ??
      order.hour ??
      order.requestHour ??
      order.generatedHour ??
      0;

    if (!zones.has(zone)) {
      zones.set(zone, {
        zone,
        totalOrders: 0,
        completedOrders: 0,
        unclaimedOrders: 0,
        totalDriverPay: 0,
        totalTips: 0,
        totalMiles: 0,
        hours: {},
      });
    }

    const z = zones.get(zone);
    z.totalOrders += 1;
    if (status === "completed") z.completedOrders += 1;
    if (status === "unclaimed") z.unclaimedOrders += 1;
    z.totalDriverPay += driverPay;
    z.totalTips += tip;
    z.totalMiles += miles;

    const hourBucket = getHourBucket(createdHour);
    if (!z.hours[hourBucket]) {
      z.hours[hourBucket] = {
        totalOrders: 0,
        completedOrders: 0,
        unclaimedOrders: 0,
      };
    }
    z.hours[hourBucket].totalOrders += 1;
    if (status === "completed") z.hours[hourBucket].completedOrders += 1;
    if (status === "unclaimed") z.hours[hourBucket].unclaimedOrders += 1;
  }

  return Array.from(zones.values())
    .map((z) => {
      const completionRate = safeDivide(z.completedOrders, z.totalOrders);
      return {
        zone: z.zone,
        totalOrders: z.totalOrders,
        completedOrders: z.completedOrders,
        unclaimedOrders: z.unclaimedOrders,
        completionRate: round(completionRate, 4),
        completionRatePct: toPercent(completionRate),
        totalDriverPay: round(z.totalDriverPay, 2),
        totalTips: round(z.totalTips, 2),
        totalMiles: round(z.totalMiles, 2),
        avgPayoutPerCompletedOrder: round(
          safeDivide(z.totalDriverPay + z.totalTips, z.completedOrders),
          2
        ),
        avgMilesPerCompletedOrder: round(
          safeDivide(z.totalMiles, z.completedOrders),
          2
        ),
        dollarsPerMile: round(
          safeDivide(z.totalDriverPay + z.totalTips, z.totalMiles),
          2
        ),
        hourlyBreakdown: z.hours,
      };
    })
    .sort((a, b) => b.completionRate - a.completionRate);
}

function buildHourAnalytics(orders) {
  const hours = new Map();

  for (const order of orders) {
    const hour = getHourBucket(
      order.createdHour ??
        order.hour ??
        order.requestHour ??
        order.generatedHour ??
        0
    );

    const status = (order.status || "unknown").toLowerCase();
    const driverPay = Number(order.driverPay) || 0;
    const tip = Number(order.tip) || 0;
    const miles = Number(order.totalMiles) || Number(order.miles) || 0;

    if (!hours.has(hour)) {
      hours.set(hour, {
        hour,
        totalOrders: 0,
        completedOrders: 0,
        unclaimedOrders: 0,
        totalDriverPay: 0,
        totalTips: 0,
        totalMiles: 0,
      });
    }

    const h = hours.get(hour);
    h.totalOrders += 1;
    if (status === "completed") h.completedOrders += 1;
    if (status === "unclaimed") h.unclaimedOrders += 1;
    h.totalDriverPay += driverPay;
    h.totalTips += tip;
    h.totalMiles += miles;
  }

  return Array.from(hours.values())
    .map((h) => {
      const completionRate = safeDivide(h.completedOrders, h.totalOrders);
      return {
        hour: h.hour,
        totalOrders: h.totalOrders,
        completedOrders: h.completedOrders,
        unclaimedOrders: h.unclaimedOrders,
        completionRate: round(completionRate, 4),
        completionRatePct: toPercent(completionRate),
        totalDriverPay: round(h.totalDriverPay, 2),
        totalTips: round(h.totalTips, 2),
        totalMiles: round(h.totalMiles, 2),
        avgPayoutPerCompletedOrder: round(
          safeDivide(h.totalDriverPay + h.totalTips, h.completedOrders),
          2
        ),
        dollarsPerMile: round(
          safeDivide(h.totalDriverPay + h.totalTips, h.totalMiles),
          2
        ),
      };
    })
    .sort((a, b) => a.hour.localeCompare(b.hour));
}

function buildHeadlineAssessment(metrics, zoneAnalytics) {
  const completionRate = safeDivide(metrics.completedOrders, metrics.totalOrders);
  const avgPayout = safeDivide(
    metrics.totalDriverPay + metrics.totalTips,
    metrics.completedOrders
  );
  const dollarsPerMile = safeDivide(
    metrics.totalDriverPay + metrics.totalTips,
    metrics.totalMiles
  );
  const hourlyEquivalent = safeDivide(
    metrics.totalDriverPay + metrics.totalTips,
    metrics.marketHours
  );

  const strongestZone = zoneAnalytics[0] || null;
  const weakestZone = zoneAnalytics[zoneAnalytics.length - 1] || null;

  let operationalReadiness = "UNKNOWN";
  if (completionRate >= 0.9) operationalReadiness = "CONTROLLED PILOT READY";
  else if (completionRate >= 0.82) operationalReadiness = "PROMISING BUT NOT STABLE";
  else if (completionRate >= 0.7) operationalReadiness = "ECONOMICALLY STRONG / OPERATIONALLY CONSTRAINED";
  else operationalReadiness = "NOT READY";

  const diagnosis = [];
  if (completionRate < 0.9) {
    diagnosis.push("Completion rate is below launch-quality target.");
  }
  if (strongestZone && weakestZone) {
    const spread = strongestZone.completionRate - weakestZone.completionRate;
    if (spread > 0.1) {
      diagnosis.push("Zone imbalance is material; supply is not evenly distributed.");
    }
  }
  if (avgPayout >= 15) {
    diagnosis.push("Payout quality appears strong enough to support driver participation.");
  }
  if (dollarsPerMile >= 2.0) {
    diagnosis.push("Mileage economics are attractive on paper.");
  }
  if (completionRate < 0.8 && avgPayout >= 15) {
    diagnosis.push("Primary bottleneck is likely dispatch logic, driver placement, or offer reach rather than pay level alone.");
  }

  return {
    operationalReadiness,
    completionRate: round(completionRate, 4),
    completionRatePct: toPercent(completionRate),
    avgPayoutPerCompletedOrder: round(avgPayout, 2),
    hourlyEquivalent: round(hourlyEquivalent, 2),
    dollarsPerMile: round(dollarsPerMile, 2),
    strongestZone: strongestZone
      ? {
          zone: strongestZone.zone,
          completionRate: strongestZone.completionRate,
          completionRatePct: strongestZone.completionRatePct,
        }
      : null,
    weakestZone: weakestZone
      ? {
          zone: weakestZone.zone,
          completionRate: weakestZone.completionRate,
          completionRatePct: weakestZone.completionRatePct,
        }
      : null,
    diagnosis,
    recommendedNextPriorities: [
      "zone rebalancing",
      "adaptive surge by local undercoverage",
      "conditional fallback dispatch widening",
      "hour-by-hour pre-positioning of drivers",
      "unclaimed-order root cause logging",
    ],
  };
}

function buildMarkdownReport(inputFile, metrics, assessment, zoneAnalytics, hourAnalytics) {
  const lines = [];

  lines.push("# ChopExpress Simulation Analytics Report");
  lines.push("");
  lines.push(`**Source:** \`${inputFile}\``);
  lines.push("");
  lines.push("## Headline Metrics");
  lines.push("");
  lines.push(`- Total Orders: **${metrics.totalOrders}**`);
  lines.push(`- Completed Orders: **${metrics.completedOrders}**`);
  lines.push(`- Unclaimed Orders: **${metrics.unclaimedOrders}**`);
  lines.push(`- Completion Rate: **${assessment.completionRatePct}**`);
  lines.push(`- Total Driver Pay: **${toCurrency(metrics.totalDriverPay)}**`);
  lines.push(`- Total Tips: **${toCurrency(metrics.totalTips)}**`);
  lines.push(`- Total Miles: **${round(metrics.totalMiles, 2)}**`);
  lines.push(`- Avg Payout per Completed Order: **${toCurrency(assessment.avgPayoutPerCompletedOrder)}**`);
  lines.push(`- Hourly Equivalent: **${toCurrency(assessment.hourlyEquivalent)}**`);
  lines.push(`- Dollars per Mile: **${toCurrency(assessment.dollarsPerMile)}**`);
  lines.push(`- Operational Readiness: **${assessment.operationalReadiness}**`);
  lines.push("");
  lines.push("## Interpretation");
  lines.push("");
  for (const item of assessment.diagnosis) {
    lines.push(`- ${item}`);
  }
  lines.push("");
  if (assessment.strongestZone) {
    lines.push(
      `- Strongest Zone: **${assessment.strongestZone.zone}** at **${assessment.strongestZone.completionRatePct}** completion`
    );
  }
  if (assessment.weakestZone) {
    lines.push(
      `- Weakest Zone: **${assessment.weakestZone.zone}** at **${assessment.weakestZone.completionRatePct}** completion`
    );
  }
  lines.push("");
  lines.push("## Recommended Next Priorities");
  lines.push("");
  for (const item of assessment.recommendedNextPriorities) {
    lines.push(`- ${item}`);
  }
  lines.push("");
  lines.push("## Zone Breakdown");
  lines.push("");
  lines.push("| Zone | Orders | Completed | Unclaimed | Completion | Avg Payout | $/Mile |");
  lines.push("|---|---:|---:|---:|---:|---:|---:|");
  for (const zone of zoneAnalytics) {
    lines.push(
      `| ${zone.zone} | ${zone.totalOrders} | ${zone.completedOrders} | ${zone.unclaimedOrders} | ${zone.completionRatePct} | ${toCurrency(zone.avgPayoutPerCompletedOrder)} | ${toCurrency(zone.dollarsPerMile)} |`
    );
  }
  lines.push("");
  lines.push("## Hour Breakdown");
  lines.push("");
  lines.push("| Hour | Orders | Completed | Unclaimed | Completion | Avg Payout |");
  lines.push("|---|---:|---:|---:|---:|---:|");
  for (const hour of hourAnalytics) {
    lines.push(
      `| ${hour.hour} | ${hour.totalOrders} | ${hour.completedOrders} | ${hour.unclaimedOrders} | ${hour.completionRatePct} | ${toCurrency(hour.avgPayoutPerCompletedOrder)} |`
    );
  }
  lines.push("");

  return lines.join("\n");
}

function main() {
  const defaultInput = "E:/ChopExpress/sim/output/latest_console_summary.json";
  const inputFile = process.argv[2] || defaultInput;

  if (!fs.existsSync(inputFile)) {
    console.error(`Input file not found: ${inputFile}`);
    process.exit(1);
  }

  const summary = readJson(inputFile);
  const orders = normalizeOrdersFromSummary(summary);
  const metrics = detectTopLevelMetrics(summary, orders);
  const zoneAnalytics = buildZoneAnalytics(orders);
  const hourAnalytics = buildHourAnalytics(orders);
  const assessment = buildHeadlineAssessment(metrics, zoneAnalytics);

  const outputDir = path.resolve(path.dirname(inputFile), "analytics");
  ensureDir(outputDir);

  const summaryOutput = {
    sourceFile: inputFile,
    generatedAt: new Date().toISOString(),
    metrics: {
      ...metrics,
      completionRate: round(safeDivide(metrics.completedOrders, metrics.totalOrders), 4),
      completionRatePct: toPercent(safeDivide(metrics.completedOrders, metrics.totalOrders)),
      avgPayoutPerCompletedOrder: round(
        safeDivide(metrics.totalDriverPay + metrics.totalTips, metrics.completedOrders),
        2
      ),
      hourlyEquivalent: round(
        safeDivide(metrics.totalDriverPay + metrics.totalTips, metrics.marketHours),
        2
      ),
      dollarsPerMile: round(
        safeDivide(metrics.totalDriverPay + metrics.totalTips, metrics.totalMiles),
        2
      ),
    },
    assessment,
  };

  const markdown = buildMarkdownReport(
    inputFile,
    metrics,
    assessment,
    zoneAnalytics,
    hourAnalytics
  );

  writeJson(path.join(outputDir, "analytics_summary.json"), summaryOutput);
  writeJson(path.join(outputDir, "analytics_by_zone.json"), zoneAnalytics);
  writeJson(path.join(outputDir, "analytics_by_hour.json"), hourAnalytics);
  writeText(path.join(outputDir, "analytics_report.md"), markdown);

  console.log("Analytics report generated successfully.");
  console.log(`Input:  ${inputFile}`);
  console.log(`Output: ${outputDir}`);
}

main();