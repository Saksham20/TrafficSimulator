/* Mixed-traffic illustration. Model/observation notes: traffic_flow_sources.md.
 * Geometry is in metres; time in seconds. No imposed throughput or merge penalty.
 * IDM longitudinal acceleration + MTM-inspired lateral attenuation + gap search.
 * This is a small illustrative model, not a reproduction of the calibrated MTM.
 */
(function (root) {
  'use strict';
  const LENGTH = 125, WIDTH = 7.4, DT = 1 / 30;
  // Fixed illustrative equivalents, consistent with inputs_silk_board.py.
  // The simulated van is a delivery LCV, not a passenger van.
  const PCU = { car: 1, bike: .75, scooter: .75, auto: 2, van: 2, bus: 3.7 };
  // Two-way PCU/hour. Capacity inputs mirror inputs_silk_board.py/model.py.
  const DEFAULTS = { demandPcuH: 8000, violations: 100 };
  const CAPACITY = { best: 3600 / .70, today: 3996,
    factors: { parking: (2 - .1 - 18 * 30 / 3600) / 2, encroach: 5.7 / 6,
      box: .92, bus: (2 - 14.4 * (112 * .60) / 3600) / 2,
      peds: 1 - .30 * (600 - 200) / (1360 - 200), lanes: .95,
      access: .95, signals: 1 / 1.18, surface: .97 } };
  CAPACITY.k = Math.log(CAPACITY.today / CAPACITY.best) /
    Math.log(Object.values(CAPACITY.factors).reduce((p, f) => p * f, 1));
  // 30/32 ordinary arrivals plus two scheduled stop vehicles per direction.
  // Across both directions their combined PCU is auto+bus+car+auto = 8.7.
  const MEAN_PCU = (30 * (.47 * PCU.bike + .25 * PCU.car + .15 * PCU.auto + .08 * PCU.van + .05 * PCU.bus) + 8.7 / 2) / 32;
  function capacity(ideal, violations) {
    if (ideal) return CAPACITY.best;
    const intensity = Math.max(0, Math.min(100, violations)) / 100;
    return CAPACITY.best * Object.entries(CAPACITY.factors).reduce((p, [id, f]) =>
      p * f ** (CAPACITY.k * (id === 'parking' || id === 'bus' ? intensity : 1)), 1);
  }
  // Reproducible demand sweep: node traffic_flow_capacity_audit.js.
  // 120 s warm-up + 480 s measured discharge, five offered demands, one seed.
  // Observed envelope, NOT a fitted saturation curve or a forced throughput.
  const BENCHMARK = { upper: [7871.63, 4306.88, 3144, 2230.12, 2563.12], lower: 8175.38 };
  function simulationCapacity(ideal, violations) {
    if (ideal) return BENCHMARK.lower;
    const q = Math.max(0, Math.min(100, violations)) / 25;
    const i = Math.min(3, Math.floor(q));
    return BENCHMARK.upper[i] + (BENCHMARK.upper[i + 1] - BENCHMARK.upper[i]) * (q - i);
  }
  function volumeCapacity(sim, scene) {
    const c = simulationCapacity(scene.ideal, scene.violations);
    return { demand: sim.settings.demandPcuH, capacity: c, ratio: sim.settings.demandPcuH / c };
  }
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const types = {
    car:     { name: 'car', length: 4.2, width: 1.75, speed: 10.8, a: 1.6, b: 2.2, T: .85, gap: 1.2 },
    bike:    { name: 'bike', length: 1.9, width: .65, speed: 11.7, a: 2.1, b: 2.5, T: .45, gap: .6 },
    scooter: { name: 'scooter', length: 1.8, width: .72, speed: 9.8, a: 1.8, b: 2.4, T: .55, gap: .65 },
    auto:    { name: 'auto', length: 2.65, width: 1.3, speed: 8.4, a: 1.35, b: 2.1, T: .85, gap: 1.0 },
    van:     { name: 'van', length: 5.0, width: 1.95, speed: 9.2, a: 1.2, b: 2.0, T: .95, gap: 1.3 },
    bus:     { name: 'bus', length: 10.3, width: 2.45, speed: 8.5, a: .9, b: 1.8, T: 1.1, gap: 1.5 }
  };
  const stops = [
    { dir: 0, u: 30, type: 'auto', title: 'AUTO PICKUP', dwell: 5 },
    { dir: 0, u: 91, type: 'bus', title: 'BUS BOARDING', dwell: 11 },
    { dir: 1, u: 29, type: 'car', title: 'CAR DROP-OFF', dwell: 6 },
    { dir: 1, u: 88, type: 'auto', title: 'AUTO PICKUP', dwell: 5 }
  ];
  const parked = [
    { id: -1, dir: 0, u: 56, y: .55, type: types.car, speed: 0, vy: 0, fixed: true },
    { id: -2, dir: 1, u: 54, y: .7, type: types.van, speed: 0, vy: 0, fixed: true },
    { id: -3, dir: 0, u: 18, y: .5, type: types.auto, speed: 0, vy: 0, fixed: true },
    { id: -4, dir: 1, u: 16, y: .55, type: types.car, speed: 0, vy: 0, fixed: true },
    { id: -5, dir: 0, u: 73, y: .65, type: types.car, speed: 0, vy: 0, fixed: true },
    { id: -6, dir: 1, u: 71, y: .55, type: types.auto, speed: 0, vy: 0, fixed: true },
    { id: -7, dir: 0, u: 111, y: .55, type: types.auto, speed: 0, vy: 0, fixed: true },
    { id: -8, dir: 1, u: 110, y: .6, type: types.car, speed: 0, vy: 0, fixed: true }
  ];
  // Separate from the shared scheduled passenger services: these are unscheduled
  // kerbside interruptions assigned only to upper-road cars, autos and goods vans.
  const extraStops = [0, 1].flatMap(dir => ['car', 'auto', 'van'].flatMap(type => [38, 82, 99].map(u => ({
    dir, type, u, title: type === 'auto' ? 'EXTRA AUTO PICKUP' : type === 'van' ? 'IN-LANE LOADING' : 'EXTRA CAR STOP',
    dwell: type === 'van' ? 8 : type === 'auto' ? 6 : 5, extra: true
  }))));
  function violationProfile(percent) {
    const intensity = Math.max(0, Math.min(100, percent)) / 100;
    const parkingCount = intensity === 0 ? 0 : 2 * Math.ceil(intensity * 4);
    const active = parked.slice(0, parkingCount);
    return { intensity, parkingCount,
      parkedCars: active.filter(p => p.type.name === 'car').length,
      parkedAutos: active.filter(p => p.type.name === 'auto').length,
      parkedVans: active.filter(p => p.type.name === 'van').length,
      extraCar: .35 * intensity, extraAuto: .55 * intensity, extraVan: .20 * intensity,
      cuttingShare: .60 * intensity };
  }
  function configureViolations(v, scene) {
    const p = violationProfile(scene.violations);
    v.useBay = scene.ideal || random(v.id * 59 + 817) >= p.intensity;
    v.cutting = !scene.ideal && ['car', 'auto'].includes(v.type.name) && random(v.id * 61 + 97) < p.cuttingShare;
    v.aggression = v.cutting ? p.intensity : 0;
    if (scene.ideal || v.stop) return;
    const chance = v.type.name === 'auto' ? p.extraAuto : v.type.name === 'car' ? p.extraCar : v.type.name === 'van' ? p.extraVan : 0;
    if (random(v.id * 83 + 711) >= chance) return;
    const choices = extraStops.filter(s => s.dir === v.dir && s.type === v.type.name);
    v.stop = choices[Math.floor(random(v.id * 19 + 413) * choices.length)];
    v.dwell = v.stop.dwell * (.8 + .4 * random(v.id + 215));
    v.useBay = false;
    scene.assignedExtra[v.type.name]++;
  }
  function random(n) {
    n = Math.imul(n ^ (n >>> 16), 0x7feb352d);
    n = Math.imul(n ^ (n >>> 15), 0x846ca68b);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
  }
  function makeVehicle(serial, dir) {
    const id = serial * 2 + dir, r = random(id * 71 + 33);
    const name = r < .33 ? 'bike' : r < .47 ? 'scooter' : r < .72 ? 'car' : r < .87 ? 'auto' : r < .95 ? 'van' : 'bus';
    const k = serial % 32;
    const stop = dir === 0 ? (k === 2 ? stops[0] : k === 17 ? stops[1] : null)
      : (k === 9 ? stops[2] : k === 25 ? stops[3] : null);
    const type = types[stop ? stop.type : name];
    const lane = stop ? 0 : random(id * 31 + 13) < .5 ? 0 : 1;
    return { id, dir, type, stop, u: -type.length, y: 1.85 + lane * 3.7,
      home: 1.85 + lane * 3.7, speed: 6, vy: 0, accel: 0,
      v0: type.speed * (.87 + .26 * random(id * 47 + 9)),
      headway: type.T * (.85 + .3 * random(id * 17 + 23)),
      decision: random(id + 89) * .3, state: 'moving', served: false,
      dwell: stop ? stop.dwell * (.8 + .4 * random(id + 215)) : 0,
      remaining: 0, trail: [], target: 1.85 + lane * 3.7 };
  }
  function create(options = {}) {
    const settings = {
      demandPcuH: clamp(Number.isFinite(options.demandPcuH) ? options.demandPcuH : DEFAULTS.demandPcuH, 0, 24000),
      violations: clamp(Number.isFinite(options.violations) ? options.violations : DEFAULTS.violations, 0, 100)
    };
    return { settings, time: 0, serial: [0, 0], credit: [0, 0],
      offeredPcu: [0, 0], offeredEvents: [], measurementStart: 0,
      scenes: [false, true].map(ideal => ({ ideal, violations: ideal ? 0 : settings.violations,
        parking: parked.slice(0, ideal ? 2 : Math.max(2, violationProfile(settings.violations).parkingCount))
          .map((p, i) => ({ ...p, y: !ideal && i < violationProfile(settings.violations).parkingCount ? p.y : -1.6 })),
        vehicles: [], pending: [[], []],
        assignedExtra: { car: 0, auto: 0, van: 0 }, extraStopCount: 0, cutAttempts: 0, cutIns: 0,
        passed: 0, stopCount: 0, passedIds: [], completedStops: [], brakeSeconds: 0,
        exits: [], entries: [], measurementStart: 0, admitted: 0, admittedCars: 0,
        admittedPcu: 0, departedPcu: 0, totalDepartedPcu: 0, departed: 0,
        tripCount: 0, tripSeconds: 0, entryWaitSeconds: 0 })) };
  }
  function resetMeasurement(sim) {
    sim.measurementStart = sim.time; sim.offeredEvents = [];
    for (const scene of sim.scenes) {
      scene.passed = 0; scene.passedIds = []; scene.exits = []; scene.entries = [];
      scene.measurementStart = sim.time;
      scene.admitted = 0; scene.admittedCars = 0; scene.tripCount = 0; scene.tripSeconds = 0;
      scene.admittedPcu = 0; scene.departedPcu = 0; scene.departed = 0; scene.entryWaitSeconds = 0;
      for (const v of scene.vehicles) v.entryTime = null;
    }
  }
  function travelStats(scene, distanceKm = 12) {
    const seconds = scene.tripCount ? scene.tripSeconds / scene.tripCount : null;
    return { seconds, scaledMinutes: seconds === null ? null : seconds * (distanceKm * 1000 / LENGTH) / 60,
      completed: scene.tripCount, admitted: scene.admitted, cars: scene.admittedCars,
      unfinished: scene.admitted - scene.tripCount,
      meanEntryWait: scene.admitted ? scene.entryWaitSeconds / scene.admitted : null };
  }
  function percentageChange(before, after) {
    return before === null || after === null || before === 0 ? null : (after - before) / before * 100;
  }
  function outflow(scene, now) {
    return eventFlow(scene.exits, scene.measurementStart, now);
  }
  function eventFlow(events, start, now) {
    const seconds = Math.min(60, Math.max(0, now - start));
    const since = Math.max(start, now - 60);
    const byDirection = [0, 0];
    for (const event of events) {
      if (event.time > since && event.time <= now) byDirection[event.dir] += event.pcu;
    }
    return { seconds, pcu: byDirection[0] + byDirection[1],
      perMinute: seconds > 0 ? (byDirection[0] + byDirection[1]) * 60 / seconds : 0,
      byDirection: byDirection.map(pcu => seconds > 0 ? pcu * 60 / seconds : 0) };
  }
  function demandStats(sim, scene) {
    const outside = scene.pending.flat().concat(scene.vehicles.filter(v => v.u < 0));
    return {
      offered: eventFlow(sim.offeredEvents, sim.measurementStart, sim.time),
      admitted: eventFlow(scene.entries, scene.measurementStart, sim.time),
      waitingVehicles: outside.length,
      waitingPcu: outside.reduce((sum, v) => sum + PCU[v.type.name], 0),
      oldestWait: outside.length ? Math.max(...outside.map(v => sim.time - v.offeredAt)) : 0,
      onRoad: scene.vehicles.filter(v => v.u >= 0 && v.u < LENGTH).length,
      queuedOnRoad: scene.vehicles.filter(v => v.u >= 0 && v.u < LENGTH && v.speed < 1).length
    };
  }
  function lateralGap(v, o, y = v.y) { return Math.abs(y - o.y) - (v.type.width + o.type.width) / 2; }
  function longitudinalGap(v, o) { return o.u - v.u - (v.type.length + o.type.length) / 2; }
  function neighbours(scene, v) {
    return scene.vehicles.concat(scene.parking.filter(p => p.y + p.type.width / 2 > 0)).filter(o => o !== v && o.dir === v.dir && Math.abs(o.u - v.u) < 55);
  }
  // IDM interaction, weighted by side clearance as in the MTM's Eq. 8.
  // The strongest leader constrains the follower; several bikes ahead don't
  // incorrectly multiply a bus's braking demand.
  function acceleration(v, others, y = v.y) {
    let interaction = 0;
    for (const o of others) {
      if (o.u < v.u) continue;
      const sy = lateralGap(v, o, y);
      if (sy > 1.4) continue;
      const weight = Math.exp(-Math.max(0, sy) / .22);
      const s = longitudinalGap(v, o);
      const desired = v.type.gap + Math.max(0, v.speed * v.headway +
        v.speed * (v.speed - o.speed) / (2 * Math.sqrt(v.type.a * v.type.b)));
      const braking = s <= 0 ? 7 : Math.min(7, v.type.a * (desired / Math.max(.1, s)) ** 2);
      interaction = Math.max(interaction, weight * braking);
    }
    const free = v.type.a * (1 - (v.speed / v.v0) ** 4);
    return clamp(free - interaction, -7, v.type.a);
  }
  // Check the swept lateral corridor and closing speed of followers rather
  // than assigning an entire adjacent lane to a partially intruding vehicle.
  function canSteer(v, y, others, aggression = 0) {
    const low = Math.min(v.y, y), high = Math.max(v.y, y);
    for (const o of others) {
      const side = o.y < low ? low - o.y : o.y > high ? o.y - high : 0;
      if (side > (v.type.width + o.type.width) / 2 + .18) continue;
      const dx = o.u - v.u;
      const gap = Math.abs(dx) - (v.type.length + o.type.length) / 2;
      if (gap < .45) return false;
      if (dx < 0 && lateralGap(v, o, y) < .2) {
        const closing = Math.max(0, o.speed - v.speed);
        if (gap < .7 + (.35 - .17 * aggression) * o.speed + closing * closing / (2 * (3.5 + aggression))) return false;
      }
    }
    return true;
  }
  function stopGoal(v, ideal) { return ideal ? -1.55 : v.type.width / 2 + .24; }
  function bayAvailable(scene, v) {
    return !scene.vehicles.some(o => o !== v && o.stop === v.stop && (o.u > v.u || o.y < 0) && o.u > v.stop.u - 22 && o.u < v.stop.u + 12 &&
      (!o.served || o.y < o.type.width / 2 + .4));
  }
  function clearStopApproach(scene, v) {
    if (!v.stop) return true;
    const goal = stopGoal(v, v.useBay);
    return !scene.parking.some(p => p.dir === v.dir && p.u + (p.type.length + v.type.length) / 2 > v.u &&
      p.y + p.type.width / 2 > 0 && p.u < v.stop.u && p.u - v.u < 35 &&
      p.y >= Math.min(v.y, goal) - (p.type.width + v.type.width) / 2 - .4 &&
      p.y <= Math.max(v.y, goal) + (p.type.width + v.type.width) / 2 + .4);
  }
  function chooseTarget(scene, v, others) {
    const half = v.type.width / 2;
    const low = half + .18, high = WIDTH - half - .22;
    const distance = v.stop ? v.stop.u - v.u : Infinity;
    const approaching = v.stop && !v.served && distance < 35 && clearStopApproach(scene, v);
    let goal = v.home;
    if (approaching) goal = v.useBay && !bayAvailable(scene, v) ? 1.85 : stopGoal(v, v.useBay);
    if (v.state === 'leaving') goal = 1.85;
    if (approaching || v.state === 'leaving') {
      if (canSteer(v, goal, others)) return goal;
      const nearer = v.y + clamp(goal - v.y, -.45, .45);
      if (canSteer(v, nearer, others)) return nearer;
      return v.y;
    }
    let candidates;
    if (scene.ideal) candidates = [v.home, 1.85, 5.55, v.y];
    else {
      candidates = [v.y, v.target, clamp(v.home, low, high)];
      for (let y = low; y <= high; y += .4) candidates.push(y);
      for (const o of others) if (o.u > v.u && o.u - v.u < 27) {
        const margin = (v.type.width + o.type.width) / 2 + .32;
        candidates.push(clamp(o.y - margin, low, high), clamp(o.y + margin, low, high));
      }
    }
    let best = v.y, bestScore = -Infinity;
    for (const y of candidates) {
      if (y < low || y > high || !canSteer(v, y, others, v.aggression || 0)) continue;
      const a = acceleration(v, others, y);
      const aggression = v.aggression || 0;
      const score = a - .13 * (1 - .55 * aggression) * Math.abs(y - v.y) - .06 * (1 - .6 * aggression) * Math.abs(y - v.target)
        - (scene.ideal ? .26 : .025) * Math.abs(y - v.home);
      if (score > bestScore) { best = y; bestScore = score; }
    }
    if (v.cutting && Math.abs(best - v.y) > .9 && !v.cutStart && (v.cutCooldown || 0) <= 0) {
      v.cutStart = { y: v.y }; v.cutCooldown = 3;
      scene.cutAttempts++;
    }
    return best;
  }
  function overlaps(u, y, v, o, margin = .12) {
    return Math.abs(u - o.u) < (v.type.length + o.type.length) / 2 + margin &&
      Math.abs(y - o.y) < (v.type.width + o.type.width) / 2 + margin;
  }
  function spawn(scene, dir) {
    const queue = scene.pending[dir];
    if (!queue.length) return;
    // Preserve the demand queue; small vehicles may enter at another free
    // lateral position, but are not teleported past vehicles already on-road.
    const v = queue[0], half = v.type.width / 2;
    const positions = scene.ideal ? [v.home] : [v.home, ...[1, 2, 3, 4, 5, 6].map(n => clamp(n, half + .2, WIDTH - half - .2))];
    for (const y of positions) {
      if (scene.vehicles.some(o => o.dir === dir && Math.abs(y - o.y) < (v.type.width + o.type.width) / 2 + .3 &&
          Math.abs(v.u - o.u) < (v.type.length + o.type.length) / 2 + 2.5)) continue;
      v.y = y; v.target = y;
      scene.vehicles.push(v); queue.shift(); break;
    }
  }
  function updateScene(scene, dt, now) {
    const plans = new Map();
    // Simultaneous behavioural decisions: no leader is advanced before its
    // follower sees it. Geometry safeguards below arbitrate conflicting moves.
    for (const v of scene.vehicles) {
      v.cutCooldown = Math.max(0, (v.cutCooldown || 0) - dt);
      if (v.state === 'dwelling') {
        v.remaining = Math.max(0, v.remaining - dt);
        if (v.remaining === 0) {
          scene.completedStops.push({ id: v.id, duration: v.dwell });
          v.served = true; v.state = 'leaving'; v.target = 1.85;
        } else { plans.set(v.id, { speed: 0, vy: 0 }); continue; }
      }
      const others = neighbours(scene, v);
      v.decision -= dt;
      if (v.decision <= 0) {
        v.target = chooseTarget(scene, v, others);
        v.decision = .22 + .16 * random(v.id + 99);
      }
      const latMax = Math.min(v.type.width < 1 ? 1.0 : .75, .16 * v.speed + .08);
      const desiredVy = clamp((v.target - v.y) / .65, -latMax, latMax);
      let vy = v.vy + clamp((desiredVy - v.vy) / .4, -1.7, 1.7) * dt;
      let a = acceleration(v, others);
      // Both scenes share acceleration/headway parameters. No hard-coded
      // slowdown on lane changes: reactions depend on actual lateral clearance.
      let speed = Math.max(0, v.speed + a * dt);
      if (v.stop && !v.served) {
        const available = !v.useBay || bayAvailable(scene, v);
        const remaining = v.stop.u - v.u - (available ? 0 : 23);
        const safe = Math.sqrt(2 * v.type.b * Math.max(0, remaining));
        speed = Math.min(speed, safe);
        if (remaining < 30 && available && clearStopApproach(scene, v)) {
          const lateralTime = Math.abs(v.y - stopGoal(v, v.useBay)) / .65;
          if (lateralTime > .3) speed = Math.min(speed, Math.max(.2, remaining) / (lateralTime + .3));
        }
        speed = Math.min(speed, Math.max(0, remaining) / dt);
      }
      if (v.state === 'leaving' && v.y < v.type.width / 2 + .15) {
        // A bay departure must first find a usable rear gap. No jump to speed.
        if (!canSteer(v, 1.85, others)) { speed = 0; vy = 0; }
        else speed = Math.min(speed, 2.2);
      }
      plans.set(v.id, { speed, vy });
    }
    const ordered = [...scene.vehicles].sort((a, b) => b.u - a.u || a.id - b.id);
    for (const v of ordered) {
      const plan = plans.get(v.id), oldSpeed = v.speed;
      const others = neighbours(scene, v);
      let y = v.y + plan.vy * dt;
      const half = v.type.width / 2;
      const inBay = v.useBay && v.stop && Math.abs(v.u - v.stop.u) < 37;
      y = clamp(y, inBay ? -2.9 + half : half + .14, WIDTH - half - .14);
      // Swept lateral test: prevent two side-by-side bodies moving through
      // each other. Forward motion can continue while the steering waits.
      const sweepY = (y + v.y) / 2;
      if (others.some(o => Math.abs(v.u - o.u) < (v.type.length + o.type.length) / 2 + .18 &&
          Math.abs(sweepY - o.y) < (v.type.width + o.type.width) / 2 + Math.abs(y - v.y) / 2 + .16)) y = v.y;
      let travel = plan.speed * dt;
      for (const o of others) {
        if (o.u <= v.u || Math.abs(y - o.y) >= (v.type.width + o.type.width) / 2 + .16) continue;
        travel = Math.min(travel, Math.max(0, longitudinalGap(v, o) - .18));
      }
      const u = v.u + travel;
      if (others.some(o => overlaps(u, y, v, o))) { y = v.y; travel = 0; }
      const previousU = v.u;
      v.vy = (y - v.y) / dt; v.y = y; v.u += travel;
      if (v.cutStart && Math.abs(v.y - v.cutStart.y) > .7) { scene.cutIns++; v.cutStart = null; }
      else if (v.cutStart && v.cutCooldown === 0) v.cutStart = null;
      // Measure centre crossings of 0 m and 125 m, independent of vehicle
      // length and of the off-screen spawn/removal buffers. Interpolate time.
      if (previousU < 0 && v.u >= 0) {
        v.entryTime = now - dt + dt * (-previousU / travel);
        scene.admitted++;
        scene.admittedPcu += PCU[v.type.name];
        scene.entries.push({ time: v.entryTime, dir: v.dir, pcu: PCU[v.type.name] });
        scene.entryWaitSeconds += Math.max(0, v.entryTime - (v.offeredAt ?? v.entryTime));
        if (v.type.name === 'car') scene.admittedCars++;
      }
      if (previousU < LENGTH && v.u >= LENGTH) {
        const exitTime = now - dt + dt * ((LENGTH - previousU) / travel);
        scene.departed++; scene.departedPcu += PCU[v.type.name]; scene.totalDepartedPcu += PCU[v.type.name];
        scene.exits.push({ time: exitTime, dir: v.dir, pcu: PCU[v.type.name] });
        if (v.entryTime != null && v.entryTime >= scene.measurementStart) {
          scene.tripSeconds += exitTime - v.entryTime;
          scene.tripCount++;
        }
      }
      v.speed = travel / dt;
      v.accel = (v.speed - oldSpeed) / dt;
      if (v.accel < -.8 && v.u > 0 && v.u < LENGTH) scene.brakeSeconds += dt;
      if (v.stop && !v.served && v.state === 'moving' && Math.abs(v.u - v.stop.u) < .24 &&
          (!v.useBay || Math.abs(v.y - stopGoal(v, true)) < .35) && v.speed < .6) {
        v.state = 'dwelling'; v.remaining = v.dwell; v.speed = 0; v.vy = 0; scene.stopCount++;
        if (v.stop.extra) scene.extraStopCount++;
      }
      if (v.state === 'leaving' && v.y > half + .2) v.state = 'moving';
      if (!v.trail.length || now - v.trail[v.trail.length - 1].t > .16) v.trail.push({ u: v.u, y: v.y, t: now });
      while (v.trail.length && v.trail[0].t < now - 2.8) v.trail.shift();
    }
    scene.vehicles = scene.vehicles.filter(v => {
      if (v.u <= LENGTH + v.type.length) return true;
      scene.passed++; scene.passedIds.push(v.id);
      return false;
    });
    while (scene.exits.length && scene.exits[0].time <= now - 60) scene.exits.shift();
    while (scene.entries.length && scene.entries[0].time <= now - 60) scene.entries.shift();
    spawn(scene, 0); spawn(scene, 1);
  }
  function step(sim, dt = DT) {
    sim.time += dt;
    for (let dir = 0; dir < 2; dir++) {
      sim.credit[dir] += sim.settings.demandPcuH * dt / 7200;
      while (sim.settings.demandPcuH > 0) {
        const next = makeVehicle(sim.serial[dir], dir);
        const cost = PCU[next.type.name];
        // Spend ACTUAL PCUs, not an estimated PCU/vehicle conversion. A small
        // seeded dispatch delay gives irregular headways while keeping the
        // unspent budget below one vehicle plus 0.6 PCU per direction.
        const jitter = .6 * random(next.id * 43 + 12);
        if (sim.credit[dir] + 1e-10 < cost + jitter) break;
        sim.credit[dir] -= cost;
        sim.offeredPcu[dir] += cost;
        sim.offeredEvents.push({ time: sim.time, dir, pcu: cost });
        const serial = sim.serial[dir]++;
        for (const scene of sim.scenes) {
          const v = makeVehicle(serial, dir);
          v.offeredAt = sim.time;
          // Preserve actual arrivals and bus service; only upper-road behaviour
          // gets additional unscheduled car/auto/loading stops and cut-in attempts.
          configureViolations(v, scene);
          if (!scene.ideal && !v.stop) {
            v.home = clamp(v.home + (random(v.id * 29 + 15) - .5) * 2.0, v.type.width / 2 + .25, WIDTH - v.type.width / 2 - .25);
          }
          scene.pending[dir].push(v);
        }
      }
    }
    while (sim.offeredEvents.length && sim.offeredEvents[0].time <= sim.time - 60) sim.offeredEvents.shift();
    for (const scene of sim.scenes) updateScene(scene, dt, sim.time);
  }
  const api = { LENGTH, WIDTH, DT, PCU, DEFAULTS, CAPACITY, BENCHMARK, MEAN_PCU, capacity, simulationCapacity, volumeCapacity, types, stops, parked, extraStops, violationProfile, configureViolations, makeVehicle, create, step, resetMeasurement, outflow, demandStats, travelStats, percentageChange, acceleration, canSteer, overlaps, stopGoal };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.TrafficFlow = api;
})(typeof globalThis === 'undefined' ? this : globalThis);
