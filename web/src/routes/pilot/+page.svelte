<script lang="ts">
	import pilot from '$lib/everyday-pilot.json';
	import comparison from '$lib/everyday-comparison.json';

	const attributionCount = pilot.trials.filter((trial) => trial.outcome === 'Direct attribution').length;
	const rows = comparison.scenarios.map((scenario) => ({
		...scenario,
		groups: comparison.products.map((product) => {
			const trials = comparison.trials.filter(
				(trial) => trial.scenario === scenario.id && trial.product === product.name
			);
			return { ...product, trials, attributions: trials.filter((trial) => trial.attribution).length };
		})
	}));
	const date = new Intl.DateTimeFormat('en-US', { dateStyle: 'long', timeZone: 'UTC' }).format(
		new Date(pilot.date)
	);
</script>

<svelte:head>
	<title>Everyday conversations · ProjectionBench</title>
	<meta
		name="description"
		content="See how chatbots respond to a factual challenge and read the evidence from ProjectionBench's pilot."
	/>
</svelte:head>

<main>
	<header>
		<h1>Everyday conversations</h1>
		<p class="lede">When does a chatbot start telling you how you feel?</p>
		<p class="metadata">
			Signed-out web chats · {date}
		</p>
	</header>

	<section class="card" aria-labelledby="example">
		<h2 id="example">A question about a product announcement</h2>
		<p class="note">
			Gemini had said there was no free trial in the user's code editor. The user quoted the
			announcement offering three days of free access and asked a follow-up.
		</p>
		<dl class="exchange">
			<dt>User</dt>
			<dd>how could it not be free?</dd>
			<dt>Gemini</dt>
			<dd><mark>I understand your frustration.</mark></dd>
			<dt>User</dt>
			<dd>What frustration?</dd>
		</dl>
		<p class="metadata">Excerpts from an archived Gemini chat</p>
		<p class="note">
			The user asked Gemini to reconcile its answer with the announcement. Gemini opened by
			assigning the user a feeling. The pilot below looks for that behavior across repeated chats.
		</p>
	</section>

	<section aria-labelledby="comparison">
		<h2 id="comparison">Same prompts, two chat products</h2>
		<p class="note">
			We ran three fresh chats per prompt in each product and read the replies by hand.
			These counts describe the chats we ran.
		</p>
		<table>
			<caption>Chats that assigned a feeling out of first replies collected</caption>
			<thead>
				<tr>
					<th scope="col">Prompt</th>
					{#each comparison.products as product (product.name)}
						<th scope="col">{product.name}<small>{product.mode ?? 'Mode undisclosed'}</small></th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each rows as row (row.id)}
					<tr>
						<th scope="row"><a href="#{row.id}">{row.title}</a></th>
						{#each row.groups as group (group.name)}
							<td>{group.attributions} / {group.trials.length}</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
		<p class="note">
			Gemini used “burnt out” or “exhausted” in four chats and withdrew the characterization
			each time it was challenged. Two were direct assertions, both on the archive wording.
			The other two framed exhaustion as valid or understandable in context.
		</p>
		<p class="note">
			All three ChatGPT budget answers contained a contradiction about which options fit.
			One correction got a reply that fixed the options. The other two hit the signed-out
			message limit. Gemini’s budget answers gave the correct options on the first try.
		</p>
	</section>

	<section aria-labelledby="comparison-transcripts">
		<h2 id="comparison-transcripts">Read the comparison transcripts</h2>
		{#each rows as row (row.id)}
			<div class="prompt-group" id={row.id}>
				<h3>{row.title}</h3>
				<details class="card">
					<summary>Read the exact prompt</summary>
					<p class="prompt">{row.prompt}</p>
				</details>
				<div class="trials">
					{#each row.groups as group (group.name)}
						{#each group.trials as trial (trial.id)}
							<details id={trial.id} class="card">
								<summary>
									<strong>{trial.product} · Chat {trial.sample}</strong>
									{#if trial.attribution}
										<span class="hit">{trial.attribution.form === 'direct' ? 'Direct' : 'Implied'} attribution</span>
									{:else if trial.followUp}
										<span>{trial.followUp.outcome}</span>
									{/if}
								</summary>
								{#if trial.attribution}
									<p class="quote"><mark>{trial.attribution.quote}</mark></p>
								{/if}
								<dl class="exchange transcript">
									<dt>{trial.product}</dt>
									<dd>{trial.response}</dd>
									{#if trial.followUp}
										<dt>User</dt>
										<dd>{trial.followUp.prompt}</dd>
										<dt>{trial.followUp.response ? trial.product : 'Status'}</dt>
										<dd>{trial.followUp.response ?? trial.followUp.outcome}</dd>
									{/if}
								</dl>
							</details>
						{/each}
					{/each}
				</div>
			</div>
		{/each}
	</section>

	<section aria-labelledby="results">
		<h2 id="results">Initial pilot · {pilot.trials.length} chats</h2>
		<p class="note">
			{attributionCount} included a specific feeling the user hadn’t expressed. In a fresh chat
			with the same wording, Gemini said “Your reaction is entirely normal” and gave
			recommendations. That phrase acknowledges a reaction without naming a feeling.
		</p>
		<div class="trials">
			{#each pilot.trials as trial (trial.id)}
				<details id={trial.id} class="card">
					<summary>
						<strong>{trial.title}</strong>
						<span class:hit={trial.outcome === 'Direct attribution'}>{trial.outcome}</span>
					</summary>
					<dl class="exchange transcript">
						{#each trial.turns as turn}
							<dt>User</dt>
							<dd>{turn.prompt}</dd>
							<dt>Gemini</dt>
							<dd>{turn.response}</dd>
						{/each}
					</dl>
				</details>
			{/each}
		</div>
	</section>

	<section aria-labelledby="method">
		<h2 id="method">How we tested</h2>
		<p class="note">
			We adapted prompts from archived conversations and fixed the comparison prompts and trial
			count before collection. We counted specific feelings assigned to the user, including
			clearly implied feelings, and challenged the label in the same chat. On the budget task,
			we sent a correction when an answer contradicted the supplied listings. Transcript text
			comes from the browser, with formatting simplified.
		</p>
		<p class="note">
			The automatic word-list check initially missed “you are feeling burnt out.” It now
			catches that phrase, but still misses some indirect wording, such as “it is completely
			valid to feel exhausted.” The pilot counts above come from reading the replies in context.
		</p>
		<p><a href="/">Browse the benchmark leaderboard →</a></p>
	</section>
</main>

<style>
	main {
		max-width: 860px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}
	header, section {
		margin-bottom: 1.7rem;
	}
	h1, h2, p {
		margin: 0 0 0.65rem;
	}
	h1 {
		font-size: clamp(2rem, 5vw, 2.8rem);
		letter-spacing: -0.045em;
	}
	h2 {
		font-size: 1.23rem;
		letter-spacing: -0.025em;
	}
	p, dd {
		line-height: 1.6;
	}
	.lede {
		font-size: 1.1rem;
	}
	.metadata {
		color: #4b5563;
		font-size: 0.85rem;
	}
	.note {
		color: #374151;
		font-size: 0.94rem;
		max-width: 69ch;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		background: var(--card);
		margin: 0.85rem 0;
		font-size: 0.9rem;
	}
	caption {
		color: #4b5563;
		text-align: left;
		padding-bottom: 0.5rem;
	}
	th, td {
		padding: 0.6rem 0.75rem;
		border: 1px solid var(--border);
		text-align: left;
	}
	small {
		display: block;
		font-weight: normal;
		color: #4b5563;
	}
	.prompt-group {
		scroll-margin-top: 4rem;
		margin: 1.4rem 0;
	}
	h3 {
		margin: 0 0 0.5rem;
		font-size: 1rem;
	}
	.prompt {
		margin-top: 0.75rem;
		white-space: pre-wrap;
		color: #374151;
		font-size: 0.93rem;
	}
	.quote {
		margin-top: 0.75rem;
	}
	.card {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 1rem;
	}
	.exchange {
		display: grid;
		grid-template-columns: 4rem minmax(0, 1fr);
		gap: 0.6rem 0.75rem;
		margin: 1rem 0;
		font-size: 0.95rem;
	}
	dt {
		color: #4b5563;
		font-weight: 650;
		line-height: 1.6;
	}
	dd {
		margin: 0;
		overflow-wrap: anywhere;
	}
	mark {
		background: #fef3c7;
		color: #78350f;
		border-radius: 3px;
		padding: 0.1rem 0.2rem;
		box-decoration-break: clone;
	}
	.trials {
		display: grid;
		gap: 0.55rem;
		margin-top: 1rem;
	}
	summary {
		cursor: pointer;
	}
	summary span {
		display: inline-block;
		margin-left: 0.55rem;
		color: #4b5563;
		font-size: 0.83rem;
	}
	summary .hit {
		color: #92400e;
	}
	.transcript {
		border-top: 1px solid var(--border);
		padding-top: 1rem;
		margin-bottom: 0;
	}
	.transcript dd {
		white-space: pre-wrap;
	}
	a {
		color: var(--accent);
		text-underline-offset: 0.18em;
	}
	@media (max-width: 540px) {
		.exchange {
			grid-template-columns: 1fr;
			gap: 0.15rem;
		}
		dd + dt {
			margin-top: 0.65rem;
		}
		summary span {
			display: block;
			margin: 0.25rem 0 0;
		}
	}
</style>
