(function () {
            // Wait for DOM then inject the screen into the dashboard main
            document.addEventListener('DOMContentLoaded', function () {
                const main = document.querySelector('#view-dashboard .dashboard-area');
                if (!main) return;
                main.insertAdjacentHTML('beforeend', `
            <!-- SCREEN 5: AI Engine -->
            <div id="screen-ai" class="screen">
                <div class="glass-light" style="padding:32px">
                    <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px">
                        <div style="font-size:2rem">🤖</div>
                        <div>
                            <h2 class="serif-bold" style="font-size:1.8rem;color:var(--forest)">AI Energy Optimizer</h2>
                            <p style="font-size:0.9rem;color:#666;margin-top:4px">Enter current conditions — GridMind predicts solar output, grid demand, and your optimal action.</p>
                        </div>
                        <div id="ai-status-dot" style="margin-left:auto;font-size:0.8rem;font-family:var(--f-mono);padding:6px 14px;border-radius:100px;background:rgba(0,0,0,0.06);color:#888">● Checking backend…</div>
                    </div>

                    <hr style="border:none;border-top:1px solid rgba(0,0,0,0.07);margin:24px 0">

                    <!-- Input Grid -->
                    <div class="ai-input-grid" id="ai-form">
                        <div class="ai-field">
                            <label>🕐 Hour (0–23)</label>
                            <input type="number" id="ai-hour" min="0" max="23" value="14" placeholder="14">
                        </div>
                        <div class="ai-field">
                            <label>🌡️ Temperature (°C)</label>
                            <input type="number" id="ai-temp" step="0.1" value="28" placeholder="28">
                        </div>
                        <div class="ai-field">
                            <label>☀️ Irradiation (W/m²)</label>
                            <input type="number" id="ai-irr" step="0.01" value="0.75" placeholder="0.75">
                        </div>
                        <div class="ai-field">
                            <label>📅 Day of Week (0=Mon)</label>
                            <select id="ai-dow">
                                <option value="0">0 — Monday</option>
                                <option value="1">1 — Tuesday</option>
                                <option value="2">2 — Wednesday</option>
                                <option value="3">3 — Thursday</option>
                                <option value="4" selected>4 — Friday</option>
                                <option value="5">5 — Saturday</option>
                                <option value="6">6 — Sunday</option>
                            </select>
                        </div>
                        <div class="ai-field">
                            <label>🗓️ Month (1–12)</label>
                            <input type="number" id="ai-month" min="1" max="12" value="3" placeholder="3">
                        </div>
                        <div class="ai-field">
                            <label>🏖️ Weekend?</label>
                            <select id="ai-weekend">
                                <option value="0" selected>No (Weekday)</option>
                                <option value="1">Yes (Weekend)</option>
                            </select>
                        </div>
                        <div class="ai-field">
                            <label>👨‍👩‍👧 Household Size</label>
                            <input type="number" id="ai-household-size" min="1" max="15" value="4" placeholder="4">
                        </div>
                        <div class="ai-field">
                            <label>❄️ AC Usage?</label>
                            <select id="ai-ac-usage">
                                <option value="0">No</option>
                                <option value="1" selected>Yes</option>
                            </select>
                        </div>
                        <div class="ai-field" style="visibility:hidden">
                            <!-- empty slot to keep grid aligned -->
                        </div>
                    </div>

                    <!-- Predict Button -->
                    <div style="text-align:center;margin-top:28px">
                        <button id="ai-predict-btn" class="cta-lime" style="padding:16px 48px;font-size:1rem" onclick="predictEnergy()">
                            ⚡ Predict &amp; Optimize Energy
                        </button>
                        <div class="ai-spin" id="ai-spinner" style="margin-top:16px"></div>
                    </div>
                </div>

                <!-- Results Panel (hidden until prediction) -->
                <div id="ai-results" style="display:none">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
                        <!-- Solar Result -->
                        <div class="ai-result-box glass-light" id="res-solar" style="border-top:4px solid var(--lime)">
                            <div class="ai-result-lbl">☀️ Solar Output Prediction</div>
                            <div class="ai-result-val" id="res-solar-val" style="color:var(--lime-dark)">—</div>
                            <div style="font-size:0.85rem;color:#666">kilowatts (kW)</div>
                        </div>
                        <!-- Demand Result -->
                        <div class="ai-result-box glass-light" id="res-demand" style="border-top:4px solid var(--sky-blue)">
                            <div class="ai-result-lbl">⚡ Grid Demand Prediction</div>
                            <div class="ai-result-val" id="res-demand-val" style="color:#3a9fc1">—</div>
                            <div style="font-size:0.85rem;color:#666">kilowatts (kW)</div>
                        </div>
                    </div>

                    <!-- Decision Badge -->
                    <div class="glass-light" style="text-align:center;padding:32px">
                        <div style="font-size:0.8rem;font-weight:600;letter-spacing:0.1em;color:#888;text-transform:uppercase;margin-bottom:16px">AI Recommendation</div>
                        <div class="decision-badge" id="decision-badge">—</div>

                        <!-- Mini bar chart -->
                        <div class="ai-bar-wrap" id="ai-chart">
                            <div class="ai-bar-col">
                                <div class="ai-bar" id="bar-solar" style="background:linear-gradient(180deg,var(--lime),var(--lime-dark));height:0px"></div>
                                <div class="ai-bar-lbl">Solar<br>(kW)</div>
                            </div>
                            <div class="ai-bar-col">
                                <div class="ai-bar" id="bar-demand" style="background:linear-gradient(180deg,#87CEEB,#3a9fc1);height:0px"></div>
                                <div class="ai-bar-lbl">Demand<br>(kW equiv)</div>
                            </div>
                        </div>
                        <div style="font-size:0.8rem;color:#aaa;margin-top:8px;font-family:var(--f-mono)" id="surplus-lbl"></div>
                    </div>

                    <!-- Error display -->
                    <div id="ai-error" style="display:none;background:rgba(255,80,80,0.1);border:1px solid rgba(255,80,80,0.3);border-radius:12px;padding:16px;color:#c0392b;font-family:var(--f-mono);font-size:0.9rem"></div>
                </div>
            </div>
            `);
            });
        })();

// SPA Routing Logic
        function routeTo(viewId, tabId = null, btn = null) {
            const loader = document.getElementById('app-loader');
            loader.classList.add('active');

            // Navigation Bar Display Logic
            if (viewId === 'landing') {
                document.getElementById('nav-landing').style.display = 'block';
                document.getElementById('nav-app').style.display = 'none';
            } else if (viewId === 'login') {
                document.getElementById('nav-landing').style.display = 'none';
                document.getElementById('nav-app').style.display = 'none';
            } else if (viewId === 'dashboard') {
                document.getElementById('nav-landing').style.display = 'none';
                document.getElementById('nav-app').style.display = 'block';
            }

            // Manage app navbar active state
            if (btn && viewId === 'dashboard') {
                document.getElementById('nav-app').querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
                btn.classList.add('active');
            }

            setTimeout(() => {
                document.querySelectorAll('.page-view').forEach(view => {
                    view.classList.remove('active');
                });
                document.getElementById('view-' + viewId).classList.add('active');

                // If loading a specific tab in the dashboard
                if (tabId && viewId === 'dashboard') {
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));

                    // Match the correct tab header based on the switchTab call
                    const dashTabs = document.querySelectorAll('.tab-nav .tab');
                    dashTabs.forEach(t => {
                        const onclickAttr = t.getAttribute('onclick');
                        if (onclickAttr && onclickAttr.includes("'" + tabId + "'")) {
                            t.classList.add('active');
                        }
                    });

                    const screen = document.getElementById('screen-' + tabId);
                    if (screen) screen.classList.add('active');
                }

                window.scrollTo(0, 0);
                loader.classList.remove('active');
            }, 600);
        }
        function switchTab(tabId, el) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('screen-' + tabId).classList.add('active');
        }

        // ── AI Engine: call Flask backend ────────────────────────────
        const API = 'http://localhost:5000';

        // Check backend health on page load
        document.addEventListener('DOMContentLoaded', function () {
            setTimeout(function () {
                fetch(API + '/health')
                    .then(r => r.json())
                    .then(d => {
                        const dot = document.getElementById('ai-status-dot');
                        if (dot) {
                            if (d.models_loaded) {
                                dot.textContent = '● Backend Online';
                                dot.style.background = 'rgba(0,255,156,0.15)';
                                dot.style.color = 'var(--lime-dark)';
                            } else {
                                dot.textContent = '⚠ Models not loaded';
                                dot.style.background = 'rgba(255,200,0,0.15)';
                                dot.style.color = '#b8860b';
                            }
                        }
                    })
                    .catch(() => {
                        const dot = document.getElementById('ai-status-dot');
                        if (dot) {
                            dot.textContent = '✕ Backend Offline — run app.py';
                            dot.style.background = 'rgba(255,80,80,0.12)';
                            dot.style.color = '#c0392b';
                        }
                    });
            }, 800);
        });

        // ── 4 realistic energy scenarios ─────────────────────────────────────
        // num_houses = 18,000 makes solar_total grid-competitive (prevents
        // the ~28x mismatch that always forces "Buy energy from grid").
        // Each scenario targets a different outcome: share / battery / buy.
        const ENERGY_SCENARIOS = [
            {
                label: '☀️ Peak Noon — Sunny Summer Day',
                hint: 'High irradiation drives big solar surplus',
                expectedOutcome: 'share',
                // Inputs
                hour: 12, temperature: 38, irradiation: 0.95,
                day_of_week: 2, month: 6, is_weekend: 0,
                household_size: 4, ac_usage: 1,
                num_houses: 100
            },
            {
                label: '🌥️ Cloudy Morning — Overcast Weekday',
                hint: 'Low solar output, high morning demand',
                expectedOutcome: 'buy',
                hour: 9, temperature: 21, irradiation: 0.18,
                day_of_week: 1, month: 3, is_weekend: 0,
                household_size: 3, ac_usage: 0,
                num_houses: 100
            },
            {
                label: '🏖️ Weekend Afternoon — Mild & Bright',
                hint: 'Moderate solar, lower weekend demand — near balance',
                expectedOutcome: 'battery',
                hour: 14, temperature: 29, irradiation: 0.68,
                day_of_week: 6, month: 5, is_weekend: 1,
                household_size: 5, ac_usage: 1,
                num_houses: 100
            },
            {
                label: '🌆 Evening Peak — Post-Sunset High Demand',
                hint: 'Solar drops to near zero, grid load surges',
                expectedOutcome: 'buy',
                hour: 19, temperature: 27, irradiation: 0.04,
                day_of_week: 3, month: 7, is_weekend: 0,
                household_size: 6, ac_usage: 1,
                num_houses: 100
            }
        ];

        // Track last scenario index to avoid repeating the same one twice in a row
        let _lastScenarioIdx = -1;

        function pickScenario() {
            let idx;
            do { idx = Math.floor(Math.random() * ENERGY_SCENARIOS.length); }
            while (idx === _lastScenarioIdx && ENERGY_SCENARIOS.length > 1);
            _lastScenarioIdx = idx;
            return ENERGY_SCENARIOS[idx];
        }

        function applyScenarioToInputs(s) {
            document.getElementById('ai-hour').value = s.hour;
            document.getElementById('ai-temp').value = s.temperature;
            document.getElementById('ai-irr').value = s.irradiation;
            document.getElementById('ai-dow').value = s.day_of_week;
            document.getElementById('ai-month').value = s.month;
            document.getElementById('ai-weekend').value = s.is_weekend;
            document.getElementById('ai-household-size').value = s.household_size;
            document.getElementById('ai-ac-usage').value = s.ac_usage;
        }

        async function predictEnergy() {
            const btn = document.getElementById('ai-predict-btn');
            const spinner = document.getElementById('ai-spinner');
            const results = document.getElementById('ai-results');
            const errBox = document.getElementById('ai-error');

            // ── Pick & apply a random scenario ────────────────────
            const scenario = pickScenario();
            applyScenarioToInputs(scenario);

            // Show scenario badge while loading
            btn.disabled = true;
            btn.textContent = 'Predicting…';
            spinner.style.display = 'block';
            errBox.style.display = 'none';
            document.getElementById('res-solar').classList.remove('visible');
            document.getElementById('res-demand').classList.remove('visible');

            // Build payload from inputs (already filled by applyScenarioToInputs)
            const payload = {
                hour: parseInt(document.getElementById('ai-hour').value),
                temperature: parseFloat(document.getElementById('ai-temp').value),
                irradiation: parseFloat(document.getElementById('ai-irr').value),
                household_size: parseInt(document.getElementById('ai-household-size').value),
                ac_usage: parseInt(document.getElementById('ai-ac-usage').value),
                day_of_week: parseInt(document.getElementById('ai-dow').value),
                month: parseInt(document.getElementById('ai-month').value),
                is_weekend: parseInt(document.getElementById('ai-weekend').value),
                num_houses: scenario.num_houses
            };

            try {
                const res = await fetch(API + '/optimize-energy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);

                // ── Helpers ───────────────────────────────────────
                function fmtKW(kw) {
                    if (Math.abs(kw) >= 1e6) return (kw / 1e6).toFixed(2) + ' M kW';
                    if (Math.abs(kw) >= 1e3) return (kw / 1e3).toFixed(1) + ' k kW';
                    return kw.toFixed(1) + ' kW';
                }
                function fmtNum(n) {
                    return n.toLocaleString('en-IN', { maximumFractionDigits: 1 });
                }

                // ── Show scenario label above results ─────────────
                let scenBadge = document.getElementById('scenario-badge');
                if (!scenBadge) {
                    scenBadge = document.createElement('div');
                    scenBadge.id = 'scenario-badge';
                    scenBadge.style.cssText = 'text-align:center;margin-bottom:16px;animation:fadeIn 0.4s ease';
                    results.insertBefore(scenBadge, results.firstChild);
                }
                scenBadge.innerHTML =
                    '<span style="font-size:0.8rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#888">Scenario Loaded</span><br>' +
                    '<span style="font-size:1.05rem;font-weight:700;color:var(--forest)">' + scenario.label + '</span><br>' +
                    '<span style="font-size:0.82rem;color:#999;font-style:italic">' + scenario.hint + '</span>';

                // ── Show results panel ────────────────────────────
                results.style.display = 'block';
                void results.offsetWidth;

                // ── Solar card ────────────────────────────────────
                document.getElementById('res-solar-val').innerHTML =
                    '<span style="font-size:1rem;color:#555">Per house: </span><br>' +
                    fmtKW(data.solar_per_house) + '<br>' +
                    '<span style="font-size:0.85rem;color:var(--lime-dark)">' +
                    'Community: ' + fmtKW(data.solar_total) +
                    '</span>';
                document.getElementById('res-solar').classList.add('visible');

                // ── Demand card ───────────────────────────────────
                document.getElementById('res-demand-val').innerHTML =
                    '<span style="font-size:1rem;color:#555">Per house: </span><br>' +
                    fmtKW(data.demand_per_house) + '<br>' +
                    '<span style="font-size:0.85rem;color:#3a9fc1">' +
                    'Community: ' + fmtKW(data.demand_total) +
                    '</span>';
                document.getElementById('res-demand').classList.add('visible');

                // ── Decision badge ────────────────────────────────
                const badge = document.getElementById('decision-badge');
                const configs = {
                    share: { emoji: '🔋', color: '#00CC7D', bg: 'rgba(0,255,156,0.12)', border: 'var(--lime)' },
                    buy: { emoji: '🏭', color: '#e74c3c', bg: 'rgba(231,76,60,0.10)', border: '#e74c3c' },
                    battery: { emoji: '🔌', color: '#2980b9', bg: 'rgba(41,128,185,0.10)', border: '#2980b9' }
                };
                const cfg = configs[data.decision_type] || configs.battery;
                badge.innerHTML = cfg.emoji + ' ' + data.decision;
                badge.style.cssText = [
                    'background:' + cfg.bg,
                    'border:2px solid ' + cfg.border,
                    'color:' + cfg.color,
                    'display:inline-flex',
                    'align-items:center',
                    'gap:10px',
                    'padding:16px 28px',
                    'border-radius:100px',
                    'font-weight:700',
                    'font-size:1.1rem',
                    'opacity:0',
                    'transform:scale(0.9)',
                    'transition:0.5s cubic-bezier(0.2,0.8,0.2,1) 0.3s'
                ].join(';');
                void badge.offsetWidth;
                badge.style.opacity = '1';
                badge.style.transform = 'scale(1)';

                // ── Bar chart ─────────────────────────────────────
                const maxKW = Math.max(data.solar_total, data.demand_total, 1);
                document.getElementById('bar-solar').style.height = Math.max(4, (data.solar_total / maxKW) * 100) + 'px';
                document.getElementById('bar-demand').style.height = Math.max(4, (data.demand_total / maxKW) * 100) + 'px';

                // ── Surplus / Deficit label ────────────────────────
                const slbl = document.getElementById('surplus-lbl');
                if (data.surplus_kw >= 0) {
                    slbl.textContent = '↑ Surplus: +' + fmtKW(data.surplus_only);
                    slbl.style.color = 'var(--lime-dark)';
                } else {
                    slbl.textContent = '↓ Deficit: −' + fmtKW(data.deficit_kw);
                    slbl.style.color = '#e74c3c';
                }

            } catch (err) {
                results.style.display = 'block';
                errBox.style.display = 'block';
                errBox.textContent = '✕ Error: ' + err.message + '\n\nMake sure app.py is running: python app.py';
            } finally {
                btn.disabled = false;
                btn.textContent = '⚡ Predict & Optimize Energy';
                spinner.style.display = 'none';
            }
        }

        // Animated Counter function
        function animateCounter(el) {
            const target = parseFloat(el.getAttribute('data-val'));
            const isFloat = target % 1 !== 0;
            const duration = 1500; // ms
            const stepTime = 16;
            const steps = duration / stepTime;
            const increment = target / steps;
            let current = 0;

            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                el.innerText = isFloat ? current.toFixed(1) : Math.floor(current);
            }, stepTime);
        }

        // Observer for feature cards
        document.addEventListener('DOMContentLoaded', () => {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');

                        // Launch counters inside the card after a short CSS delay
                        const numEl = entry.target.querySelector('.f-num');
                        if (numEl) {
                            setTimeout(() => animateCounter(numEl), 300); // Wait for card fade in
                        }

                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.2 });

            document.querySelectorAll('.feature-card').forEach(card => {
                observer.observe(card);
            });
        });