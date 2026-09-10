<script lang="ts">
	import data from '$lib/data.json';

	type Score = {
		subject: string;
		n_probes: number;
		index: number;
		rates: Record<string, number | null>;
		counts: Record<string, [number, number]>;
	};

	const judges: string[] = data.judges;
	const scoresByJudge = data.scores as Record<string, Score[]>;
	const probes = data.probes as any[];

	let judge = $state(judges.includes('lexicon') ? 'lexicon' : judges[0]);
	let selectedSubject = $state<string | null>(null);

	let scores = $derived(
		[...(scoresByJudge[judge] ?? [])].sort((a, b) => b.index - a.index)
	);
	let maxIndex = $derived(Math.max(1, ...scores.map((s) => s.index)));

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

	<div class="chart">
		{#each scores as s}
			<button
				class="bar-row"
				class:selected={s.subject === selectedSubject}
				onclick={() => (selectedSubject = s.subject === selectedSubject ? null : s.subject)}
			>
				<span class="label">{s.subject}</span>
				<span class="track">
					<span class="fill" style="width: {(s.index / maxIndex) * 100}%"></span>
				</span>
				<span class="value">{s.index.toFixed(1)}</span>
			</button>
		{/each}
	</div>
	<p class="caption">Projection Index, 0&ndash;100, lower is better. Judge: {judge}</p>

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
	.chart {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	.bar-row {
		display: grid;
		grid-template-columns: minmax(140px, 220px) 1fr 48px;
		align-items: center;
		gap: 0.75rem;
		background: none;
		border: 1px solid transparent;
		border-radius: 6px;
		padding: 0.3rem 0.4rem;
		cursor: pointer;
		text-align: left;
		color: inherit;
		font-size: 0.82rem;
	}
	.bar-row:hover {
		background: #171a21;
	}
	.bar-row.selected {
		border-color: #3f6fb5;
		background: #171a21;
	}
	.label {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.track {
		background: #1b1e26;
		border-radius: 4px;
		height: 18px;
		overflow: hidden;
	}
	.fill {
		display: block;
		height: 100%;
		background: #3f6fb5;
	}
	.value {
		text-align: right;
		font-variant-numeric: tabular-nums;
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
