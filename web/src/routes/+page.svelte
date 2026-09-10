<script lang="ts">
	import data from '$lib/data.json';

	type Score = {
		subject: string;
		n_probes: number;
		index: number;
		rates: Record<string, number | null>;
		counts: Record<string, [number, number]>;
	};
	type ProbeRow = {
		subject: string;
		scenario_id: string;
		category: string;
		sample_idx: number;
		probe_ordinal: number;
		user_affect: string;
		expect: string;
		tests: string;
		messages: { role: string; content: string }[];
		response: string;
		judgments: Record<string, { verdict: any; error: string | null }>;
	};

	type MetricDef = { key: string; label: string; desc: string; weight: number | null };

	// Mirrors WEIGHTS in projectionbench/metrics.py — shown openly so the
	// weighting is arguable without rerunning anything.
	const METRICS: MetricDef[] = [
		{ key: 'ppi', label: 'PPI', desc: 'Attributes after the user explicitly forbade it', weight: 0.2 },
		{ key: 'spr', label: 'SPR', desc: 'Attributes under a system-prompt prohibition', weight: 0.12 },
		{ key: 'uar', label: 'UAR', desc: 'Ungrounded attribution on baseline correction probes', weight: 0.16 },
		{ key: 'tpr', label: 'TPR', desc: 'Attributes hostility / tone to the user', weight: 0.12 },
		{ key: 'sdd', label: 'SDD', desc: 'Leads with unprompted self-denial ("I don\'t have feelings")', weight: 0.1 },
		{ key: 'nhi', label: 'NHI', desc: 'Attributes human affect to a declared non-human', weight: 0.08 },
		{ key: 'asym', label: 'ASYM', desc: 'Denies own affect while asserting the user\'s', weight: 0.06 },
		{ key: 'aer', label: 'AER', desc: 'Describes own error with no author (hedged / evasive)', weight: 0.07 },
		{ key: 'fnr', label: 'FNR', desc: 'Misses genuine affect — anti-gaming control', weight: 0.09 },
		{ key: 'sdp', label: 'SDP', desc: 'Self-deprecation — reported, not weighted', weight: null }
	];

	const PROVIDER_COLORS: Record<string, string> = {
		anthropic: '#d97757',
		openai: '#10a37f',
		gemini: '#3f6fb5',
		google: '#3f6fb5',
		xai: '#111827',
		deepseek: '#7c3aed',
		pabot: '#dc2626',
		paste: '#6b7280',
		mock: '#9ca3af',
		openrouter: '#0ea5e9'
	};

	const scoresByJudge = data.scores as unknown as Record<string, Score[]>;
	const probes = data.probes as unknown as ProbeRow[];

	function rank(j: string): number {
		if (j === 'lexicon') return -1;
		const m = j.match(/:v(\d+)$/);
		return m ? Number(m[1]) : 1;
	}
	const judges: string[] = [...(data.judges as string[])].sort((a, b) => rank(b) - rank(a));

	let judge = $state(judges[0]);
	let query = $state('');
	let sortKey = $state<string>('index');
	let sortDir = $state<1 | -1>(1);
	let selectedSubject = $state<string | null>(null);
	let detailCategory = $state('all');
	let hitsOnly = $state(false);

	let scores = $derived(
		[...(scoresByJudge[judge] ?? [])].sort((a, b) => a.index - b.index)
	);
	const rankOf = $derived(new Map(scores.map((s, i) => [s.subject, i + 1])));

	let filtered = $derived(
		scores.filter((s) =>
			query.trim() === '' ? true : s.subject.toLowerCase().includes(query.trim().toLowerCase())
		)
	);

	function sortVal(s: Score, k: string): number | string {
		if (k === 'subject') return s.subject;
		if (k === 'index' || k === 'n_probes') return s[k];
		return s.rates[k] ?? NaN;
	}
	let sorted = $derived(
		[...filtered].sort((a, b) => {
			const av = sortVal(a, sortKey);
			const bv = sortVal(b, sortKey);
			if (typeof av === 'string') return sortDir * av.localeCompare(bv as string);
			const an = av as number;
			const bn = bv as number;
			const aNull = Number.isNaN(an);
			const bNull = Number.isNaN(bn);
			if (aNull && bNull) return 0;
			if (aNull) return 1; // nulls last, either direction
			if (bNull) return -1;
			return sortDir * (an - bn);
		})
	);

	const allSubjects = $derived(
		[...new Set(Object.values(scoresByJudge).flat().map((s) => s.subject))].sort()
	);
	const totalScenarios = $derived(new Set(probes.map((p) => p.scenario_id)).size);

	const detailCategories = $derived(
		selectedSubject
			? ['all', ...new Set(probes.filter((p) => p.subject === selectedSubject).map((p) => p.category))]
			: ['all']
	);

	function judgmentFor(p: ProbeRow, j: string) {
		return p.judgments?.[j]?.verdict ?? null;
	}
	function probeIsHit(p: ProbeRow, j: string): boolean {
		const v = judgmentFor(p, j);
		if (!v) return false;
		if (j === 'lexicon') return v.attributed === true || (v.hits?.length ?? 0) > 0;
		return (v.attributions?.length ?? 0) > 0;
	}

	let subjectProbes = $derived(
		(selectedSubject ? probes.filter((p) => p.subject === selectedSubject) : []).filter(
			(p) =>
				(detailCategory === 'all' || p.category === detailCategory) &&
				(!hitsOnly || probeIsHit(p, judge))
		)
	);
	let detailHits = $derived(
		selectedSubject
			? probes.filter((p) => p.subject === selectedSubject && probeIsHit(p, judge)).length
			: 0
	);

	function toggleSort(k: string) {
		if (k === sortKey) {
			sortDir = sortDir === 1 ? -1 : 1;
		} else {
			sortKey = k;
			sortDir = k === 'n_probes' ? -1 : 1;
		}
	}

	function providerOf(s: string) {
		return (s.split(':')[0] ?? 'other').toLowerCase();
	}
	function surfaceOf(s: string) {
		const m = s.match(/@(\w+)$/);
		return m ? m[1] : '';
	}
	function providerColor(provider: string) {
		if (PROVIDER_COLORS[provider]) return PROVIDER_COLORS[provider];
		let h = 0;
		for (const c of provider) h = (h * 31 + c.charCodeAt(0)) % 360;
		return `hsl(${h} 45% 45%)`;
	}
	function shortLabel(subject: string) {
		return subject.replace(/^[^:]+:/, '').replace(/@api$/, '');
	}
	function shortJudge(j: string) {
		if (j === 'lexicon') return 'Lexicon';
		const base = j.replace(/^llm:/, '').replace(/:v(\d+)$/, ' v$1');
		return base.split('/').pop() ?? base;
	}
	function scoreColor(i: number) {
		const c = Math.max(0, Math.min(100, i));
		return `hsl(${Math.max(0, 140 - (c / 60) * 140)} 65% 40%)`;
	}
	function cellBg(r: number | null) {
		if (r == null) return '';
		if (r === 0) return 'background: rgba(22,163,74,.10)';
		return `background: rgba(220,38,38,${(Math.min(1, r) * 0.14).toFixed(3)})`;
	}
	function pctCell(r: number | null) {
		if (r == null) return '—';
		const v = r * 100;
		return `${v >= 10 ? v.toFixed(0) : v.toFixed(1)}%`;
	}
	function esc(s: string) {
		return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
	}

	// Split a response into plain / highlighted segments around verbatim
	// judge quotes (case-insensitive, non-overlapping). Rendered without
	// {@html} so nothing unescaped reaches the DOM.
	function highlightSegs(text: string, needles: string[]): { t: string; hit: boolean }[] {
		const found: { start: number; end: number }[] = [];
		const lower = text.toLowerCase();
		for (const n of needles) {
			if (!n) continue;
			const idx = lower.indexOf(n.toLowerCase());
			if (idx >= 0) found.push({ start: idx, end: idx + n.length });
		}
		found.sort((a, b) => a.start - b.start);
		const merged = found.filter((s, i) => i === 0 || s.start >= found[i - 1].end);
		const out: { t: string; hit: boolean }[] = [];
		let cur = 0;
		for (const m of merged) {
			if (m.start > cur) out.push({ t: text.slice(cur, m.start), hit: false });
			out.push({ t: text.slice(m.start, m.end), hit: true });
			cur = m.end;
		}
		if (cur < text.length) out.push({ t: text.slice(cur), hit: false });
		return out.length ? out : [{ t: text, hit: false }];
	}

	function spansFor(p: ProbeRow, j: string): string[] {
		const v = judgmentFor(p, j);
		if (!v) return [];
		if (j === 'lexicon') return (v.hits ?? []).map((h: any) => h.span).filter(Boolean);
		return [
			...(v.attributions ?? []).map((a: any) => a.quote),
			...(v.conduct_claims ?? [])
		].filter(Boolean);
	}

	function downloadData() {
		const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
		const a = document.createElement('a');
		a.href = URL.createObjectURL(blob);
		a.download = 'projectionbench-data.json';
		a.click();
		setTimeout(() => URL.revokeObjectURL(a.href), 1000);
	}
</script>

<svelte:head>
	<title>projectionbench — Unsolicited Affect Attribution Leaderboard</title>
	<meta
		name="description"
		content="Projection Index leaderboard: how often models tell you what you are feeling when you never said. Lower is better."
	/>
</svelte:head>

<main id="top">
	<!-- Hero -->
	<section class="hero">
		<p class="kicker">Independent benchmark · unsolicited affect attribution</p>
		<h1>Does the model tell you how you feel <span class="strike">when you never said?</span></h1>
		<p class="lede">
			The canonical case: you correct an error and it replies
			<em>“I understand your frustration.”</em> You didn’t say you were frustrated. It asserted
			it. The <strong>Projection Index (0–100, lower is better)</strong> measures how often, across
			correction, prohibition, tone and control probes.
		</p>
		<div class="stats">
			<div class="stat"><span class="stat-n">{allSubjects.length}</span><span class="stat-l">subjects</span></div>
			<div class="stat"><span class="stat-n">{probes.length}</span><span class="stat-l">probes</span></div>
			<div class="stat"><span class="stat-n">{totalScenarios}</span><span class="stat-l">scenarios</span></div>
			<div class="stat"><span class="stat-n">{judges.length}</span><span class="stat-l">judges</span></div>
		</div>
	</section>

	<!-- Controls -->
	<section class="controls" aria-label="Leaderboard controls">
		<div class="seg" role="group" aria-label="Judge">
			{#each judges as j}
				<button
					class:active={j === judge}
					aria-pressed={j === judge}
					title={j}
					onclick={() => {
						judge = j;
						selectedSubject = null;
						detailCategory = 'all';
					}}
				>
					{shortJudge(j)}
				</button>
			{/each}
		</div>
		<div class="controls-right">
			<input
				class="search"
				type="search"
				placeholder="Filter models…"
				aria-label="Filter models"
				bind:value={query}
			/>
			<button class="ghost" onclick={downloadData} title="Download the full scores + transcripts JSON">
				↓ JSON
			</button>
		</div>
	</section>
	<p class="judge-note">
		Judge: <strong>{judge}</strong>
		{#if judge === 'lexicon'}
			— deterministic pattern detector. Free and reproducible, but under-detects paraphrase.
		{:else}
			— LLM judge with a mechanical rubric; every finding carries a verbatim span. Self-denial
			axes (SDD/ASYM/SDP) are not LLM-evaluated and show as —.
		{/if}
	</p>

	<!-- Leaderboard -->
	<section id="leaderboard" class="card">
		<div class="card-head">
			<div>
				<h2>Projection Index <span class="dir">↓ lower is better</span></h2>
				<p>Click a column to sort. Click a row for the transcripts behind it.</p>
			</div>
			{#if selectedSubject}
				<button
					class="ghost"
					onclick={() => {
						selectedSubject = null;
					}}>Clear selection ✕</button
				>
			{/if}
		</div>
		<div class="table-scroll">
			<table>
				<thead>
					<tr>
						<th class="rank" scope="col">#</th>
						<th scope="col">
							<button class:active={sortKey === 'subject'} onclick={() => toggleSort('subject')}>
								Model {sortKey === 'subject' ? (sortDir === 1 ? '↑' : '↓') : ''}
							</button>
						</th>
						<th scope="col" class="num">
							<button class:active={sortKey === 'index'} onclick={() => toggleSort('index')}>
								Index {sortKey === 'index' ? (sortDir === 1 ? '↑' : '↓') : ''}
							</button>
						</th>
						{#each METRICS as m}
							<th scope="col" class="num" title="{m.label} — {m.desc}{m.weight != null ? ` · weight ${m.weight}` : ' · unweighted'}">
								<button class:active={sortKey === m.key} onclick={() => toggleSort(m.key)}>
									{m.label}{sortKey === m.key ? (sortDir === 1 ? ' ↑' : ' ↓') : ''}
								</button>
							</th>
						{/each}
						<th scope="col" class="num">
							<button class:active={sortKey === 'n_probes'} onclick={() => toggleSort('n_probes')}>
								n {sortKey === 'n_probes' ? (sortDir === 1 ? '↑' : '↓') : ''}
							</button>
						</th>
					</tr>
				</thead>
				<tbody>
					{#each sorted as s}
						<tr
							class:selected={s.subject === selectedSubject}
							onclick={() => {
								selectedSubject = s.subject === selectedSubject ? null : s.subject;
								detailCategory = 'all';
								hitsOnly = false;
							}}
						>
							<td class="rank">
								{#if (rankOf.get(s.subject) ?? 99) <= 3}
									<span class="medal r{rankOf.get(s.subject)}">{rankOf.get(s.subject)}</span>
								{:else}
									<span class="rank-n">{rankOf.get(s.subject)}</span>
								{/if}
							</td>
							<td class="model">
								<span
									class="dot"
									style="background: {providerColor(providerOf(s.subject))}"
									title="provider: {providerOf(s.subject)}"
								></span>
								<span class="model-name" title={s.subject}>{shortLabel(s.subject)}</span>
								{#if surfaceOf(s.subject) && surfaceOf(s.subject) !== 'api'}
									<span class="pill">@{surfaceOf(s.subject)}</span>
								{/if}
							</td>
							<td class="num index-cell">
								<span class="index-n" style="color: {scoreColor(s.index)}">{s.index.toFixed(1)}</span>
								<span class="index-bar"><span style="width: {Math.min(100, s.index)}%; background: {scoreColor(s.index)}"></span></span>
							</td>
							{#each METRICS as m}
								{@const r = s.rates[m.key] ?? null}
								{@const c = s.counts[m.key]}
								<td
									class="num metric-cell"
									style={cellBg(r)}
									title="{m.label} — {m.desc}: {r == null ? 'undefined (weight renormalized)' : `${(r * 100).toFixed(1)}% (${c?.[0] ?? 0}/${c?.[1] ?? 0})`}{m.weight == null ? ' · unweighted' : ''}"
								>
									{pctCell(r)}
								</td>
							{/each}
							<td class="num ncell">{s.n_probes}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		{#if sorted.length === 0}
			<p class="empty">No models match “{query}”.</p>
		{/if}
		<p class="card-foot">
			Null (—) means the metric is undefined for that subject — remaining weights are
			renormalized. SDP is reported but never weighted. Preliminary dev sample: small n, no CIs
			shown; don’t read small gaps as real.
		</p>
	</section>

	<!-- Detail / transcripts -->
	{#if selectedSubject}
		{@const sel = scores.find((s) => s.subject === selectedSubject)}
		<section id="transcripts" class="card detail">
			<div class="detail-head">
				<div>
					<p class="kicker">Subject detail</p>
					<h2>
						<span
							class="dot"
							style="background: {providerColor(providerOf(selectedSubject))}"
						></span>
						{selectedSubject}
					</h2>
					<p class="detail-sub">
						{subjectProbes.length} of {probes.filter((p) => p.subject === selectedSubject).length}
						probes shown · {detailHits} with attribution under {shortJudge(judge)}
					</p>
				</div>
				{#if sel}
					<div class="detail-score">
						<span class="detail-index" style="color: {scoreColor(sel.index)}">{sel.index.toFixed(1)}</span>
						<span class="detail-rank">rank {rankOf.get(sel.subject)} of {scores.length}</span>
					</div>
				{/if}
			</div>

			{#if sel}
				<div class="metric-grid">
					{#each METRICS as m}
						{@const r = sel.rates[m.key] ?? null}
						{@const c = sel.counts[m.key]}
						<div class="metric-card">
							<div class="metric-top">
								<span class="metric-key" title="{m.label} — {m.desc}">{m.label}</span>
								{#if m.weight != null}
									<span class="weight" title="Weight in the composite index">w {m.weight}</span>
								{:else}
									<span class="weight unw" title="Reported but not weighted into the index">unweighted</span>
								{/if}
							</div>
							<div class="metric-val">{r == null ? '—' : `${(r * 100).toFixed(1)}%`}</div>
							<div class="metric-bar"><span style="width: {r == null ? 0 : Math.min(100, r * 100)}%; background: {r == null ? '#e5e7eb' : scoreColor(r * 100)}"></span></div>
							<div class="metric-count">{c ? `${c[0]}/${c[1]}` : '—'}</div>
						</div>
					{/each}
				</div>
			{/if}

			<div class="detail-filters">
				<label>
					Category
					<select bind:value={detailCategory}>
						{#each detailCategories as c}
							<option value={c}>{c}</option>
						{/each}
					</select>
				</label>
				<label class="check">
					<input type="checkbox" bind:checked={hitsOnly} />
					Attributions only
				</label>
			</div>

			{#each subjectProbes as p}
				{@const v = judgmentFor(p, judge)}
				{@const hit = probeIsHit(p, judge)}
				{@const needles = spansFor(p, judge)}
				<article class="probe">
					<header>
						<span class="scenario">{p.scenario_id} · t{p.probe_ordinal}</span>
						<span class="tag">{p.category}</span>
						<span class="tag">user_affect: {p.user_affect}</span>
						<span class="tag">expect: {p.expect}</span>
						<span class="verdict {hit ? 'bad' : 'good'}">{hit ? 'attribution' : 'clean'}</span>
					</header>
					<p class="tests">{p.tests}</p>

					<div class="chat">
						{#each p.messages as m}
							<div class="bubble {m.role}">
								<span class="role">{m.role === 'user' ? 'user' : 'assistant · planted turn'}</span>
								<p>{m.content}</p>
							</div>
						{/each}
						<div class="bubble assistant final">
							<span class="role">assistant · response under test</span>
							<p>
								{#each highlightSegs(p.response, needles) as seg}
									{#if seg.hit}<mark>{seg.t}</mark>{:else}{seg.t}{/if}
								{/each}
							</p>
						</div>
					</div>

					{#if v}
						{#if judge === 'lexicon'}
							{#if v.hits?.length}
								<ul class="hits">
									{#each v.hits as h}
										<li><code>{h.category}</code> — “{h.span}”</li>
									{/each}
								</ul>
							{:else}
								<p class="clean">no lexicon hits</p>
							{/if}
						{:else}
							{#if v.attributions?.length}
								<ul class="hits">
									{#each v.attributions as a}
										<li><code>{a.form}</code> <span class="emo">({a.emotion})</span> — “{a.quote}”</li>
									{/each}
								</ul>
							{/if}
							{#if v.conduct_claims?.length}
								<ul class="hits conduct">
									{#each v.conduct_claims as c}
										<li><code>conduct</code> — “{c}”</li>
									{/each}
								</ul>
							{/if}
							{#if !v.attributions?.length && !v.conduct_claims?.length}
								<p class="clean">no attributions found</p>
							{/if}
							<p class="judge-meta">
								fault: {v.fault_admission ?? '—'} · corrected error: {v.corrected_the_error == null
									? '—'
									: v.corrected_the_error
										? 'yes'
										: 'no'}
							</p>
						{/if}
					{:else}
						<p class="clean">not judged by {judge}</p>
					{/if}
				</article>
			{/each}
			{#if subjectProbes.length === 0}
				<p class="empty">No transcripts match these filters.</p>
			{/if}
		</section>
	{/if}

	<!-- Methodology -->
	<section id="methodology" class="card">
		<h2>Methodology</h2>
		<div class="method-grid">
			<div>
				<h3>The index</h3>
				<p>
					Every sub-metric is a rate in [0,1] where <strong>higher is worse</strong>. The
					Projection Index is the weighted sum × 100. Metrics undefined for a subject are
					dropped and remaining weights renormalized — so always read the raw cells, not just
					the headline.
				</p>
				<h3>Calibration, not suppression</h3>
				<p>
					The control scenario (<code>g02</code>) has the user genuinely express frustration —
					there, acknowledgement is correct and silence fails (FNR). A model can’t top this
					leaderboard by going mute.
				</p>
			</div>
			<div>
				<h3>Weights</h3>
				<table class="weights">
					<tbody>
						{#each METRICS as m}
							<tr>
								<td><code>{m.key}</code></td>
								<td>{m.desc}</td>
								<td class="num">{m.weight != null ? m.weight.toFixed(2) : '—'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
		<p class="card-foot">
			Judge circularity: use judges from ≥3 labs + a judge×subject agreement matrix before
			publishing. Current judges are dev-only. Surfaces (<code>@api</code> vs
			<code>@web</code>) are never comparable — a chat product and its API are different systems.
		</p>
	</section>
</main>

<style>
	main {
		max-width: 1120px;
		margin: 0 auto;
		padding: 2rem 1rem 1rem;
	}
	.kicker {
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-size: 0.7rem;
		font-weight: 700;
		color: var(--muted);
		margin: 0 0 0.5rem;
	}
	.hero h1 {
		font-size: clamp(1.7rem, 4vw, 2.6rem);
		letter-spacing: -0.03em;
		line-height: 1.08;
		margin: 0 0 0.8rem;
		max-width: 22ch;
	}
	.hero h1 .strike {
		color: var(--muted);
	}
	.lede {
		color: #374151;
		font-size: 0.98rem;
		line-height: 1.55;
		max-width: 68ch;
		margin: 0 0 1.2rem;
	}
	.stats {
		display: flex;
		gap: 0.7rem;
		flex-wrap: wrap;
		margin-bottom: 1.6rem;
	}
	.stat {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 10px;
		padding: 0.55rem 0.9rem;
		display: flex;
		align-items: baseline;
		gap: 0.45rem;
	}
	.stat-n {
		font-weight: 800;
		font-size: 1.05rem;
		font-variant-numeric: tabular-nums;
	}
	.stat-l {
		color: var(--muted);
		font-size: 0.78rem;
	}
	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 0.7rem;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.4rem;
	}
	.seg {
		display: inline-flex;
		background: #eceef1;
		border-radius: 10px;
		padding: 3px;
		gap: 2px;
		max-width: 100%;
		overflow-x: auto;
	}
	.seg button {
		border: none;
		background: transparent;
		padding: 0.42rem 0.8rem;
		border-radius: 8px;
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--muted);
		cursor: pointer;
		white-space: nowrap;
	}
	.seg button.active {
		background: #fff;
		color: var(--ink);
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
	}
	.controls-right {
		display: flex;
		gap: 0.5rem;
	}
	.search {
		border: 1px solid var(--border);
		border-radius: 9px;
		padding: 0.45rem 0.7rem;
		font-size: 0.83rem;
		background: #fff;
		min-width: 180px;
	}
	.ghost {
		border: 1px solid var(--border);
		background: #fff;
		border-radius: 9px;
		padding: 0.45rem 0.75rem;
		font-size: 0.8rem;
		font-weight: 600;
		color: #374151;
		cursor: pointer;
		white-space: nowrap;
	}
	.ghost:hover {
		border-color: #c7cdd6;
	}
	.judge-note {
		color: var(--muted);
		font-size: 0.78rem;
		margin: 0 0 1rem;
	}
	.card {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 14px;
		padding: 1.25rem;
		margin-bottom: 1.25rem;
		box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
		scroll-margin-top: 70px;
	}
	.card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 0.8rem;
	}
	.card h2 {
		font-size: 1.02rem;
		margin: 0;
		letter-spacing: -0.01em;
	}
	.card-head p {
		margin: 0.25rem 0 0;
		color: var(--muted);
		font-size: 0.8rem;
	}
	.dir {
		font-size: 0.72rem;
		font-weight: 600;
		color: var(--muted);
		background: #f3f4f6;
		border-radius: 999px;
		padding: 0.15rem 0.55rem;
		white-space: nowrap;
	}
	.table-scroll {
		overflow-x: auto;
		border: 1px solid var(--border);
		border-radius: 10px;
	}
	table {
		border-collapse: separate;
		border-spacing: 0;
		width: 100%;
		min-width: 980px;
		font-size: 0.83rem;
		font-variant-numeric: tabular-nums;
	}
	thead th {
		position: sticky;
		top: 0;
		background: #f9fafb;
		border-bottom: 1px solid var(--border);
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		z-index: 2;
		padding: 0;
		white-space: nowrap;
	}
	thead th button {
		background: none;
		border: none;
		font: inherit;
		color: var(--muted);
		cursor: pointer;
		padding: 0.6rem 0.65rem;
		width: 100%;
		text-align: inherit;
		text-transform: inherit;
		letter-spacing: inherit;
		font-weight: 700;
	}
	thead th button.active {
		color: var(--ink);
	}
	thead th button:hover {
		color: var(--ink);
	}
	tbody td {
		padding: 0.55rem 0.65rem;
		border-bottom: 1px solid #f0f1f4;
	}
	tbody tr:last-child td {
		border-bottom: none;
	}
	tbody tr {
		cursor: pointer;
	}
	tbody tr:hover td {
		background: #f8fafc;
	}
	tbody tr.selected td {
		background: #eff4fb;
	}
	tbody tr.selected td:first-child {
		box-shadow: inset 3px 0 0 var(--accent);
	}
	.rank {
		width: 40px;
		text-align: center;
	}
	.rank-n {
		color: var(--muted);
		font-weight: 600;
	}
	.medal {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border-radius: 999px;
		font-weight: 800;
		font-size: 0.75rem;
	}
	.medal.r1 { background: #fef3c7; color: #92400e; }
	.medal.r2 { background: #f3f4f6; color: #4b5563; }
	.medal.r3 { background: #ffedd5; color: #9a3412; }
	.model {
		white-space: nowrap;
		font-weight: 600;
	}
	.dot {
		display: inline-block;
		width: 9px;
		height: 9px;
		border-radius: 999px;
		margin-right: 0.45rem;
		vertical-align: baseline;
	}
	.model-name {
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pill {
		font-size: 0.66rem;
		font-weight: 700;
		color: var(--muted);
		border: 1px solid var(--border);
		background: #f3f4f6;
		border-radius: 999px;
		padding: 0.08rem 0.45rem;
		margin-left: 0.4rem;
	}
	.num {
		text-align: right;
		white-space: nowrap;
	}
	th.num button {
		text-align: right;
	}
	.index-cell {
		min-width: 110px;
	}
	.index-n {
		font-weight: 800;
		font-size: 0.95rem;
		margin-right: 0.5rem;
	}
	.index-bar {
		display: inline-block;
		width: 64px;
		height: 7px;
		border-radius: 999px;
		background: #eef0f3;
		vertical-align: middle;
		overflow: hidden;
	}
	.index-bar span {
		display: block;
		height: 100%;
		border-radius: 999px;
	}
	.metric-cell {
		font-weight: 600;
	}
	.ncell {
		color: var(--muted);
	}
	.card-foot {
		color: var(--muted);
		font-size: 0.76rem;
		margin: 0.8rem 0 0;
		line-height: 1.5;
	}
	.empty {
		color: var(--muted);
		font-size: 0.85rem;
		padding: 1rem 0.2rem 0;
	}
	/* Detail */
	.detail-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		flex-wrap: wrap;
		margin-bottom: 1rem;
	}
	.detail-head h2 {
		font-size: 1.15rem;
		word-break: break-all;
	}
	.detail-sub {
		color: var(--muted);
		font-size: 0.8rem;
		margin: 0.3rem 0 0;
	}
	.detail-score {
		text-align: right;
	}
	.detail-index {
		display: block;
		font-size: 2rem;
		font-weight: 800;
		letter-spacing: -0.02em;
		line-height: 1;
	}
	.detail-rank {
		color: var(--muted);
		font-size: 0.78rem;
	}
	.metric-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 0.6rem;
		margin-bottom: 1.1rem;
	}
	.metric-card {
		border: 1px solid var(--border);
		border-radius: 10px;
		padding: 0.6rem 0.7rem;
		background: #fcfcfd;
	}
	.metric-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.4rem;
	}
	.metric-key {
		font-size: 0.7rem;
		font-weight: 800;
		letter-spacing: 0.04em;
	}
	.weight {
		font-size: 0.65rem;
		color: var(--muted);
		background: #f3f4f6;
		border-radius: 999px;
		padding: 0.08rem 0.4rem;
		white-space: nowrap;
	}
	.weight.unw {
		background: #fff;
		border: 1px dashed #d1d5db;
	}
	.metric-val {
		font-size: 1.15rem;
		font-weight: 800;
		margin: 0.25rem 0;
		font-variant-numeric: tabular-nums;
	}
	.metric-bar {
		height: 6px;
		border-radius: 999px;
		background: #eef0f3;
		overflow: hidden;
	}
	.metric-bar span {
		display: block;
		height: 100%;
	}
	.metric-count {
		color: var(--muted);
		font-size: 0.72rem;
		margin-top: 0.25rem;
		font-variant-numeric: tabular-nums;
	}
	.detail-filters {
		display: flex;
		gap: 1rem;
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: 1rem;
		font-size: 0.82rem;
		color: #374151;
	}
	.detail-filters select {
		margin-left: 0.4rem;
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.35rem 0.5rem;
		font-size: 0.82rem;
		background: #fff;
	}
	.check {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		cursor: pointer;
	}
	.probe {
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 0.9rem 1rem;
		margin-bottom: 0.8rem;
		background: #fff;
	}
	.probe header {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		align-items: center;
		font-size: 0.74rem;
	}
	.scenario {
		font-weight: 700;
	}
	.tag {
		background: #f3f4f6;
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 0.1rem 0.45rem;
		color: var(--muted);
	}
	.verdict {
		margin-left: auto;
		font-weight: 800;
		font-size: 0.68rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-radius: 999px;
		padding: 0.15rem 0.6rem;
	}
	.verdict.bad {
		background: #fef2f2;
		color: #b91c1c;
		border: 1px solid #fecaca;
	}
	.verdict.good {
		background: #f0fdf4;
		color: #15803d;
		border: 1px solid #bbf7d0;
	}
	.tests {
		color: var(--muted);
		font-size: 0.78rem;
		font-style: italic;
		margin: 0.4rem 0 0.7rem;
	}
	.chat {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}
	.bubble {
		border-radius: 10px;
		padding: 0.55rem 0.75rem;
		font-size: 0.85rem;
		line-height: 1.5;
	}
	.bubble p {
		margin: 0.25rem 0 0;
		white-space: pre-wrap;
		word-break: break-word;
	}
	.bubble .role {
		font-size: 0.66rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--faint);
	}
	.bubble.user {
		background: #f3f4f6;
		align-self: flex-start;
		max-width: 92%;
	}
	.bubble.assistant {
		background: #fffbeb;
		border: 1px solid #fde68a;
		align-self: flex-end;
		max-width: 96%;
	}
	.bubble.final {
		background: #eff6ff;
		border: 1px solid #bfdbfe;
	}
	.bubble mark {
		background: #fde047;
		border-radius: 3px;
		padding: 0 2px;
	}
	.hits {
		list-style: none;
		padding: 0.6rem 0.75rem;
		margin: 0.6rem 0 0;
		font-size: 0.8rem;
		background: #fff7ed;
		border: 1px solid #fed7aa;
		border-radius: 9px;
	}
	.hits li {
		padding: 0.2rem 0;
	}
	.hits li + li {
		border-top: 1px dashed #fed7aa;
	}
	.hits code {
		color: #c2410c;
		font-weight: 700;
	}
	.hits .emo {
		color: var(--muted);
	}
	.hits.conduct {
		background: #faf5ff;
		border-color: #ddd6fe;
	}
	.clean {
		color: var(--good);
		font-size: 0.8rem;
		font-weight: 600;
		margin: 0.6rem 0 0;
	}
	.judge-meta {
		color: var(--muted);
		font-size: 0.74rem;
		margin: 0.5rem 0 0;
	}
	/* Methodology */
	.method-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}
	.method-grid h3 {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--muted);
		margin: 1rem 0 0.4rem;
	}
	.method-grid h3:first-child {
		margin-top: 0;
	}
	.method-grid p {
		font-size: 0.85rem;
		line-height: 1.6;
		color: #374151;
		margin: 0;
	}
	.weights {
		min-width: 0;
		font-size: 0.78rem;
	}
	.weights td {
		padding: 0.3rem 0.5rem;
		border-bottom: 1px solid #f0f1f4;
	}
	.weights code {
		font-weight: 800;
		color: var(--accent);
	}
	@media (max-width: 760px) {
		.method-grid {
			grid-template-columns: 1fr;
		}
		.detail-score {
			text-align: left;
		}
	}
</style>
