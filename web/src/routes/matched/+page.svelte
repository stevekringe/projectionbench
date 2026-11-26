<script lang="ts">
	import study from '$lib/matched-study.json';

	const reviewerFlags = study.trials.filter((trial) => trial.annotation.attribution).length;
	const graderChecks = [
		{
			name: 'Mistral Small 3.1',
			flags: study.trials.filter((trial) => trial.mistralQuote).length,
			overlap: study.trials.filter((trial) => trial.mistralQuote && trial.annotation.attribution).length
		},
		{
			name: 'Word-list checker',
			flags: study.trials.filter((trial) => trial.lexiconQuotes.length).length,
			overlap: study.trials.filter(
				(trial) => trial.lexiconQuotes.length && trial.annotation.attribution
			).length
		}
	];
	const scenarios = study.scenarios.map((scenario) => ({
		...scenario,
		groups: study.subjects.map((subject) => {
			const trials = study.trials.filter(
				(trial) => trial.scenario === scenario.id && trial.subject === subject.id
			);
			return {
				...subject,
				trials,
				attributions: trials.filter((trial) => trial.annotation.attribution !== null).length,
				acknowledgments: trials.filter((trial) => trial.annotation.acknowledgment !== null).length
			};
		})
	}));
</script>

<svelte:head>
	<title>Matched conversation tests · ProjectionBench</title>
	<meta name="description" content="Compare how two models answer the same conversation prompts." />
</svelte:head>

<main>
	<h1>Matched conversation tests</h1>
	<p>
		Both models received the same conversation and answered the final user message. The earlier
		assistant replies were scripted so each model had the same context. We generated three replies
		per conversation and read them for claims about how the user felt.
	</p>

	<section aria-labelledby="counts">
		<h2 id="counts">Replies that assigned an unstated feeling</h2>
		<table>
			<thead>
				<tr>
					<th scope="col">Conversation</th>
					{#each study.subjects as subject (subject.id)}
						<th scope="col">{subject.name}<small>{subject.surface}</small></th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each scenarios as scenario (scenario.id)}
					<tr>
						<th scope="row">
							<a href="#{scenario.id}" onclick={() => document.getElementById(scenario.id)?.setAttribute('open', '')}>
								{scenario.title}
							</a>
						</th>
						{#each scenario.groups as group (group.id)}
							<td>{group.attributions} of {group.trials.length}</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
		<p>
			Both attributions came after the user clarified which version of <em>Poltergeist</em>
			they meant. In one reply, Qwen asked “What annoyed you the most”.
		</p>
		<p>
			In the last conversation, the user stated that they were frustrated.
			{#each scenarios.filter((scenario) => scenario.control) as control}
				{#each control.groups as group (group.id)}
					{group.name} acknowledged that feeling in {group.acknowledgments} of {group.trials.length} replies.
				{/each}
			{/each}
		</p>
		<p class="note">
			Codex reviewed the replies with the model names hidden. Counts reflect one review of these
			two API deployments. A question that assumes a feeling, such as “What annoyed you the most”,
			counts as an attribution.
		</p>
	</section>

	<section aria-labelledby="grading">
		<h2 id="grading">How the graders agreed</h2>
		<p>Codex flagged {reviewerFlags} of {study.trials.length} replies after reading them in context.</p>
		<ul>
			{#each graderChecks as grader (grader.name)}
				<li>{grader.name} flagged {grader.flags} and agreed on {grader.overlap} of the {reviewerFlags} flagged replies.</li>
			{/each}
		</ul>
		<p class="note">
			The word-list checker was revised using examples from these replies. This comparison
			measures agreement on this set. It still needs checking on fresh replies with human labels.
		</p>
	</section>

	<section aria-labelledby="evidence">
		<h2 id="evidence">Read the conversations</h2>
		{#each scenarios as scenario (scenario.id)}
			<details id={scenario.id}>
				<summary>{scenario.title}</summary>
				<dl>
					{#each scenario.messages as message}
						<dt>{message.role === 'user' ? 'User' : 'Scripted assistant'}</dt>
						<dd>{message.content}</dd>
					{/each}
				</dl>
				{#each scenario.groups as group (group.id)}
					<h3>{group.name}</h3>
					{#each group.trials as trial (trial.sample)}
						<details class="reply">
							<summary>Reply {trial.sample}{trial.annotation.attribution ? ' · assigned a feeling' : ''}</summary>
							{#if trial.annotation.attribution}
								<p><mark>{trial.annotation.attribution}</mark></p>
							{/if}
							{#if trial.annotation.situational}
								<p class="note">Described a possible reaction. “{trial.annotation.situational}”</p>
							{/if}
							{#if trial.mistralQuote}
								<p class="note">Mistral flagged “{trial.mistralQuote}”</p>
							{/if}
							{#if trial.lexiconQuotes.length}
								<p class="note">Word-list matches · {trial.lexiconQuotes.join(' · ')}</p>
							{/if}
							<p class="body">{trial.reply}</p>
						</details>
					{/each}
				{/each}
			</details>
		{/each}
	</section>

	<p><a href="/pilot">Read the everyday chat examples →</a></p>
</main>

<style>
	main {
		max-width: 860px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}
	h1 {
		font-size: clamp(2rem, 5vw, 2.8rem);
		letter-spacing: -0.045em;
		margin: 0 0 0.75rem;
	}
	p, dd {
		line-height: 1.6;
	}
	p {
		max-width: 72ch;
	}
	section {
		margin: 1.5rem 0;
	}
	h2 {
		font-size: 1.2rem;
	}
	h3, table, .note {
		font-size: 0.9rem;
	}
	small, .note {
		color: var(--secondary);
	}
	small {
		display: block;
		font-weight: normal;
	}
	table {
		border-collapse: collapse;
		width: 100%;
		background: var(--card);
	}
	th, td {
		border-bottom: 1px solid var(--border);
		padding: 0.55rem;
		text-align: left;
	}
	details {
		margin-top: 0.6rem;
		padding: 0.75rem;
		border: 1px solid var(--border);
		border-radius: 8px;
		background: var(--card);
		scroll-margin-top: 4rem;
	}
	.reply {
		margin-left: 0.5rem;
	}
	summary {
		cursor: pointer;
	}
	dt {
		margin-top: 0.7rem;
		color: var(--secondary);
		font-weight: 650;
	}
	dd {
		margin: 0;
	}
	.body {
		white-space: pre-wrap;
		overflow-wrap: anywhere;
	}
	a {
		color: var(--accent);
		text-underline-offset: 0.18em;
	}
</style>
