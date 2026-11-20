// Run with: node --test traffic_flow_model.test.js
const { test } = require('node:test');
const assert = require('node:assert/strict');
const model = require('./traffic_flow_model.js');

function car(overrides = {}) {
  return { id: 1, dir: 0, u: 20, y: 3.7, type: model.types.car, speed: 5,
    vy: 0, v0: 10, headway: .85, ...overrides };
}

test('travel time uses boundary crossings, scales by distance, and counts admitted cars', () => {
  const sim = model.create({ demandPcuH: 0 });
  const scene = sim.scenes[1];
  scene.vehicles.push(car({ u: -1, y: 1.85, speed: 10, v0: 10, home: 1.85,
    target: 1.85, decision: 0, state: 'moving', served: false, trail: [] }));
  assert.equal(model.travelStats(scene).seconds, null);
  for (let n = 0; n < 14 / model.DT; n++) model.step(sim);
  const stats = model.travelStats(scene, 12);
  assert.equal(stats.admitted, 1); assert.equal(stats.cars, 1); assert.equal(stats.completed, 1);
  assert.equal(stats.unfinished, 0);
  assert.ok(Math.abs(stats.seconds - 12.5) < 1e-8);
  assert.ok(Math.abs(stats.scaledMinutes - 20) < 1e-8);
  assert.ok(Math.abs(model.travelStats(scene, 15).scaledMinutes - 25) < 1e-8);
  assert.equal(model.percentageChange(20, 15), -25);
  assert.equal(model.percentageChange(10, 15), 50);
  assert.equal(model.percentageChange(0, 15), null);
  assert.equal(model.percentageChange(null, 15), null);
});

test('travel averages exclude pre-reset vehicles and incomplete trips', () => {
  const sim = model.create({ demandPcuH: 0 });
  const scene = sim.scenes[1];
  scene.vehicles.push(car({ u: -1, y: 1.85, speed: 10, v0: 10, home: 1.85,
    target: 1.85, decision: 0, state: 'moving', served: false, trail: [] }));
  for (let n = 0; n < 2 / model.DT; n++) model.step(sim);
  assert.equal(model.travelStats(scene).unfinished, 1);
  assert.equal(model.travelStats(scene).seconds, null);
  model.resetMeasurement(sim);
  for (let n = 0; n < 14 / model.DT; n++) model.step(sim);
  assert.equal(model.travelStats(scene).admitted, 0);
  assert.equal(model.travelStats(scene).completed, 0);
  assert.equal(model.travelStats(scene).seconds, null);
});

test('reference capacity matches Python inputs; V stays shared as violations change C', () => {
  const { execFileSync } = require('node:child_process');
  const reference = JSON.parse(execFileSync('python3', ['-c',
    'import inputs_silk_board as i,math,json; p=math.prod(x["today"] for x in i.INTERVENTIONS); k=math.log(i.TODAY_CAPACITY/i.BEST_CAPACITY)/math.log(p); print(json.dumps({"best":i.BEST_CAPACITY,"today":i.TODAY_CAPACITY,"k":k,"fixedStops":i.BEST_CAPACITY*math.prod(x["today"]**k for x in i.INTERVENTIONS if x["id"] not in ("parking","bus"))}))'], { cwd: __dirname, encoding: 'utf8', env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } }));
  assert.ok(Math.abs(model.CAPACITY.k - reference.k) < 1e-12);
  assert.ok(Math.abs(model.capacity(false, 100) - reference.today) < 1e-8);
  assert.ok(Math.abs(model.capacity(false, 0) - reference.fixedStops) < 1e-8);
  assert.equal(model.capacity(true, 100), reference.best);
  assert.ok(model.capacity(false, 50) > model.capacity(false, 100));
  const sim = model.create({ demandPcuH: 8000, violations: 50 });
  assert.equal(model.volumeCapacity(sim, sim.scenes[0]).demand, 8000);
  assert.equal(model.volumeCapacity(sim, sim.scenes[1]).demand, 8000);
  assert.ok(model.volumeCapacity(sim, sim.scenes[0]).ratio > model.volumeCapacity(sim, sim.scenes[1]).ratio);
});

test('maximum PCU demand conserves offered PCUs and creates queues without overlaps', () => {
  const sim = model.create({ demandPcuH: 24000 });
  const offered = new Map();
  for (let n = 0; n < 180 / model.DT; n++) {
    model.step(sim);
    for (const scene of sim.scenes) {
      for (const v of scene.vehicles.concat(scene.pending.flat())) offered.set(v.id, model.PCU[v.type.name]);
      if (n % 30 === 0) for (let i = 0; i < scene.vehicles.length; i++) {
        const v = scene.vehicles[i];
        for (const other of scene.vehicles.slice(i + 1).concat(scene.parking)) {
          if (other.dir === v.dir) assert.equal(model.overlaps(v.u, v.y, v, other, -.001), false);
        }
      }
      assert.equal(scene.passed + scene.vehicles.length + scene.pending.flat().length, sim.serial[0] + sim.serial[1]);
    }
  }
  const offeredPcuH = [...offered.values()].reduce((a, b) => a + b, 0) * 3600 / sim.time;
  assert.ok(Math.abs(offeredPcuH / 24000 - 1) < .1, `mean offered demand ${offeredPcuH}`);
  assert.ok(sim.scenes.every(s => s.pending.flat().length > 100));
});

test('actual PCU budget and conservation hold at every step for both roads', () => {
  for (const demandPcuH of [0, 3996, 8000, 24000]) {
    const sim = model.create({ demandPcuH });
    for (let n = 0; n < 90 / model.DT; n++) {
      model.step(sim);
      for (let dir = 0; dir < 2; dir++) {
        const budget = demandPcuH * sim.time / 7200;
        assert.ok(Math.abs(budget - sim.offeredPcu[dir] - sim.credit[dir]) < 1e-6);
        assert.ok(sim.credit[dir] >= -1e-8 && sim.credit[dir] < 3.7 + .6 + 1e-8);
      }
      if (n % 30 !== 0) continue;
      const total = sim.offeredPcu.reduce((a, b) => a + b, 0);
      for (const scene of sim.scenes) {
        const waiting = model.demandStats(sim, scene).waitingPcu;
        const onRoad = scene.vehicles.filter(v => v.u >= 0 && v.u < model.LENGTH)
          .reduce((sum, v) => sum + model.PCU[v.type.name], 0);
        assert.ok(Math.abs(total - waiting - onRoad - scene.totalDepartedPcu) < 1e-6);
      }
      assert.equal(model.demandStats(sim, sim.scenes[0]).offered.perMinute,
        model.demandStats(sim, sim.scenes[1]).offered.perMinute);
    }
  }
});

test('benchmark and moderate-overload contrast come from simulated discharge', () => {
  for (const demandPcuH of [18000, 24000]) {
    const sim = model.create({ demandPcuH, violations: 100 });
    for (let n = 0; n < 120 / model.DT; n++) model.step(sim);
    const start = sim.scenes.map(s => s.totalDepartedPcu);
    for (let n = 0; n < 480 / model.DT; n++) model.step(sim);
    const flows = sim.scenes.map((s, i) => (s.totalDepartedPcu - start[i]) * 3600 / 480);
    if (demandPcuH === 18000) {
      assert.ok(Math.abs(flows[0] - model.BENCHMARK.upper[4]) < .05);
      assert.ok(flows[1] > flows[0] * 1.2);
      assert.ok(model.travelStats(sim.scenes[0]).seconds > model.travelStats(sim.scenes[1]).seconds * 1.3);
    } else assert.ok(Math.abs(flows[1] - model.BENCHMARK.lower) < .05);
  }
});

test('PCU outflow combines directions, normalizes startup and expires old exits', () => {
  const scene = { measurementStart: 25, exits: [
    { time: 30, dir: 0, pcu: model.PCU.car },
    { time: 40, dir: 1, pcu: model.PCU.bus },
    { time: 50, dir: 0, pcu: model.PCU.bike }
  ] };
  const early = model.outflow(scene, 55);
  assert.equal(early.seconds, 30);
  assert.ok(Math.abs(early.perMinute - 10.9) < 1e-9);
  assert.deepEqual(early.byDirection, [3.5, 7.4]);
  const rolling = model.outflow(scene, 95);
  assert.equal(rolling.seconds, 60);
  assert.equal(rolling.perMinute, 4.45);
  assert.equal(model.outflow(scene, 110).perMinute, 0);
  assert.equal(model.outflow(scene, 25).perMinute, 0);
});

test('measurement reset clears pre-run exits without changing moving traffic', () => {
  const sim = model.create();
  for (let n = 0; n < 90 / model.DT; n++) model.step(sim);
  assert.ok(sim.scenes.every(scene => scene.exits.length > 0));
  const active = sim.scenes.map(scene => scene.vehicles.length);
  model.resetMeasurement(sim);
  assert.deepEqual(sim.scenes.map(scene => scene.vehicles.length), active);
  for (const scene of sim.scenes) {
    assert.equal(scene.passed, 0);
    assert.equal(scene.exits.length, 0);
    assert.equal(model.outflow(scene, sim.time).perMinute, 0);
  }
});

test('zero inflow generates no traffic; higher demand offers more identical arrivals', () => {
  const none = model.create({ demandPcuH: 0 });
  const low = model.create({ demandPcuH: 3000 });
  const high = model.create({ demandPcuH: 12000 });
  for (let n = 0; n < 60 / model.DT; n++) for (const sim of [none, low, high]) model.step(sim);
  assert.deepEqual(none.serial, [0, 0]);
  assert.ok(none.scenes.every(s => s.vehicles.length === 0 && s.passed === 0 && s.pending.flat().length === 0));
  assert.ok(high.serial[0] > low.serial[0] * 3);
  for (const sim of [low, high]) {
    const ids = sim.scenes.map(scene => scene.passedIds.concat(scene.vehicles.map(v => v.id), scene.pending.flat().map(v => v.id)).sort((a, b) => a - b));
    assert.deepEqual(ids[0], ids[1]);
    for (const scene of sim.scenes) assert.equal(scene.passed + scene.vehicles.length + scene.pending.flat().length, sim.serial[0] + sim.serial[1]);
  }
});

test('violation slider changes only upper-road stop placement and parking, with safe geometry', () => {
  const sims = [0, 50, 100].map(violations => model.create({ demandPcuH: 9000, violations }));
  for (let n = 0; n < 120 / model.DT; n++) {
    for (const sim of sims) {
      model.step(sim);
      const scene = sim.scenes[0];
      for (let i = 0; i < scene.vehicles.length; i++) {
        const v = scene.vehicles[i];
        if (sim.settings.violations === 0) assert.equal(v.useBay, true);
        if (sim.settings.violations === 100) assert.equal(v.useBay, false);
        for (const other of scene.vehicles.slice(i + 1).concat(scene.parking)) {
          if (other.dir === v.dir) assert.equal(model.overlaps(v.u, v.y, v, other, -.001), false);
        }
      }
    }
  }
  assert.ok(sims[0].scenes[0].parking.every(p => p.y + p.type.width / 2 <= 0));
  assert.ok(sims[2].scenes[0].parking.every(p => p.y + p.type.width / 2 > 0));
  for (const sim of sims.slice(1)) {
    assert.deepEqual(sim.serial, sims[0].serial);
    assert.deepEqual(sim.scenes[1], sims[0].scenes[1], 'lower scene is independent of violation setting');
  }
  const middle = sims[1].scenes[0].vehicles.concat(sims[1].scenes[0].pending.flat()).filter(v => v.stop);
  assert.ok(middle.some(v => v.useBay) && middle.some(v => !v.useBay));
});

test('intensity adds parked cars/autos, extra stops and cutting drivers without changing buses or arrivals', () => {
  const assigned = [];
  for (const violations of [0, 25, 50, 75, 100]) {
    const sim = model.create({ violations });
    const counts = { car: 0, auto: 0, van: 0, cutting: 0, buses: [] };
    for (let serial = 0; serial < 1000; serial++) for (let dir = 0; dir < 2; dir++) {
      const v = model.makeVehicle(serial, dir);
      const original = { type: v.type, stop: v.stop, dwell: v.dwell };
      model.configureViolations(v, sim.scenes[0]);
      assert.equal(v.type, original.type, 'intensity must not alter vehicle mix or PCUs');
      if (v.type.name === 'bus') {
        assert.equal(v.stop, original.stop); assert.equal(v.dwell, original.dwell);
        counts.buses.push(v.id);
      }
      if (v.stop?.extra) counts[v.type.name]++;
      if (v.cutting) counts.cutting++;
      const lower = model.makeVehicle(serial, dir);
      model.configureViolations(lower, sim.scenes[1]);
      assert.equal(lower.stop, original.stop); assert.equal(lower.dwell, original.dwell);
      assert.equal(lower.cutting, false);
    }
    assigned.push(counts);
  }
  assert.deepEqual(model.violationProfile(100), { intensity: 1, parkingCount: 8, parkedCars: 4, parkedAutos: 3, parkedVans: 1,
    extraCar: .35, extraAuto: .55, extraVan: .20, cuttingShare: .60 });
  for (let i = 1; i < assigned.length; i++) {
    for (const category of ['car', 'auto', 'van', 'cutting']) assert.ok(assigned[i][category] > assigned[i - 1][category]);
    assert.deepEqual(assigned[i].buses, assigned[0].buses);
  }
});

test('partial-width squeeze penalizes a wide vehicle more than a motorcycle', () => {
  const leaders = [car({ id: 2, u: 26, y: 2.2, speed: 0 }), car({ id: 3, u: 26, y: 5.2, speed: 0 })];
  const wide = car();
  const narrow = car({ type: model.types.bike, headway: .45 });
  assert.ok(model.acceleration(wide, leaders) < -1);
  assert.ok(model.acceleration(narrow, leaders) > model.acceleration(wide, leaders) + 1);
});

test('a lateral intrusion slows its new follower without a lane-change penalty', () => {
  const follower = car();
  const leader = car({ id: 2, u: 27, y: 6.5, speed: 2 });
  const clear = model.acceleration(follower, [leader]);
  const intrusion = model.acceleration(follower, [{ ...leader, y: 4.7 }]);
  assert.ok(intrusion < clear - 1);
  assert.ok(model.acceleration(follower, [{ ...leader, y: 3.7, speed: 10 }]) > intrusion);
});

test('steering respects side-by-side bodies and a fast approaching rear vehicle', () => {
  const subject = car({ y: 1.85 });
  assert.equal(model.canSteer(subject, 5.55, [car({ id: 2, y: 5.55, u: 20 })]), false);
  assert.equal(model.canSteer(subject, 5.55, [car({ id: 2, y: 5.55, u: 13, speed: 13 })]), false);
  assert.equal(model.canSteer(subject, 5.55, []), true);
});

test('five minutes: bodies remain separate, demand conserved, stops recur and finish', () => {
  const sim = model.create({ demandPcuH: 8000 });
  const seenModes = new Set();
  const observedStopIds = new Set();
  const stopParams = new Map();
  const partialShiftIds = new Set();
  for (let n = 0; n < 300 / model.DT; n++) {
    model.step(sim);
    for (const scene of sim.scenes) {
      const vs = scene.vehicles;
      for (let i = 0; i < vs.length; i++) {
        const v = vs[i]; seenModes.add(v.type.name);
        assert.ok(Number.isFinite(v.u + v.y + v.speed + v.vy));
        assert.ok(v.speed >= 0);
        assert.ok(v.y + v.type.width / 2 < model.WIDTH);
        if (v.state === 'dwelling') {
          observedStopIds.add(`${scene.ideal}:${v.id}`);
          if (scene.ideal) assert.ok(v.y + v.type.width / 2 < 0, 'managed dwell must be fully off-lane');
        }
        if (v.stop) {
          if (stopParams.has(v.id)) assert.equal(v.dwell, stopParams.get(v.id));
          stopParams.set(v.id, v.dwell);
        }
        if (!scene.ideal && v.trail.length > 3) {
          const span = Math.max(...v.trail.map(p => p.y)) - Math.min(...v.trail.map(p => p.y));
          if (span > .4 && span < 2) partialShiftIds.add(v.id);
        }
        for (const other of vs.slice(i + 1).concat(scene.parking)) {
          if (v.dir !== other.dir) continue;
          assert.equal(model.overlaps(v.u, v.y, v, other, -.001), false,
            `overlap at ${sim.time}: ${v.id}/${other.id}, ideal=${scene.ideal}`);
        }
      }
      assert.equal(scene.passed + vs.length + scene.pending.flat().length, sim.serial[0] + sim.serial[1]);
      assert.equal(new Set(scene.passedIds).size, scene.passedIds.length);
    }
  }
  assert.equal(seenModes.size, 6);
  assert.ok(partialShiftIds.size > 15, 'upper scene uses partial lateral shifts');
  for (const scene of sim.scenes) {
    assert.ok(scene.passed > 100, 'flow remains live');
    assert.ok(scene.stopCount > 10, 'stopping events continue');
    assert.ok(scene.completedStops.length > 10, 'vehicles depart after dwelling');
    for (const stop of scene.completedStops) assert.ok(observedStopIds.has(`${scene.ideal}:${stop.id}`));
  }
  console.log('Illustrative five-minute counts:', sim.scenes.map(scene => ({
    ideal: scene.ideal, passed: scene.passed, stops: scene.stopCount,
    completedStops: scene.completedStops.length, waiting: scene.pending.flat().length
  })));
});
