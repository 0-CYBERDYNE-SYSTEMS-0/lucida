(() => {
  const $ = (sel, el = document) => el.querySelector(sel);
  const state = {
    session: null,
    page: 0,
    cache: new Map(),
    pointer: { x: 0.5, y: 0.5 },
    plateOpen: true,
    stars: [],
  };

  const gate = $("#gate");
  const deck = $("#deck");
  const raising = $("#raising");
  const stage = $("#stage");
  const fileInput = $("#file");
  const plateImg = $("#plate-img");
  const plateWrap = $("#plate-wrap");
  const strip = $("#strip");
  const sceneBleed = $("#scene-bleed");
  const voidCanvas = $("#void");
  const vctx = voidCanvas.getContext("2d");

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function media(chamber, rel) {
    if (!rel) return "";
    return `${chamber.media_base}/${rel}`;
  }

  async function openDemo() {
    showRaising("opening the sample atlas");
    const res = await fetch("/api/demo", { method: "POST" });
    if (!res.ok) throw new Error(await res.text());
    await enter(await res.json());
  }

  async function openFile(file) {
    showRaising("cutting signatures");
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/open", { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    await enter(await res.json());
  }

  async function enter(session) {
    state.session = session;
    state.page = 0;
    state.cache.clear();
    gate.hidden = true;
    deck.hidden = false;
    $("#book-title").textContent = session.title || "LUCIDA";
    buildStrip(session.page_count);
    await showPage(0);
  }

  function buildStrip(n) {
    strip.innerHTML = "";
    for (let i = 0; i < n; i++) {
      const b = document.createElement("button");
      b.className = "leaf";
      b.type = "button";
      b.textContent = String(i + 1).padStart(2, "0");
      b.addEventListener("click", () => showPage(i));
      strip.appendChild(b);
    }
  }

  function showRaising(msg) {
    raising.hidden = false;
    $("#raising-msg").textContent = msg;
  }
  function hideRaising() {
    raising.hidden = true;
  }

  async function fetchPage(i) {
    if (state.cache.has(i)) return state.cache.get(i);
    const sid = state.session.id;
    const res = await fetch(`/api/session/${sid}/page/${i}`);
    if (!res.ok) throw new Error(await res.text());
    const chamber = await res.json();
    state.cache.set(i, chamber);
    return chamber;
  }

  async function showPage(i) {
    if (!state.session) return;
    i = Math.max(0, Math.min(state.session.page_count - 1, i));
    state.page = i;
    showRaising(`raising chamber ${String(i + 1).padStart(2, "0")}`);
    try {
      const chamber = await fetchPage(i);
      renderChamber(chamber);
      prefetch(i + 1);
      prefetch(i - 1);
    } catch (err) {
      stage.innerHTML = `<p class="ch-lede">${esc(err.message || err)}</p>`;
    } finally {
      hideRaising();
    }
  }

  function prefetch(i) {
    if (!state.session || i < 0 || i >= state.session.page_count) return;
    if (state.cache.has(i)) return;
    fetchPage(i).catch(() => {});
  }

  function renderChamber(c) {
    $("#book-meta").textContent = `chamber ${String(c.index + 1).padStart(2, "0")} / ${String(c.page_count).padStart(2, "0")}`;
    $("#kind-plaque").textContent = c.kind;
    $("#readtime").textContent = `${c.reading_seconds}s · ${c.word_count} words`;
    [...strip.children].forEach((el, idx) => el.classList.toggle("on", idx === c.index));

    const plate = media(c, c.raster);
    plateImg.src = plate;
    plateWrap.classList.toggle("off", !state.plateOpen);
    const art = media(c, c.plate);
    if (art) {
      sceneBleed.style.backgroundImage = `url("${art}")`;
      sceneBleed.classList.add("on");
    }

    const kicker = `${c.kind} · page ${c.index + 1}`;
    const stats = (c.stats || [])
      .map((s) => `<div class="inst"><div class="v">${esc(s.value)}</div><div class="l">${esc(s.label)}</div></div>`)
      .join("");
    const keys = (c.keywords || [])
      .slice(0, 10)
      .map((k) => `<span>${esc(k.word)}</span>`)
      .join("");
    const body = (c.body || []).map((p) => `<p>${esc(p)}</p>`).join("");
    const quote = (c.quotes && c.quotes[0]) || "";
    const figs = (c.images || [])
      .map((im) => `<img src="${esc(media(c, im.file))}" alt="" />`)
      .join("");
    const quiz = c.question
      ? `<button type="button" class="quiz" id="quiz"><b>recall</b><p class="q">${esc(c.question)}</p><p class="a">${esc(c.answer || "")}</p></button>`
      : "";

    let extra = "";
    if ((c.charts || []).length) extra += `<canvas class="viz" id="viz"></canvas>`;
    if (stats) extra += `<div class="instruments">${stats}</div>`;
    if (quiz) extra += quiz;
    if (quote && c.kind === "narrative") extra += `<p class="quote">${esc(quote)}</p>`;
    if (figs) extra += `<div class="figs">${figs}</div>`;
    if (keys) extra += `<div class="keywords">${keys}</div>`;

    // chamber JSON is escaped via esc(); media URLs are server-minted paths
    stage.innerHTML = `
      <article class="ch ${esc(c.kind)}">
        <header>
          <p class="ch-kicker">${esc(kicker)}</p>
          <h2 class="ch-title">${esc(c.title)}</h2>
          ${c.idea ? `<p class="idea">${esc(c.idea)}</p>` : ""}
          ${c.lede && c.lede !== c.idea ? `<p class="ch-lede">${esc(c.lede)}</p>` : ""}
        </header>
        <div>
          ${extra}
          ${body && c.kind !== "title" ? `<div class="ch-body">${body}</div>` : ""}
        </div>
      </article>`;

    if ((c.charts || []).length) drawChart($("#viz"), c.charts[0]);
    const quizBtn = $("#quiz");
    if (quizBtn) quizBtn.addEventListener("click", () => quizBtn.classList.toggle("open"));
  }

  function drawChart(canvas, chart) {
    if (!canvas || !chart) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = canvas.clientWidth || 640;
    const h = canvas.clientHeight || 240;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    const labels = chart.labels || [];
    const seriesList = (chart.series || []).slice(0, 3);
    if (!seriesList.length) return;
    const log = chart.scale === "log";
    const pos = [];
    seriesList.forEach((s) => (s.values || []).forEach((v) => { if (v > 0) pos.push(v); }));
    if (!pos.length) return;
    const minp = Math.min(...pos);
    const maxp = Math.max(...pos);
    const pad = { l: log ? 44 : 28, r: 16, t: 22, b: 28 };
    const iw = w - pad.l - pad.r;
    const ih = h - pad.t - pad.b;
    const colors = ["#8eecc8", "#d4b45a", "#e07a4a"];
    const n = Math.max(...seriesList.map((s) => (s.values || []).length), 1);
    const yOf = (v) => {
      if (log) {
        const lv = Math.log10(Math.max(v, minp / 10));
        const lmin = Math.log10(minp / 10);
        const lmax = Math.log10(maxp);
        return pad.t + ih - ((lv - lmin) / Math.max(1e-9, lmax - lmin)) * ih;
      }
      return pad.t + ih - (v / maxp) * ih;
    };
    ctx.strokeStyle = "rgba(212,180,90,0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.l, pad.t);
    ctx.lineTo(pad.l, h - pad.b);
    ctx.lineTo(w - pad.r, h - pad.b);
    ctx.stroke();
    ctx.font = "10px 'Share Tech Mono', monospace";
    ctx.fillStyle = "#8a8376";
    ctx.fillText(log ? "log" : chart.type, pad.l, 12);
    seriesList.forEach((s, si) => {
      ctx.fillStyle = colors[si % colors.length];
      ctx.fillText(String(s.name || "").slice(0, 18), pad.l + 40 + si * 110, 12);
    });
    seriesList.forEach((s, si) => {
      const vals = s.values || [];
      const col = colors[si % colors.length];
      ctx.strokeStyle = col;
      if (chart.type === "line") {
        ctx.beginPath();
        vals.forEach((v, i) => {
          const x = pad.l + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
          const y = yOf(v);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      } else {
        const gap = 6;
        const bw = Math.max(3, iw / n - gap);
        const slice = bw / seriesList.length;
        vals.forEach((v, i) => {
          const x = pad.l + i * (bw + gap) + si * slice;
          const y = yOf(v);
          ctx.strokeRect(x, y, Math.max(2, slice - 1), h - pad.b - y);
        });
      }
    });
    ctx.fillStyle = "#8a8376";
    labels.forEach((lb, i) => {
      if (n > 8 && i % 2) return;
      ctx.fillText(String(lb).slice(0, 10), pad.l + (i + 0.05) * (iw / n), h - 8);
    });
  }

  function resizeVoid() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    voidCanvas.width = innerWidth * dpr;
    voidCanvas.height = innerHeight * dpr;
    voidCanvas.style.width = innerWidth + "px";
    voidCanvas.style.height = innerHeight + "px";
    vctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    state.stars = Array.from({ length: 140 }, () => ({
      x: Math.random() * innerWidth,
      y: Math.random() * innerHeight,
      r: Math.random() * 1.4 + 0.2,
      v: Math.random() * 0.25 + 0.02,
      a: Math.random() * 0.5 + 0.2,
    }));
  }

  function tick() {
    const w = innerWidth;
    const h = innerHeight;
    vctx.fillStyle = "rgba(8,8,12,0.35)";
    vctx.fillRect(0, 0, w, h);
    for (const s of state.stars) {
      s.y += s.v;
      if (s.y > h) s.y = 0;
      vctx.fillStyle = `rgba(243,234,216,${s.a})`;
      vctx.beginPath();
      vctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      vctx.fill();
    }
    const px = (state.pointer.x - 0.5) * 24;
    const py = (state.pointer.y - 0.5) * 16;
    vctx.strokeStyle = "rgba(212,180,90,0.12)";
    vctx.beginPath();
    vctx.arc(w * 0.5 + px, h * 0.42 + py, 80, 0, Math.PI * 2);
    vctx.stroke();
    requestAnimationFrame(tick);
  }

  function onPointer(e) {
    state.pointer.x = e.clientX / innerWidth;
    state.pointer.y = e.clientY / innerHeight;
    const frame = $("#plate-frame");
    if (!frame) return;
    const ry = (state.pointer.x - 0.5) * -24 - 18;
    const rx = (state.pointer.y - 0.5) * 10 + 6;
    frame.style.transform = `rotateY(${ry}deg) rotateX(${rx}deg)`;
  }

  function onKey(e) {
    if (e.target && ["INPUT", "TEXTAREA"].includes(e.target.tagName)) return;
    if (e.key === "ArrowRight" || e.key === "j") showPage(state.page + 1);
    if (e.key === "ArrowLeft" || e.key === "k") showPage(state.page - 1);
    if (e.key === " ") {
      e.preventDefault();
      state.plateOpen = !state.plateOpen;
      plateWrap.classList.toggle("off", !state.plateOpen);
    }
    if (e.key === "r") {
      const q = $("#quiz");
      if (q) q.classList.toggle("open");
    }
    if (e.key === "f") {
      if (!document.fullscreenElement) document.documentElement.requestFullscreen().catch(() => {});
      else document.exitFullscreen().catch(() => {});
    }
    if (e.key === "Escape" && !deck.hidden) {
      /* stay in deck */
    }
  }

  function bindDrop() {
    const root = document.body;
    const over = (e) => {
      e.preventDefault();
      root.classList.add("drag");
    };
    const leave = (e) => {
      e.preventDefault();
      root.classList.remove("drag");
    };
    root.addEventListener("dragover", over);
    root.addEventListener("dragenter", over);
    root.addEventListener("dragleave", leave);
    root.addEventListener("drop", (e) => {
      e.preventDefault();
      root.classList.remove("drag");
      const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (f) openFile(f).catch((err) => alert(err.message || err));
    });
  }

  $("#demo").addEventListener("click", () => openDemo().catch((err) => alert(err.message || err)));
  $("#pick").addEventListener("click", () => fileInput.click());
  $("#new-book").addEventListener("click", () => {
    deck.hidden = true;
    gate.hidden = false;
    sceneBleed.classList.remove("on");
    state.session = null;
  });
  fileInput.addEventListener("change", () => {
    const f = fileInput.files && fileInput.files[0];
    if (f) openFile(f).catch((err) => alert(err.message || err));
    fileInput.value = "";
  });
  window.addEventListener("mousemove", onPointer);
  window.addEventListener("keydown", onKey);
  window.addEventListener("resize", resizeVoid);
  bindDrop();
  resizeVoid();
  tick();
})();
