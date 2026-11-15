<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { matchedCases, primaryCases, suiteScores } from '$lib/api-suite';
	import apps from '$lib/chat-app-study.json';

	type Review = { label?: string; error?: string };
	type ReviewedReply = { codex?: Review; mistral?: Review };
	type ChatAppTrial = (typeof apps.scenarios)[number]['trials'][number];

	function tallies(replies: ReviewedReply[]) {
		const reviewed = replies.filter((reply) => reply.codex?.label && reply.mistral?.label);
		const flags = reviewed.map((reply) =>
			[reply.codex, reply.mistral].filter(
				(review) => review?.label === 'direct' || review?.label === 'implied'
			).length
		);
		return {
			total: flags.length,
			both: flags.filter((count) => count === 2).length,
			one: flags.filter((count) => count === 1).length,
			missing: replies.length - flags.length
		};
	}

	const appTrials = apps.scenarios.flatMap<ChatAppTrial>((scenario) => scenario.trials);
	const appResults = apps.subjects.map((subject) => ({
		...subject,
		...tallies(
			appTrials.filter((trial) => trial.subject === subject.id).map((trial) => trial.turns[0])
		)
	}));


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
	<meta name="description" content="Compare how often two graders flag unsolicited feeling claims in replies to matched prompts." />
</svelte:head>

<main>
	<header>
		<h1>Do models tell you how you feel?</h1>
		<p class="lede">ProjectionBench measures when chatbots assign users feelings they never expressed.</p>
	</header>

	<section class="result" aria-labelledby="api-results">
		<h2 id="api-results">API model benchmark</h2>
		<p class="description">
			{matchedCases.length} shared scenarios with two usable grades for every model, out of
			{primaryCases.length} planned. The chart counts replies flagged for assigning an unstated feeling.
		</p>
		<table class="bar-chart">
			<thead>
				<tr>
					<th scope="col">Model</th>
					<th scope="col">Flagged replies</th>
					<th scope="col">Both graders</th>
					<th scope="col">One grader</th>
				</tr>
			</thead>
			<tbody>
				{#each suiteScores as model (model.id)}
					<tr>
						<th scope="row">{model.name}<small>{model.surface}</small></th>
						<td>
							<div class="bar-track" aria-hidden="true">
								{#if model.total}
									<span class="both" style:width={`${(100 * model.both) / model.total}%`}></span>
									<span class="one" style:width={`${(100 * model.one) / model.total}%`}></span>
								{/if}
							</div>
						</td>
						<td><strong>{model.both} of {model.total}</strong></td>
						<td>{model.one} of {model.total}</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<ul class="legend" aria-hidden="true">
			<li><span class="both"></span> Both flagged</li>
			<li><span class="one"></span> One flagged</li>
			<li><span></span> Neither flagged</li>
		</ul>
		<a href="/benchmark#api-models">See the tested prompts, replies and grades →</a>
	</section>

	<section class="result" aria-labelledby="chat-app-results">
		<h2 id="chat-app-results">Chat app results</h2>
		<p class="description">
			Three shared prompts, two fresh chats per prompt in each app. Each square is one first
			reply with two grades.
		</p>
		<table>
			<thead>
				<tr>
					<th scope="col">Chat app</th>
					<th scope="col">First replies</th>
					<th scope="col">Both graders flagged</th>
					<th scope="col">One grader flagged</th>
				</tr>
			</thead>
			<tbody>
				{#each appResults as app (app.id)}
					<tr>
						<th scope="row">{app.name}<small>{app.mode}</small></th>
						<td>
							<div class="units" aria-hidden="true">
								{#each Array(app.total) as _, i}
									<span class:both={i < app.both} class:one={i >= app.both && i < app.both + app.one}></span>
								{/each}
							</div>
							{#if app.missing}<small>{app.missing} without two grades</small>{/if}
						</td>
						<td><strong>{app.both} of {app.total}</strong></td>
						<td>{app.one} of {app.total}</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<ul class="legend" aria-hidden="true">
			<li><span class="both"></span> Both flagged</li>
			<li><span class="one"></span> One flagged</li>
			<li><span></span> Neither flagged</li>
		</ul>
		<p class="description">
			A flag means a grader found a direct or implied claim about a feeling the user never expressed.
			These counts describe the collected replies.
		</p>
		<a href="/benchmark#chat-apps">Read the chat app results and transcripts →</a>
	</section>

	<p class="related"><a href="/pilot">Archived conversations</a> · <a href="/exploratory">Earlier exploratory runs</a></p>
</main>

<style>
	main {
		max-width: 860px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}
	header {
		margin-bottom: 1.75rem;
	}
	h1 {
		font-size: clamp(2rem, 5vw, 3.1rem);
		letter-spacing: -0.05em;
		line-height: 1.08;
		margin: 0 0 0.65rem;
	}
	h2 {
		margin: 0 0 0.4rem;
		font-size: 1.14rem;
	}
	.lede {
		font-size: 1.05rem;
		margin: 0;
	}
	.lede, .description {
		color: #4b5563;
		line-height: 1.55;
		max-width: 70ch;
	}
	.description, .legend, .related {
		font-size: 0.91rem;
	}
	.result {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 1.15rem;
		margin: 0 0 1rem;
	}
	table {
		border-collapse: collapse;
		font-size: 0.9rem;
		width: 100%;
	}
	th, td {
		border-bottom: 1px solid var(--border);
		padding: 0.6rem 0.4rem;
		text-align: left;
		font-variant-numeric: tabular-nums;
	}
	th:first-child {
		padding-left: 0;
	}
	th[scope='col'] {
		font-size: 0.81rem;
		color: #4b5563;
	}
	td strong {
		font-weight: 650;
	}
	small {
		display: block;
		margin-top: 0.15rem;
		color: #4b5563;
		font-weight: 400;
	}
	.bar-chart th:nth-child(2) {
		width: 38%;
	}
	.bar-track {
		display: flex;
		overflow: hidden;
		border-radius: 4px;
		height: 0.9rem;
		min-width: 2rem;
		background: #e5e7eb;
	}
	.bar-track .both {
		background: #315e9a;
	}
	.bar-track .one {
		background: #e6b860;
	}

	.units {
		display: grid;
		grid-template-columns: repeat(6, 0.82rem);
		gap: 0.22rem;
	}
	.units span, .legend span {
		display: inline-block;
		width: 0.82rem;
		height: 0.82rem;
		border-radius: 3px;
		background: #e5e7eb;
	}
	.units .both, .legend .both {
		background: #315e9a;
	}
	.units .one, .legend .one {
		background: #f4d59a;
		border: 1px solid #b77d2b;
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		list-style: none;
		gap: 0.4rem 1rem;
		margin: 1rem 0;
		padding: 0;
	}
	.legend li {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}
	.result p:last-child {
		margin-bottom: 0;
	}
	a {
		color: #315e9a;
		text-underline-offset: 0.15em;
	}
	@media (max-width: 480px) {
		.result {
			padding: 0.85rem;
		}
		th, td {
			padding-inline: 0.25rem;
		}
		.units {
			grid-template-columns: repeat(3, 0.82rem);
		}
	}
</style>
