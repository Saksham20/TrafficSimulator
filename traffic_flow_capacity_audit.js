// node traffic_flow_capacity_audit.js
// Capacity is an approximate maximum observed discharge over the demand sweep,
// not a guaranteed flow or the capacity of a real Bengaluru road.
const model = require('./traffic_flow_model.js');
const rows = [];
for (const violations of [0, 25, 50, 75, 100]) {
  for (const demandPcuH of [6000, 9000, 12000, 18000, 24000]) {
    const sim = model.create({ demandPcuH, violations });
    for (let n = 0; n < 120 / model.DT; n++) model.step(sim);
    const start = sim.scenes.map(s => s.totalDepartedPcu);
    const queues = [0, 0];
    for (let n = 0; n < 480 / model.DT; n++) {
      model.step(sim);
      sim.scenes.forEach((s, i) => { if (s.pending.some(q => q.length > 0)) queues[i]++; });
    }
    const results = sim.scenes.map((s, i) => ({
      pcuH: +(3600 * (s.totalDepartedPcu - start[i]) / 480).toFixed(2),
      backlogFraction: +(queues[i] * model.DT / 480).toFixed(3)
    }));
    rows.push({ violations, demandPcuH, results });
  }
}
const capacity = [0, 25, 50, 75, 100].map(violations => ({ violations,
  upper: Math.max(...rows.filter(r => r.violations === violations).map(r => r.results[0].pcuH)),
  lower: Math.max(...rows.filter(r => r.violations === violations).map(r => r.results[1].pcuH))
}));
console.log(JSON.stringify({ protocol: '120 s warm-up, 480 s discharge, maximum observed across 6000/9000/12000/18000/24000 PCU/h; one deterministic seed', capacity, rows }, null, 2));
