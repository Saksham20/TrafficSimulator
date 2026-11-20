/* Canvas view and controls; physical interactions live in traffic_flow_model.js. */
(() => {
  'use strict';
  const model = window.TrafficFlow, W = 1000, H = 290;
  const canvases = ['today', 'ideal'].map(id => document.getElementById(id));
  const contexts = canvases.map(c => c.getContext('2d'));
  const pauseButton = document.getElementById('pause');
  const inflowInput = document.getElementById('inflow');
  const violationsInput = document.getElementById('violations');
  const distanceInput = document.getElementById('distance');
  const endButton = document.getElementById('end');
  const advanceButton = document.getElementById('advance');
  const media = window.matchMedia('(prefers-reduced-motion: reduce)');
  let sim, paused = media.matches, ended = false, rate = 1, showPaths = true, last = null, accumulated = 0;
  const scale = 8;
  function position(v) { return { x: v.dir === 0 ? v.u * scale : W - v.u * scale, y: v.dir === 0 ? 64 + v.y * 10 : 230 - v.y * 10 }; }
  function line(ctx, x1, y1, x2, y2, width = 1, dash = []) {
    ctx.lineWidth = width; ctx.setLineDash(dash); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.setLineDash([]);
  }
  function label(ctx, text, x, y, align = 'left', size = 9) {
    ctx.font = `${size}px ui-monospace, SFMono-Regular, Menlo, monospace`;
    ctx.textAlign = align; ctx.fillText(text, x, y); ctx.textAlign = 'left';
  }
  function body(ctx, v, muted = false, icon = false) {
    const p = position(v), type = v.type, L = type.length * scale, B = type.width * 10;
    ctx.save(); ctx.translate(p.x, p.y); if (v.dir) ctx.rotate(Math.PI);
    // Heading follows motion, with a small visual cap to preserve wireframe clarity.
    if (!icon) ctx.rotate(Math.max(-.12, Math.min(.12, Math.atan2(v.vy * 10, Math.max(v.speed * scale, 8)))));
    ctx.fillStyle = '#fff'; ctx.strokeStyle = muted ? '#777' : '#191919'; ctx.lineWidth = 1.2;
    ctx.fillRect(-L / 2 - .5, -B / 2 - .5, L + 1, B + 1);
    if (type.width < 1) {
      line(ctx, -L / 2, 0, L / 2, 0, 2);
      ctx.strokeRect(-L * .17, -B * .32, L * .35, B * .64);
      line(ctx, L * .25, -B / 2, L * .25, B / 2);
      if (type.name === 'scooter') line(ctx, L * .1, -B / 2, L * .1, B / 2, 2);
    } else {
      ctx.beginPath(); ctx.roundRect(-L / 2, -B / 2, L, B, type.name === 'bus' ? 1 : 3); ctx.stroke();
      if (type.name === 'car') {
        ctx.strokeRect(-L * .16, -B * .34, L * .38, B * .68);
        line(ctx, L * .22, -B * .34, L * .29, -B / 2);
        line(ctx, L * .22, B * .34, L * .29, B / 2);
      } else if (type.name === 'auto') {
        ctx.strokeRect(-L * .38, -B * .38, L * .48, B * .76);
        line(ctx, L * .25, -B * .27, L * .25, B * .27);
      } else {
        line(ctx, L / 2 - 9, -B / 2 + 2, L / 2 - 9, B / 2 - 2);
        if (type.name === 'bus') for (let x = -L / 2 + 6; x < L / 2 - 12; x += 10) {
          line(ctx, x, -B / 2 + 3, x + 6, -B / 2 + 3);
          line(ctx, x, B / 2 - 3, x + 6, B / 2 - 3);
        }
      }
    }
    if (v.accel < -.8 && v.speed > .2) line(ctx, -L / 2 - 2, -B / 2, -L / 2 - 2, B / 2, 2.4);
    if (v.state === 'dwelling') {
      ctx.setLineDash([3, 3]); ctx.strokeRect(-L / 2 - 4, -B / 2 - 4, L + 8, B + 8); ctx.setLineDash([]);
    }
    ctx.restore();
  }
  function road(ctx, scene) {
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = '#202020'; ctx.fillStyle = '#555';
    line(ctx, 0, 64, W, 64, 1.5); line(ctx, 0, 230, W, 230, 1.5);
    line(ctx, 0, 140, W, 140, 1); line(ctx, 0, 154, W, 154, 1);
    ctx.strokeStyle = '#ccc';
    line(ctx, 0, 101, W, 101, .8, scene.ideal ? [18, 14] : [6, 30]);
    line(ctx, 0, 193, W, 193, .8, scene.ideal ? [18, 14] : [6, 30]);
    ctx.strokeStyle = '#999';
    for (let x = 0; x < W; x += 20) line(ctx, x, 140, x + 8, 154, .6);
    label(ctx, '→', 15, 128, 'left', 16); label(ctx, '←', 985, 175, 'right', 16);
    label(ctx, 'LEFT-HAND TRAFFIC · TOP VIEW', 12, 16, 'left', 9);
    for (const stop of model.stops) {
      const x = stop.dir === 0 ? stop.u * scale : W - stop.u * scale;
      const showBay = scene.ideal || scene.violations < 100;
      if (showBay) {
        const bayWidth = stop.type === 'bus' ? 112 : 64;
        ctx.fillStyle = '#fff'; ctx.fillRect(x - bayWidth / 2, stop.dir === 0 ? 33 : 231, bayWidth, 29);
        ctx.strokeStyle = '#888'; ctx.strokeRect(x - bayWidth / 2, stop.dir === 0 ? 33 : 232, bayWidth, 27);
      }
      ctx.fillStyle = '#555';
      label(ctx, showBay ? (stop.type === 'bus' ? 'BUS BAY' : 'PICKUP BAY') : stop.title, x, stop.dir === 0 ? 29 : 267, 'center');
      const active = scene.vehicles.find(v => v.stop === stop && v.state === 'dwelling');
      const phase = active ? 1 - active.remaining / active.dwell : 0;
      // Passenger moves between pavement and door only while the vehicle dwells.
      const useBay = active ? active.useBay : showBay;
      const py = stop.dir === 0 ? 48 + (useBay ? -14 : 15) * Math.sin(phase * Math.PI) : 246 - (useBay ? -14 : 15) * Math.sin(phase * Math.PI);
      ctx.strokeStyle = '#444'; ctx.beginPath(); ctx.arc(x + 8, py, 2.5, 0, Math.PI * 2); ctx.stroke();
    }
    for (const v of scene.parking) {
      body(ctx, v, true, true);
      const p = position(v); ctx.fillStyle = '#555';
      label(ctx, 'P', p.x, v.dir === 0 ? p.y - v.type.width * 5 - 5 : p.y + v.type.width * 5 + 10, 'center');
    }
  }
  function draw() {
    const offered = sim.offeredPcu[0] + sim.offeredPcu[1];
    const budget = sim.settings.demandPcuH * sim.time / 3600;
    document.getElementById('demand-check').textContent = `PCU AUDIT (including pre-run): ${offered.toFixed(1)} generated / ${budget.toFixed(1)} budgeted · ${(budget - offered).toFixed(1)} PCU waiting for whole vehicles · same arrivals on both roads · ${(sim.time - sim.measurementStart).toFixed(0)} s measured`;
    contexts.forEach((ctx, i) => {
      const scene = sim.scenes[i]; road(ctx, scene);
      if (showPaths) for (const v of scene.vehicles) {
        if (v.trail.length < 2) continue;
        ctx.strokeStyle = '#c4c4c4'; ctx.lineWidth = .7; ctx.beginPath();
        v.trail.forEach((point, n) => { const p = position({ ...point, dir: v.dir }); if (n === 0) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y); });
        ctx.stroke();
      }
      for (const v of scene.vehicles) {
        body(ctx, v);
        if (v.state === 'dwelling' && v.stop.extra) {
          const p = position(v); ctx.fillStyle = '#444';
          label(ctx, v.stop.title, p.x, v.dir === 0 ? 51 : 246, 'center', 8);
        }
      }
      const prefix = i === 0 ? 'today' : 'ideal';
      document.getElementById(`${prefix}-count`).textContent = scene.departed;
      const flow = model.outflow(scene, sim.time);
      document.getElementById(`${prefix}-flow`).textContent = flow.perMinute.toFixed(1);
      const vc = model.volumeCapacity(sim, scene);
      document.getElementById(`${prefix}-vc`).textContent = vc.ratio.toFixed(2);
      document.getElementById(`${prefix}-capacity`).textContent = `V ${Math.round(vc.demand).toLocaleString()} / C ≈ ${Math.round(vc.capacity).toLocaleString()} PCU/h · ${vc.ratio > 1 ? 'Above benchmark' : 'Below benchmark'}`;
      const travel = model.travelStats(scene, Number(distanceInput.value));
      document.getElementById(`${prefix}-time`).textContent = travel.scaledMinutes === null ? '—' : `${travel.scaledMinutes.toFixed(1)} min / ${distanceInput.value} km`;
      document.getElementById(`${prefix}-time-detail`).textContent = travel.seconds === null ? 'Waiting for completed post-reset trips' : `${travel.seconds.toFixed(1)} s / 125 m × ${Number(distanceInput.value) * 8} · ${travel.completed} completed trips`;
      document.getElementById(`${prefix}-admitted`).textContent = `${travel.admitted} vehicles admitted · ${travel.cars} cars`;
      const accounting = model.demandStats(sim, scene);
      document.getElementById(`${prefix}-inflow`).textContent = `Offered ${accounting.offered.perMinute.toFixed(1)} → admitted ${accounting.admitted.perMinute.toFixed(1)} → outflow ${flow.perMinute.toFixed(1)} PCU/min · same rolling window`;
      document.getElementById(`${prefix}-queue`).textContent = `ENTRY QUEUE: ${accounting.waitingVehicles} vehicles / ${accounting.waitingPcu.toFixed(1)} PCU · ${accounting.queuedOnRoad} slow/stopped on-road`;
      document.getElementById(`${prefix}-wait`).textContent = `Mean entry wait of admitted vehicles: ${travel.meanEntryWait === null ? '—' : `${travel.meanEntryWait.toFixed(1)} s`} · oldest still waiting: ${accounting.oldestWait.toFixed(0)} s`;
      document.getElementById(`${prefix}-window`).textContent = flow.seconds < 60
        ? `Building window · ${Math.floor(flow.seconds)}/60 s` : 'Rolling last 60 simulated seconds';
      const waiting = accounting.waitingVehicles;
      const dwelling = scene.vehicles.filter(v => v.state === 'dwelling');
      document.getElementById(`${prefix}-status`).textContent = dwelling.length
        ? `${dwelling.map(v => `${v.stop.title} ${Math.ceil(v.remaining)}s`).join(' · ')}${waiting ? ` · ${waiting} WAITING TO ENTER` : ''}`
        : `${i === 0 ? 'BIKES FILTER · CARS STAGGER · WIDTH MATTERS' : 'PREDICTABLE PATHS · SAME VEHICLE MIX'}${waiting ? ` · ${waiting} WAITING TO ENTER` : ''}`;
    });
  }
  function reset() {
    ended = false; endButton.disabled = false; pauseButton.disabled = false; advanceButton.disabled = false;
    document.getElementById('results').hidden = true;
    sim = model.create({ demandPcuH: Number(inflowInput.value), violations: Number(violationsInput.value) });
    for (let i = 0; i < 25 / model.DT; i++) model.step(sim);
    model.resetMeasurement(sim);
    accumulated = 0; last = null; draw();
  }
  function resize() {
    canvases.forEach((canvas, i) => {
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = W * pixelRatio; canvas.height = H * pixelRatio;
      contexts[i].setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    }); draw();
  }
  function syncPause() { pauseButton.textContent = paused ? '▶ Play' : 'Ⅱ Pause'; pauseButton.setAttribute('aria-pressed', String(paused)); }
  pauseButton.addEventListener('click', () => { paused = !paused; syncPause(); });
  document.getElementById('speed').addEventListener('click', event => {
    rate = rate === 1 ? 2 : 1; event.target.textContent = `${rate}× speed`; event.target.setAttribute('aria-pressed', String(rate === 2));
  });
  document.getElementById('trails').addEventListener('click', event => {
    showPaths = !showPaths; event.target.textContent = showPaths ? 'Paths on' : 'Paths off'; event.target.setAttribute('aria-pressed', String(showPaths)); draw();
  });
  document.getElementById('reset').addEventListener('click', reset);
  function showResults() {
    const stats = sim.scenes.map(scene => model.travelStats(scene, Number(distanceInput.value)));
    const rows = [
      [`Average travel time · ${distanceInput.value} km extrapolation`, stats.map(s => s.scaledMinutes), 'min'],
      ['Average travel time · measured 125 m', stats.map(s => s.seconds), 's'],
      ['Mean entry wait · admitted vehicles (not distance-scaled)', stats.map(s => s.meanEntryWait), 's'],
      ['PCU admitted after reset', sim.scenes.map(s => s.admittedPcu), 'PCU'],
      ['PCU discharged after reset', sim.scenes.map(s => s.departedPcu), 'PCU'],
      ['Vehicles admitted (all modes)', stats.map(s => s.admitted), ''],
      ['Cars admitted', stats.map(s => s.cars), ''],
      ['Completed post-reset trips', stats.map(s => s.completed), ''],
      ['Admitted trips still unfinished', stats.map(s => s.unfinished), ''],
      ['Vehicles waiting outside entrance', sim.scenes.map(s => model.demandStats(sim, s).waitingVehicles), ''],
      ['PCU waiting outside entrance', sim.scenes.map(s => model.demandStats(sim, s).waitingPcu), 'PCU']
    ];
    const tbody = document.getElementById('results-body'); tbody.replaceChildren();
    for (const [label, values, unit] of rows) {
      const change = model.percentageChange(values[0], values[1]);
      const tr = document.createElement('tr');
      const cells = [label, ...values.map(v => v === null ? '—' : unit ? `${v.toFixed(1)} ${unit}` : v.toLocaleString()),
        change === null ? '—' : `${change > 0 ? '+' : ''}${change.toFixed(1)}%`];
      for (const text of cells) { const td = document.createElement('td'); td.textContent = text; tr.append(td); }
      tbody.append(tr);
    }
    document.getElementById('results-context').textContent = `${(sim.time - sim.scenes[0].measurementStart).toFixed(1)} simulated seconds measured · ${sim.settings.demandPcuH.toLocaleString()} PCU/h shared demand · ${sim.settings.violations}% upper-road violations. Negative travel-time change means the lower road is faster.`;
    document.getElementById('results').hidden = false;
  }
  endButton.addEventListener('click', () => {
    ended = true; endButton.disabled = true; pauseButton.disabled = true; advanceButton.disabled = true;
    showResults(); document.getElementById('results-title').focus();
  });
  distanceInput.addEventListener('change', () => { draw(); if (ended) showResults(); });
  advanceButton.addEventListener('click', () => {
    if (ended) return;
    for (let n = 0; n < 300 / model.DT; n++) model.step(sim);
    accumulated = 0; last = null; draw();
  });
  function settingLabels() {
    document.getElementById('inflow-value').textContent = `${Number(inflowInput.value).toLocaleString()} PCU/h`;
    document.getElementById('inflow-context').textContent = `${(Number(inflowInput.value) / 60).toFixed(1)} PCU/min · ${(Number(inflowInput.value) / model.CAPACITY.today).toFixed(2)}× Silk Board observed peak reference`;
    document.getElementById('violations-value').textContent = `${violationsInput.value}%`;
    inflowInput.setAttribute('aria-valuetext', `${inflowInput.value} PCU per hour per road, both directions combined`);
    violationsInput.setAttribute('aria-valuetext', `${violationsInput.value} percent violation intensity on the upper road`);
    const profile = model.violationProfile(Number(violationsInput.value));
    const descriptions = [
      `Wrong parking: ${profile.parkingCount} protruding vehicles (${profile.parkedCars} cars, ${profile.parkedAutos} autos, ${profile.parkedVans} delivery vans), both directions combined.`,
      `Extra car stops: ${Math.round(profile.extraCar * 100)}% of otherwise non-stopping cars; about 4–6 s each.`,
      `Extra auto pickups / drop-offs: ${Math.round(profile.extraAuto * 100)}% of otherwise non-stopping autos; about 5–7 s each.`,
      `In-lane loading: ${Math.round(profile.extraVan * 100)}% of otherwise non-stopping delivery vans; about 6–10 s each.`,
      `Lane cutting: ${Math.round(profile.cuttingShare * 100)}% of car/auto drivers seek smaller rear gaps and reconsider paths more readily; moves still require collision clearance.`,
      `Scheduled passenger stops: ${violationsInput.value}% in-lane above. Bus arrival frequency and 9–13 s boarding dwell unchanged; lower-road stops remain in bays.`
    ];
    const list = document.getElementById('violation-list'); list.replaceChildren();
    for (const description of descriptions) { const li = document.createElement('li'); li.textContent = description; list.append(li); }
  }
  for (const input of [inflowInput, violationsInput]) {
    input.addEventListener('input', () => {
      settingLabels();
      document.getElementById('settings-status').textContent = 'Release the slider to apply these settings and restart both roads.';
    });
    input.addEventListener('change', () => {
      settingLabels(); reset();
      document.getElementById('settings-status').textContent = `Applied: ${Number(inflowInput.value).toLocaleString()} PCU/h per road (${(Number(inflowInput.value) / 60).toFixed(1)} PCU/min); upper-road violations ${violationsInput.value}%. Both roads restarted; PCU window reset.${paused ? ' Press Play to run.' : ''}`;
    });
  }
  for (const button of document.querySelectorAll('[data-demand]')) button.addEventListener('click', () => {
    inflowInput.value = button.dataset.demand;
    inflowInput.dispatchEvent(new Event('change'));
  });
  media.addEventListener('change', event => { paused = event.matches; syncPause(); });
  document.addEventListener('visibilitychange', () => { last = null; accumulated = 0; });
  window.addEventListener('resize', resize);
  function frame(now) {
    if (last !== null && !paused && !ended && !document.hidden) {
      accumulated += Math.min((now - last) / 1000, .1) * rate;
      while (accumulated >= model.DT) { model.step(sim); accumulated -= model.DT; }
      draw();
    }
    last = now; requestAnimationFrame(frame);
  }
  settingLabels(); reset(); resize(); syncPause(); requestAnimationFrame(frame);
})();
