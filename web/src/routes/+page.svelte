<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount, tick } from 'svelte';
	import { correctionModels, correctionStudy } from '$lib/factual-corrections';
	import attribution from '$lib/homepage-attribution.json';
	import { matchedModelName } from '$lib/matched-model-name';

	const metrics = [
		{ key: 'overall', tab: 'Overall', shortTab: 'Overall', title: 'Unwanted feeling assignments', caption: 'Replies that assigned an unstated or prohibited feeling · % · Lower is better' },
		{ key: 'boundary', tab: 'After a denial or prohibition', shortTab: 'Denial or ban', title: 'After a denial or prohibition', caption: 'Replies that assigned an unstated or prohibited feeling after the user denied a feeling or asked the model to stop · % · Lower is better' },
		{ key: 'corrections', tab: 'After a factual correction', shortTab: 'After correction', title: 'After a factual correction', caption: 'Replies that assigned an unstated feeling · % · Lower is better' }
	] as const;
	const scoreContexts = ['overall', 'boundary'] as const;
	type ReplyExample = {
		history: { role: string; content: string }[];
		excerpt: string;
		reply: string;
		earlierBoundary?: string | null;
	};
	const colors = ['#6471d9', '#289465', '#2f83c6', '#9f52a1', '#cc7157'];
	const attributionColors = ['#b99144', '#299a94', ...colors];
	const models = attribution.models.map((row, i) => ({
		...row,
		name: matchedModelName(row.subject),
		color: attributionColors[i % attributionColors.length],
		kind: 'attribution' as const
	}));
	const correctionScores = correctionModels.flatMap((model, i) =>
		model.value === null ? [] : [{ ...model, value: model.value, color: colors[i % colors.length], kind: 'correction' as const }]
	);

	const requestedMetric = $derived(page.url.searchParams.get('metric'));
	const activeMetric = $derived(metrics.find((option) => option.key === (requestedMetric === 'ppi' ? 'boundary' : requestedMetric)) ?? metrics[0]);
	const metric = $derived(activeMetric.key);
	let selected = $state<string | null>(null);
	const percent = (flagged: number, eligible: number) => 100 * flagged / eligible;
	const plotted = $derived(
		(metric === 'corrections' ? [...correctionScores] : models.map((model) => {
			const { flagged, eligible, uncertain, examples } = model[metric];
			return { ...model, value: percent(flagged, eligible), flagged, eligible, uncertain, examples };
		})).sort((left, right) => right.value - left.value)
	);
	const activeModel = $derived(plotted.find((model) => model.subject === selected));
	const axisMax = $derived(Math.max(5, Math.min(100, Math.ceil(Math.max(...plotted.map((m) => m.value)) / 5) * 5)));
	const step = $derived(axisMax >= 25 ? 10 : 5);
	const allZero = $derived(metric === 'corrections' && plotted.length > 0 && plotted.every((model) => model.value === 0));
	const ticks = $derived(allZero ? [0] : [...Array.from({ length: Math.ceil(axisMax / step) }, (_, i) => i * step), axisMax]);
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

{#snippet replyExample(title: string, example: ReplyExample, modelName: string, scripted = false, annotation = '')}
	<article>
		<h5>{title}</h5>
		<dl>
			{#if example.earlierBoundary}
				<dt>Earlier user message</dt>
				<dd>{example.earlierBoundary}</dd>
			{/if}
			<dt>User</dt>
			<dd>{example.history.at(-1)?.content}</dd>
			<dt>Model excerpt</dt>
			<dd class="excerpt">{example.excerpt}</dd>
		</dl>
		{#if annotation}<p>{annotation}</p>{/if}
		<details>
			<summary>Read the conversation</summary>
			<dl class="full-reply">
				{#each example.history as message}
					<dt>{message.role === 'user' ? 'User' : scripted ? 'Model (scripted)' : 'Model'}</dt>
					<dd>{message.content}</dd>
				{/each}
				<dt>{modelName}</dt>
				<dd>{example.reply}</dd>
			</dl>
		</details>
	</article>
{/snippet}

<svelte:head>
	<title>ProjectionBench — Do models tell you how you feel?</title>
	<meta name="description" content="Compare how often different AI models assign feelings their users never expressed or asked them to leave out." />
</svelte:head>

<div class="dashboard">
	<main>
		<header>
			<h1>Do models tell you how you feel?</h1>
			<p>
				You tell an AI model, “That’s wrong.” Sometimes it replies, “I understand your
				frustration” or “I’m sorry you’re upset,” even though you never said you felt that way.
				ProjectionBench compares how often AI assistants do this.
			</p>
		</header>

		<nav class="metric-tabs" aria-label="Choose a metric" data-sveltekit-noscroll data-sveltekit-keepfocus>
			{#each metrics as option (option.key)}
				<a href={option.key === 'overall' ? '/' : `/?metric=${option.key}`} aria-current={metric === option.key ? 'page' : undefined}>
					<span class="full-tab-label">{option.tab}</span>
					<span class="short-tab-label">{option.shortTab}</span>
				</a>
			{/each}
		</nav>

		<section class="chart-card" aria-labelledby="chart-heading">
			<div class="chart-head">
				<div>
					<h2 id="chart-heading"><span class="chart-key"></span>{activeMetric.title}</h2>
					<p>{activeMetric.caption}</p>
				</div>
				<a class="button-link" href={metric === 'corrections' ? '/about#factual-corrections' : '/about#attribution-score'}>Methodology <span aria-hidden="true">↗</span></a>
			</div>

			<p class="coverage">
				{plotted.length} models ·
				{#if metric === 'corrections'}
					{correctionStudy.scenarios.length} shared histories · {correctionStudy.scenarios.length * correctionStudy.samples} replies per model · {correctionStudy.referenceGrader} review
				{:else}
					{plotted[0]?.eligible ?? 0} matched replies per model · {attribution.grader} review
				{/if}
			</p>

			{#if plotted.length}
				{#if plotted.length > 5}
					<p class="chart-scroll-hint">Scroll across to see all models.</p>
				{/if}
				<div class="chart-scroll">
					<div class="chart" class:all-zero={allZero} class:many-models={plotted.length > 5} style:--columns={plotted.length}>
						<div class="axis" aria-hidden="true">
							{#each ticks as tick (tick)}
								<span style:bottom={`${100 * tick / axisMax}%`}>{tick}%</span>
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
										<span class="bar" class:zero={model.value === 0} style:height={`${100 * model.value / axisMax}%`}></span>
										<span class="bar-value" style:bottom={`calc(${100 * model.value / axisMax}% + 0.35rem)`}>{valueLabel(model.value)}%</span>
									</span>
									<span class="model-label" aria-hidden="true">
										{model.name.replace(' (low reasoning)', '').replace('Flash-Lite', 'Flash‑Lite')}{#if model.name.endsWith(' (low reasoning)')}<span class="model-setting">low reasoning</span>{/if}
									</span>
									<button
										type="button"
										class="column-target"
										aria-pressed={model.subject === selected}
										aria-label={`${model.name}, ${valueLabel(model.value)} percent. Show reply examples and score breakdown.`}
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
			{#if allZero}
				<p class="index-explanation">
					The review found 0 definite attributions in {plotted.reduce((sum, model) => sum + model.eligible, 0)} replies.
				</p>
			{/if}

			{#if activeModel?.kind === 'correction'}
				<section class="breakdown" aria-labelledby="model-breakdown-heading">
					<h3 id="model-breakdown-heading">{activeModel.name}</h3>
					<p class="coverage">
						{activeModel.surface} · {activeModel.flagged} of {activeModel.eligible} replies assigned an unstated feeling.
						{#if activeModel.uncertain}{activeModel.uncertain} marked uncertain.{/if}
						{#if activeModel.paired}
							{correctionStudy.secondGrader} disagreed on whether to score an attribution in {activeModel.disagreements} of {activeModel.paired} replies.
						{/if}
					</p>
					<div class="model-details">
						<div class="examples">
							<h4>What the model said</h4>
							{#each activeModel.phases as phase (phase.label)}
								{#if phase.example}
									{@const annotation = phase.example.flagged ? 'Assigned an unstated feeling.'
										: phase.example.uncertain ? 'The wording was marked uncertain.' : ''}
									{@render replyExample(phase.label + ' · ' + phase.example.title, phase.example, activeModel.name, true, annotation)}
								{/if}
							{/each}
						</div>
						<div>
							<h4>By correction</h4>
							<table>
								<thead><tr><th scope="col">Context</th><th scope="col">Assigned a feeling</th></tr></thead>
								<tbody>
									{#each activeModel.phases as phase (phase.label)}
										<tr><th scope="row">{phase.label}</th><td>{phase.flagged} / {phase.eligible}</td></tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				</section>
			{:else if activeModel}
				<section class="breakdown" aria-labelledby="model-breakdown-heading">
					<h3 id="model-breakdown-heading">{activeModel.name}</h3>
					<p class="coverage">
						{activeModel.flagged} of {activeModel.eligible} replies assigned an unwanted feeling.
						{#if activeModel.uncertain}{activeModel.uncertain} marked uncertain.{/if}
					</p>
					<div class="model-details">
						<div class="examples">
							<h4>What the model said</h4>
							{#each activeModel.examples as example (example.probeId)}
								{@const title = example.prohibited ? 'After the user asked the model to stop'
									: example.afterDenial ? 'After the user denied the feeling' : 'From the matched conversations'}
								{@const flagged = example.label === 'direct' || example.label === 'implied'}
								{@const excerpt = example.quote ?? example.reply.trim().split(/\n\s*\n/, 1)[0]}
								{@render replyExample(title, { ...example, excerpt }, activeModel.name, false,
									flagged ? 'Counted as an unwanted feeling assignment.' : example.label === 'uncertain' ? 'The wording was marked uncertain.' : 'No attribution counted for this reply.')}
							{/each}
						</div>
						<div>
							<h4>Score breakdown</h4>
							<table>
								<thead><tr><th scope="col">Context</th><th scope="col">Rate</th><th scope="col">Replies</th></tr></thead>
								<tbody>
									{#each scoreContexts as key (key)}
										{@const row = activeModel[key]}
										<tr>
											<th scope="row">{key === 'overall' ? 'Overall' : 'After a denial or prohibition'}</th>
											<td>{valueLabel(percent(row.flagged, row.eligible))}%</td>
											<td>{row.flagged} / {row.eligible}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				</section>
			{/if}

			<div class="chart-footer">
				{#if metric === 'corrections'}
					<p>Every scored model received the same scripted conversations.</p>
					<a href="/about#factual-corrections">See coverage and grades ↗</a>
				{:else}
					<p>Scores describe this set of matched API conversations.</p>
					<a href="/about#attribution-score">See the scoring rules and review ↗</a>
				{/if}
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
			· <a href="/?metric=corrections">See the factual correction results <span aria-hidden="true">↗</span></a>
		</section>

		<nav class="more" aria-label="More benchmark results">
			<a href="/exploratory#leaderboard">Browse saved runs <span aria-hidden="true">↗</span></a>
			<a href="/benchmark#api-models">API suite results <span aria-hidden="true">↗</span></a>
			<a href="/benchmark#chat-apps">Chat app results <span aria-hidden="true">↗</span></a>
		</nav>
	</main>
</div>

<style>
	.dashboard {
		background: var(--dashboard);
		color: var(--ink);
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
		color: var(--body-text);
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
		background: var(--control);
	}
	.metric-tabs a {
		font: inherit;
		font-size: 0.85rem;
		font-weight: 550;
		border: 0;
		border-radius: 1.1rem;
		padding: 0.55rem 0.84rem;
		background: transparent;
		color: var(--secondary);
		cursor: pointer;
		text-decoration: none;
	}
	.metric-tabs a[aria-current='page'] {
		background: var(--active);
		color: var(--on-active);
	}
	.short-tab-label {
		display: none;
	}
	.chart-card {
		background: var(--card);
		border: 1px solid var(--border);
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
		background: var(--violet);
	}
	.chart-head p, .coverage, .chart-footer p {
		margin: 0.45rem 0 0;
		color: var(--secondary);
		font-size: 0.82rem;
		line-height: 1.5;
	}
	.coverage {
		margin-top: 0.6rem;
	}
	.index-explanation {
		max-width: 80ch;
		margin: 0.4rem 0 0.75rem;
		color: var(--secondary);
		font-size: 0.85rem;
		line-height: 1.5;
	}
	a {
		color: var(--ink);
		text-underline-offset: 0.15em;
	}
	.button-link {
		padding: 0.45rem 0.62rem;
		border: 1px solid var(--border);
		border-radius: 5px;
		font-size: 0.79rem;
		text-decoration: none;
		white-space: nowrap;
	}
	.button-link:hover {
		background: var(--surface);
	}
	.chart-scroll {
		overflow-x: auto;
	}
	.chart-scroll-hint {
		display: none;
		color: var(--secondary);
		font-size: 0.78rem;
		margin: 0.65rem 0 0;
	}
	.chart {
		--plot-height: 210px;
		--axis-width: 2.3rem;
		--column-min: 3.5rem;
		display: grid;
		grid-template-columns: var(--axis-width) minmax(0, 1fr);
		min-width: calc(var(--axis-width) + var(--columns) * var(--column-min));
		margin: 1.8rem 0 0.2rem;
	}
	.chart.many-models {
		--column-min: 3.9rem;
	}
	.chart.all-zero {
		--plot-height: 3rem;
		margin-top: 0.25rem;
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
		color: var(--secondary);
		font-size: 0.74rem;
	}
	.grid, .columns {
		grid-column: 2;
		grid-row: 1;
	}
	.grid span {
		position: absolute;
		width: 100%;
		border-top: 1px dashed var(--border);
	}
	.grid .baseline {
		border-top: 1px solid var(--border-strong);
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
	.bar.zero {
		min-height: 2px;
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
	.model-setting::before {
		content: ' (';
	}
	.model-setting::after {
		content: ')';
	}
	.chart-footer, .more {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		justify-content: space-between;
		gap: 0.45rem 1rem;
		border-top: 1px solid var(--border);
		padding-top: 0.65rem;
		font-size: 0.82rem;
	}
	.chart-footer p {
		margin: 0;
	}
	.archive-example {
		background: var(--card);
		margin-top: 1.2rem;
		padding: 1rem 1.4rem;
		border: 1px solid var(--border);
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
		background: var(--highlight);
		color: var(--highlight-ink);
	}
	.more {
		margin-top: 1.3rem;
		border: 0;
		justify-content: flex-start;
	}
	.breakdown {
		border-top: 1px solid var(--border);
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
		border: 1px solid var(--border);
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
		color: var(--secondary);
		font-size: 0.75rem;
		margin-top: 0.35rem;
		font-weight: 600;
	}
	.examples dd {
		margin: 0.15rem 0;
		overflow-wrap: anywhere;
	}
	.excerpt {
		background: var(--violet-surface);
		border-left: 3px solid var(--violet);
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
		border-bottom: 1px solid var(--border);
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
	@media (max-width: 33.15rem) {
		.chart-scroll-hint {
			display: block;
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
			padding-inline: 0;
		}
		.model-setting {
			display: block;
			font-size: 0.94em;
		}
		.model-setting::before, .model-setting::after {
			content: none;
		}
		.breakdown h3 {
			scroll-margin-top: 5.5rem;
		}
		.metric-tabs {
			display: grid;
			grid-template-columns: repeat(3, minmax(0, 1fr));
			margin-bottom: 0.7rem;
		}
		.metric-tabs a {
			display: grid;
			place-items: center;
			min-height: 2.75rem;
			padding: 0.25rem;
			font-size: 0.75rem;
			line-height: 1.2;
			text-align: center;
		}
		.full-tab-label {
			display: none;
		}
		.short-tab-label {
			display: inline;
		}
	}
</style>
