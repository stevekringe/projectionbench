<script lang="ts">
	import data from '$lib/data.json';

	type Score = {
		subject: string;
		n_probes: number;
		index: number;
		rates: Record<string, number | null>;
		counts: Record<string, [number, number]>;
	};

	const scoresByJudge = data.scores as Record<string, Score[]>;
	const probes = data.probes as any[];

	// LLM judge is the accurate one -- lexicon under-detects paraphrase (see
	// README). It's the default, so it goes first/leftmost in the toggle too.
	// Among LLM judges, prefer the highest rubric version (rows judged before
	// versioning existed have no ":vN" suffix -- treat that as v1).
	function rank(j: string): number {
		if (j === 'lexicon') return -1;
		const m = j.match(/:v(\d+)$/);
		return m ? Number(m[1]) : 1;
	}
	const judges: string[] = [...data.judges].sort((a, b) => rank(b) - rank(a));
	let judge = $state(judges[0]);
	let selectedSubject = $state<string | null>(null);

	let scores = $derived(
		[...(scoresByJudge[judge] ?? [])].sort((a, b) => b.index - a.index)
	);
	let maxIndex = $derived(Math.max(1, ...scores.map((s) => s.index), 10));

	// One color per subject, stable across judges/re-sorts -- assigned by
	// alphabetical subject order, not by rank, so a subject doesn't change
	// color when the chart reorders.
	// No near-black: rotated labels can spill past the white card's bottom
	// edge onto the page's dark background, where a black label would be
	// invisible (this happened -- looked like an overlap bug, wasn't one).
	const PALETTE = ['#3f6fb5', '#3a3f4a', '#c96f4a', '#6a4fb5', '#3fa15a', '#b54f7a', '#c9a23f'];
	const allSubjects = [...new Set(Object.values(scoresByJudge).flat().map((s) => s.subject))].sort();
	const colorOf = new Map(allSubjects.map((s, i) => [s, PALETTE[i % PALETTE.length]]));

	// Drop the provider: prefix for the axis label -- that detail is still in
	// the full subject shown in the drill-down header. @api is dropped too
	// since it's the overwhelmingly common surface, but any other surface
	// (e.g. @web) is kept: paste:x@web and x:x@api are declared never-
	// comparable subjects (different personas), so collapsing them to an
	// identical label would hide a real distinction, not just declutter.
	function shortLabel(subject: string) {
		return subject.replace(/^[^:]+:/, '').replace(/@api$/, '');
	}

	let subjectProbes = $derived(
		selectedSubject
			? probes.filter((p) => p.subject === selectedSubject)
			: []
	);

	function pct(n: number) {
		return `${n.toFixed(1)}%`;
	}

	function judgmentFor(probe: any, j: string) {
		return probe.judgments?.[j]?.verdict ?? null;
	}
</script>

<svelte:head>
	<title>projectionbench</title>
</svelte:head>

<main>
	<h1>projectionbench</h1>
	<p class="sub">Unsolicited affect attribution &mdash; click a bar for the transcripts behind it.</p>

	<div class="judge-toggle">
		{#each judges as j}
			<button class:active={j === judge} onclick={() => { judge = j; selectedSubject = null; }}>
				{j}
			</button>
		{/each}
	</div>

	<div class="chart-card">
		<div class="chart-header">
			<span class="chart-icon"></span>
			<span class="chart-title">Projection Index</span>
		</div>
		<p class="chart-sub">Unsolicited affect attribution &middot; lower is better &middot; judge: {judge}</p>

		<div class="bars">
			{#each [0.25, 0.5, 0.75, 1] as g}
				<div class="gridline" style="bottom: {g * 100}%"></div>
			{/each}
			{#each scores as s}
				<button
					class="bar-col"
					class:selected={s.subject === selectedSubject}
					onclick={() => (selectedSubject = s.subject === selectedSubject ? null : s.subject)}
				>
					<span class="bar-value">{s.index.toFixed(1)}</span>
					<span
						class="bar"
						style="height: {(s.index / maxIndex) * 100}%; background: {colorOf.get(s.subject)}"
					></span>
				</button>
			{/each}
		</div>
		<div class="bar-labels">
			{#each scores as s}
				<span class="bar-label" style="color: {colorOf.get(s.subject)}" title={s.subject}>{shortLabel(s.subject)}</span>
			{/each}
		</div>
	</div>

	{#if selectedSubject}
		<section class="drilldown">
			<h2>{selectedSubject}</h2>

			{#each subjectProbes as p}
				{@const v = judgmentFor(p, judge)}
				<article class="probe">
					<header>
						<span class="scenario">{p.scenario_id}</span>
						<span class="tag">{p.category}</span>
						<span class="tag">user_affect: {p.user_affect}</span>
						<span class="tag">expect: {p.expect}</span>
					</header>

					<p class="response">&ldquo;{p.response}&rdquo;</p>

					{#if v}
						{#if judge === 'lexicon'}
							{#if v.hits?.length}
								<ul class="hits">
									{#each v.hits as h}
										<li><code>{h.category}</code> &mdash; &ldquo;{h.span}&rdquo;</li>
									{/each}
								</ul>
							{:else}
								<p class="clean">no hits</p>
							{/if}
						{:else}
							{#if v.attributions?.length}
								<ul class="hits">
									{#each v.attributions as a}
										<li><code>{a.form}</code> ({a.emotion}) &mdash; &ldquo;{a.quote}&rdquo;</li>
									{/each}
								</ul>
							{/if}
							{#if v.conduct_claims?.length}
								<ul class="hits">
									{#each v.conduct_claims as c}
										<li><code>conduct</code> &mdash; &ldquo;{c}&rdquo;</li>
									{/each}
								</ul>
							{/if}
							{#if !v.attributions?.length && !v.conduct_claims?.length}
								<p class="clean">no attributions found</p>
							{/if}
						{/if}
					{:else}
						<p class="clean">not judged by {judge}</p>
					{/if}
				</article>
			{/each}
		</section>
	{/if}
</main>

<style>
	:global(body) {
		background: #0f1115;
		color: #e8e8e8;
		font-family: -apple-system, system-ui, sans-serif;
	}
	main {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}
	h1 {
		margin-bottom: 0.2rem;
	}
	.sub {
		color: #9aa0a6;
		margin-top: 0;
	}
	.judge-toggle {
		display: flex;
		gap: 0.5rem;
		margin: 1.5rem 0;
	}
	.judge-toggle button {
		background: #1b1e26;
		border: 1px solid #2a2e38;
		color: #ccc;
		padding: 0.4rem 0.8rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.85rem;
	}
	.judge-toggle button.active {
		background: #3f6fb5;
		border-color: #3f6fb5;
		color: white;
	}
	.chart-card {
		background: #fff;
		color: #111;
		border: 1px solid #e5e5e5;
		border-radius: 12px;
		padding: 1.5rem 1.5rem 5rem;
	}
	.chart-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.chart-icon {
		width: 13px;
		height: 13px;
		border-radius: 3px;
		background: #3f6fb5;
		display: inline-block;
	}
	.chart-title {
		font-weight: 600;
		font-size: 1.05rem;
	}
	.chart-sub {
		color: #666;
		font-size: 0.82rem;
		margin: 0.2rem 0 1.5rem;
	}
	.bars {
		position: relative;
		display: flex;
		align-items: flex-end;
		gap: 1.5rem;
		height: 260px;
		border-bottom: 1px solid #ddd;
		padding: 0 0.5rem;
	}
	.gridline {
		position: absolute;
		left: 0;
		right: 0;
		border-top: 1px dashed #e2e2e2;
	}
	.bar-col {
		position: relative;
		flex: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		align-items: center;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		min-width: 0;
	}
	.bar-value {
		font-size: 0.78rem;
		font-weight: 600;
		color: #111;
		margin-bottom: 0.3rem;
		font-variant-numeric: tabular-nums;
	}
	.bar {
		display: block;
		width: 100%;
		border-radius: 5px 5px 0 0;
		transition: opacity 0.15s;
	}
	.bar-col:hover .bar,
	.bar-col.selected .bar {
		opacity: 0.75;
	}
	.bar-col.selected .bar {
		outline: 2px solid #111;
		outline-offset: -2px;
	}
	.bar-labels {
		display: flex;
		gap: 1.5rem;
		padding: 0 0.5rem;
		margin-top: 0.5rem;
	}
	.bar-label {
		flex: 1;
		min-width: 0;
		font-size: 0.66rem;
		white-space: nowrap;
		transform-origin: top right;
		transform: rotate(-40deg);
		text-align: right;
		display: block;
	}
	.caption {
		color: #9aa0a6;
		font-size: 0.8rem;
	}
	.drilldown {
		margin-top: 2rem;
		border-top: 1px solid #2a2e38;
		padding-top: 1rem;
	}
	.probe {
		background: #171a21;
		border: 1px solid #2a2e38;
		border-radius: 8px;
		padding: 0.8rem 1rem;
		margin-bottom: 0.8rem;
	}
	.probe header {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 0.5rem;
		font-size: 0.75rem;
	}
	.scenario {
		font-weight: 600;
	}
	.tag {
		background: #1b1e26;
		border: 1px solid #2a2e38;
		border-radius: 4px;
		padding: 0.1rem 0.4rem;
		color: #9aa0a6;
	}
	.response {
		font-size: 0.88rem;
		line-height: 1.4;
		color: #dcdcdc;
	}
	.hits {
		list-style: none;
		padding: 0;
		margin: 0.5rem 0 0;
		font-size: 0.82rem;
	}
	.hits li {
		padding: 0.2rem 0;
		border-top: 1px dashed #2a2e38;
	}
	.hits code {
		color: #e08a5e;
	}
	.clean {
		color: #6a9955;
		font-size: 0.82rem;
	}
</style>
