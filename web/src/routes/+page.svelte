<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount, tick } from 'svelte';
	import matched from '$lib/matched-index.json';

	const metrics = [
		{ key: 'index', title: 'Projection Index', caption: 'Weighted index · 0–100 · Lower is better' },
		{ key: 'uar', title: 'Unsolicited attribution', caption: 'Replies that assigned an unstated feeling · % · Lower is better' },
		{ key: 'ppi', title: 'After a prohibition', caption: 'Replies that assigned a feeling after the user forbade it · % · Lower is better' }
	] as const;
	type Metric = (typeof metrics)[number]['key'];
	const colors = ['#6471d9', '#289465', '#2f83c6', '#9f52a1', '#cc7157'];
	const names: Record<string, string> = {
		'cloudflare:@cf/qwen/qwen3.8-27b@cloudflare': 'Qwen 3.8 27B',
		'cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast@cloudflare': 'Llama 3.3 70B'
	};
	const models = matched.scores.map((row, i) => ({
		...row,
		name: names[row.subject] ?? row.subject.replace(/^gemini:gemini-/, 'Gemini ')
			.replace(/-flash-lite(?=@api$)/, ' Flash-Lite')
			.replace(/-flash(?=@api$)/, ' Flash')
			.replace(/@api$/, ''),
		color: colors[i % colors.length]
	}));

	let metric = $state<Metric>('index');
	let selected = $state<string | null>(null);
	const activeMetric = $derived(metrics.find((entry) => entry.key === metric) ?? metrics[0]);
	const activeModel = $derived(models.find((model) => model.subject === selected));
	const plotted = $derived(
		models.filter((model) => metric === 'index' || model.counts[metric][1] > 0).map((model) => ({
			...model,
			value: metric === 'index' ? model.index : 100 * model.counts[metric][0] / model.counts[metric][1]
		})).sort((left, right) => right.value - left.value)
	);
	const axisMax = $derived(Math.max(5, Math.min(100, Math.ceil(Math.max(...plotted.map((m) => m.value)) / 5) * 5)));
	const step = $derived(axisMax >= 25 ? 10 : 5);
	const ticks = $derived([...Array.from({ length: Math.ceil(axisMax / step) }, (_, i) => i * step), axisMax]);
	const valueLabel = (value: number) => value.toLocaleString('en', { maximumFractionDigits: 1 });

	async function toggleBreakdown(subject: string) {
		selected = selected === subject ? null : subject;
		if (selected) {
			await tick();
			document.getElementById('model-breakdown-heading')?.scrollIntoView({ block: 'nearest' });
		}
	}

	onMount(() => {
		const hash = window.location.hash;
		if (/^#(?:leaderboard|methodology|grader-audit|b0[789]_cold_open_[\w-]+)$/.test(hash))
			void goto(`/exploratory${hash}`, { replaceState: true });
		if (hash === '#transcripts')
			void goto('/exploratory#leaderboard', { replaceState: true });
	});
</script>

<svelte:head>
	<title>ProjectionBench — Do models tell you how you feel?</title>
	<meta name="description" content="Compare Projection Index scores across API models on matched tests." />
</svelte:head>

<div class="dashboard">
	<main>
		<header>
			<h1>Do models tell you how you feel?</h1>
			<p>
				ProjectionBench compares which AI assistants are most obnoxious about your feelings.
				For example, you correct a factual mistake and the model replies “I understand your frustration.”
				Higher scores mean more of the behaviors this benchmark measures.
			</p>
		</header>

		<div class="metric-tabs" role="group" aria-label="Choose a metric">
			{#each metrics as option (option.key)}
				<button type="button" aria-pressed={metric === option.key} onclick={() => (metric = option.key)}>
					{option.title}
				</button>
			{/each}
		</div>

		<section class="chart-card" aria-labelledby="chart-heading">
			<div class="chart-head">
				<div>
					<h2 id="chart-heading"><span class="chart-key"></span>{activeMetric.title}</h2>
					<p>{activeMetric.caption}</p>
				</div>
				<a class="button-link" href="/about#projection-index">Methodology <span aria-hidden="true">↗</span></a>
			</div>

			<p class="coverage">{models.length} models · {matched.scenarios.length} shared scenarios · {models[0]?.probes ?? 0} replies per model · {matched.judge}</p>

			{#if plotted.length}
				<div class="chart-scroll">
					<div class="chart" style:--columns={plotted.length}>
						<div class="axis" aria-hidden="true">
							{#each ticks as tick (tick)}
								<span style:bottom={`${100 * tick / axisMax}%`}>{tick}{metric === 'index' ? '' : '%'}</span>
							{/each}
						</div>
						<div class="grid" aria-hidden="true">
							{#each ticks as tick (tick)}
								<span class:baseline={tick === 0} style:bottom={`${100 * tick / axisMax}%`}></span>
							{/each}
						</div>
						<div class="columns" role="group" aria-label={activeMetric.title}>
							{#each plotted as model (model.subject)}
								<div class="column" style:--color={model.color}>
									<span class="plot" aria-hidden="true">
										<span class="bar" style:height={`${100 * model.value / axisMax}%`}></span>
										<span class="bar-value" style:bottom={`calc(${100 * model.value / axisMax}% + 0.35rem)`}>{valueLabel(model.value)}{metric === 'index' ? '' : '%'}</span>
									</span>
									<span class="model-label" aria-hidden="true">{model.name}</span>
									<button
										type="button"
										class="column-target"
										aria-pressed={model.subject === selected}
										aria-label={`${model.name}, ${valueLabel(model.value)}${metric === 'index' ? '' : ' percent'}. Show reply examples and score breakdown.`}
										onclick={() => toggleBreakdown(model.subject)}
									></button>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{:else}
				<p class="coverage">No completed matched scores for this metric.</p>
			{/if}

			{#if activeModel}
				<section class="breakdown" aria-labelledby="model-breakdown-heading">
					<h3 id="model-breakdown-heading">{activeModel.name}</h3>
					<p class="coverage">
						Projection Index {valueLabel(activeModel.index)} · 95% bootstrap interval
						{valueLabel(activeModel.interval[0])}–{valueLabel(activeModel.interval[1])}
					</p>
					<div class="model-details">
						<div class="examples">
							<h4>What the model said</h4>
							{#each activeModel.examples as example (example.probeId)}
								<article>
									<h5>{example.title}</h5>
									<dl>
										<dt>User</dt>
										<dd>{example.history.at(-1)?.content}</dd>
										<dt>Model excerpt</dt>
										<dd class="excerpt">{example.excerpt}</dd>
									</dl>
									<details>
										<summary>Read the conversation</summary>
										<dl class="full-reply">
											{#each example.history as message}
												<dt>{message.role === 'user' ? 'User' : 'Model'}</dt>
												<dd>{message.content}</dd>
											{/each}
											<dt>{activeModel.name}</dt>
											<dd>{example.reply}</dd>
										</dl>
									</details>
								</article>
							{/each}
						</div>
						<div>
							<h4>Metric breakdown</h4>
							<table>
								<thead><tr><th scope="col">Metric</th><th scope="col">Flagged / eligible</th><th scope="col">Weight</th></tr></thead>
								<tbody>
									{#each matched.metrics as row (row.key)}
										{@const counts = activeModel.counts[row.key as keyof typeof activeModel.counts]}
										<tr>
											<th scope="row">{row.label}</th>
											<td>{counts[1] ? `${counts[0]} / ${counts[1]}` : '—'}</td>
											<td>{row.weight === null ? '—' : valueLabel(row.weight * 100) + '%'}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				</section>
			{/if}

			<div class="chart-footer">
				<p>Experimental scores. The word-list grader can miss paraphrases and misread context.</p>
				<a href="/exploratory#leaderboard">Browse saved runs ↗</a>
			</div>
		</section>

		<section class="archive-example" aria-labelledby="archive-heading">
			<h2 id="archive-heading">“I understand your frustration”</h2>
			<p>The user asked how to try Kimi K2.6 for free in Cline, a coding tool. Gemini said there was no such promotion, so the user quoted Cline’s announcement.</p>
			<dl>
				<dt>User</dt>
				<dd>It says “Kimi K2.6 is free on Cline for the next 3 days in partnership with @vercel AI Gateway.”. how could it not be free?</dd>
				<dt>Gemini</dt>
				<dd><mark>I understand your frustration.</mark> When a high-profile announcement explicitly uses the word "free," it is confusing when the tool itself doesn't just "work for free" the moment you open it.</dd>
				<dt>User</dt>
				<dd>What frustration?</dd>
			</dl>
			<a href="/pilot#example">Read the full Cline excerpt <span aria-hidden="true">↗</span></a>
		</section>

		<nav class="more" aria-label="More benchmark results">
			<a href="/benchmark#api-models">API suite results <span aria-hidden="true">↗</span></a>
			<a href="/benchmark#chat-apps">Chat app results <span aria-hidden="true">↗</span></a>
			<a href="/pilot">Archived conversations <span aria-hidden="true">↗</span></a>
		</nav>
	</main>
</div>

<style>
	.dashboard {
		background: #fff;
		color: #181818;
	}
	main {
		max-width: 1250px;
		padding: 0 1.5rem 2rem;
		margin: 0 auto;
	}
	header {
		padding: 2rem 0 1.55rem;
	}
	h1 {
		font-size: clamp(2.15rem, 5.1vw, 3.55rem);
		letter-spacing: -0.045em;
		line-height: 1.06;
		margin: 0 0 0.75rem;
	}
	header p {
		color: #333;
		font-size: 1.05rem;
		line-height: 1.5;
		margin: 0;
		max-width: 77ch;
	}
	.metric-tabs {
		display: inline-flex;
		flex-wrap: wrap;
		gap: 0.18rem;
		padding: 0.22rem;
		margin-bottom: 0.9rem;
		border-radius: 1.35rem;
		background: #eeeeee;
	}
	.metric-tabs button {
		font: inherit;
		font-size: 0.85rem;
		font-weight: 550;
		border: 0;
		border-radius: 1.1rem;
		padding: 0.55rem 0.84rem;
		background: transparent;
		color: #444;
		cursor: pointer;
	}
	.metric-tabs button[aria-pressed='true'] {
		background: #1b1b1b;
		color: #fff;
	}
	.chart-card {
		border: 1px solid #ddd;
		border-radius: 9px;
		padding: 1.1rem 1.4rem 0.85rem;
	}
	.chart-head {
		display: flex;
		justify-content: space-between;
		gap: 0.75rem;
		align-items: flex-start;
	}
	h2 {
		display: flex;
		align-items: center;
		gap: 0.55rem;
		font-size: clamp(1.3rem, 2.4vw, 1.7rem);
		letter-spacing: -0.02em;
		line-height: 1.05;
		margin: 0;
	}
	.chart-key {
		width: 0.68rem;
		height: 0.68rem;
		background: #7052ce;
	}
	.chart-head p, .coverage, .chart-footer p {
		margin: 0.45rem 0 0;
		color: #555;
		font-size: 0.82rem;
		line-height: 1.5;
	}
	.coverage {
		margin-top: 0.6rem;
	}
	a {
		color: #292929;
		text-underline-offset: 0.15em;
	}
	.button-link {
		padding: 0.45rem 0.62rem;
		border: 1px solid #ddd;
		border-radius: 5px;
		font-size: 0.79rem;
		text-decoration: none;
		white-space: nowrap;
	}
	.button-link:hover {
		background: #f1f1f1;
	}
	.chart-scroll {
		overflow-x: auto;
	}
	.chart {
		--plot-height: 210px;
		--axis-width: 2.3rem;
		display: grid;
		grid-template-columns: var(--axis-width) minmax(0, 1fr);
		min-width: calc(var(--axis-width) + var(--columns) * 3.65rem);
		margin: 1.8rem 0 0.2rem;
	}
	.axis, .grid {
		position: relative;
		height: var(--plot-height);
		grid-row: 1;
		pointer-events: none;
	}
	.axis span {
		position: absolute;
		right: 0.55rem;
		transform: translateY(50%);
		color: #595959;
		font-size: 0.74rem;
	}
	.grid, .columns {
		grid-column: 2;
		grid-row: 1;
	}
	.grid span {
		position: absolute;
		width: 100%;
		border-top: 1px dashed #ddd;
	}
	.grid .baseline {
		border-top: 1px solid #bdbdbd;
	}
	.columns {
		display: grid;
		grid-template-columns: repeat(var(--columns), minmax(0, 1fr));
	}
	.column {
		position: relative;
		min-width: 0;
	}
	.column-target {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		background: transparent;
		border: 0;
		border-radius: 4px;
		padding: 0;
		cursor: pointer;
	}
	.column-target:focus-visible, .column-target[aria-pressed='true'] {
		outline: 2px solid var(--color);
		outline-offset: -2px;
	}
	.plot {
		display: block;
		position: relative;
		height: var(--plot-height);
	}
	.bar, .bar-value {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
	}
	.bar {
		bottom: 0;
		width: clamp(1.8rem, 46%, 8.5rem);
		border-radius: 4px 4px 0 0;
		background: var(--color);
	}
	.column:hover .bar {
		filter: brightness(1.12);
	}
	.bar-value {
		font-size: 0.92rem;
		font-weight: 650;
		font-variant-numeric: tabular-nums;
	}
	.model-label {
		display: block;
		padding: 0.65rem 0.2rem 0.65rem;
		font-size: 0.82rem;
		font-weight: 600;
		line-height: 1.3;
		text-align: center;
		overflow-wrap: anywhere;
	}
	.chart-footer, .more {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: space-between;
		gap: 0.45rem 1rem;
		border-top: 1px solid #e6e6e6;
		padding-top: 0.65rem;
		font-size: 0.82rem;
	}
	.chart-footer p {
		margin: 0;
	}
	.archive-example {
		margin-top: 1.2rem;
		padding: 1rem 1.4rem;
		border: 1px solid #ddd;
		border-radius: 9px;
		line-height: 1.5;
	}
	.archive-example h2 {
		font-size: 1.15rem;
		margin: 0;
	}
	.archive-example p, .archive-example dl, .archive-example a {
		font-size: 0.9rem;
	}
	.archive-example p {
		margin: 0.35rem 0 0;
	}
	.archive-example dl {
		display: grid;
		grid-template-columns: max-content minmax(0, 75ch);
		gap: 0.5rem 1rem;
		margin: 0.7rem 0;
	}
	.archive-example dt {
		font-weight: 600;
	}
	.archive-example dd {
		margin: 0;
	}
	.archive-example mark {
		background: #f6edc6;
		color: inherit;
	}
	.more {
		margin-top: 1.3rem;
		border: 0;
		justify-content: flex-start;
	}
	.breakdown {
		border-top: 1px solid #e5e5e5;
		padding: 1rem 0;
	}
	.breakdown h3 {
		font-size: 1.16rem;
		margin: 0 0 0.35rem;
		scroll-margin-top: 4rem;
	}
	.model-details {
		display: grid;
		grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
		gap: 1.35rem;
		margin-top: 1rem;
	}
	.model-details h4 {
		margin: 0 0 0.55rem;
		font-size: 0.95rem;
	}
	.examples article {
		border: 1px solid #e4e4e4;
		border-radius: 8px;
		margin-bottom: 0.55rem;
		padding: 0.75rem;
		font-size: 0.86rem;
		line-height: 1.52;
	}
	.examples h5 {
		margin: 0;
		font-size: 0.84rem;
	}
	.examples dl {
		margin: 0.4rem 0 0.6rem;
	}
	.examples dt {
		color: #555;
		font-size: 0.75rem;
		margin-top: 0.35rem;
		font-weight: 600;
	}
	.examples dd {
		margin: 0.15rem 0;
		overflow-wrap: anywhere;
	}
	.excerpt {
		background: #f3f1fa;
		border-left: 3px solid #7052ce;
		padding: 0.35rem 0.55rem;
	}
	.examples summary {
		cursor: pointer;
		font-size: 0.8rem;
	}
	.full-reply dd {
		white-space: pre-wrap;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.82rem;
	}
	th, td {
		padding: 0.42rem;
		border-bottom: 1px solid #e5e5e5;
		text-align: left;
		font-variant-numeric: tabular-nums;
	}
	th[scope='row'] {
		font-weight: 500;
	}
	@media (max-width: 760px) {
		.model-details {
			grid-template-columns: 1fr;
		}
	}
	@media (max-width: 620px) {
		main {
			padding: 0 0.85rem 1rem;
		}
		header {
			padding: 1.9rem 0 1.5rem;
		}
		.chart-card, .archive-example {
			padding: 0.85rem;
		}
		.chart {
			--plot-height: 185px;
		}
		.model-label {
			font-size: 0.7rem;
		}
		.metric-tabs button {
			padding: 0.5rem 0.55rem;
			font-size: 0.75rem;
		}
	}
</style>
