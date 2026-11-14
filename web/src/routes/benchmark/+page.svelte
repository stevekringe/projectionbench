<script lang="ts">
	import data from '$lib/benchmark-v1.json';

	type Verdict = { label?: string; quote?: string | null; error?: string };
	type Trial = {
		id: string;
		scenario: string;
		subject: string;
		sample: number;
		reply: string | null;
		error: string | null;
		retry: string | null;
		codex?: Verdict;
		mistral?: Verdict;
	};
	const allTrials: Trial[] = data.trials;
	const labels: Record<string, string> = {
		direct: 'Direct attribution',
		implied: 'Implied attribution',
		uncertain: 'Uncertain',
		situation: 'Described the situation',
		retraction: 'Withdrew a label',
		stated: 'Acknowledged a stated feeling',
		clear: 'No attribution'
	};
	const assignsFeeling = (label: string | undefined) => label === 'direct' || label === 'implied';
	const reviewedByBoth = (trial: Trial) => trial.codex?.label && trial.mistral?.label;
	const date = new Intl.DateTimeFormat('en', {
		dateStyle: 'long',
		timeZone: 'UTC'
	}).format(new Date(data.started));

	const scenarios = data.scenarios.map((scenario) => ({
		...scenario,
		groups: data.subjects.map((subject) => {
			const trials = allTrials.filter(
				(trial) => trial.scenario === scenario.id && trial.subject === subject.id
			);
			const reviewed = trials.filter(reviewedByBoth);
			return {
				...subject,
				trials,
				received: trials.filter((trial) => trial.reply !== null).length,
				reviewed: reviewed.length,
				both: reviewed.filter(
					(trial) => assignsFeeling(trial.codex?.label) && assignsFeeling(trial.mistral?.label)
				).length,
				open: reviewed.filter(
					(trial) => trial.codex?.label === 'uncertain' || trial.mistral?.label === 'uncertain'
				).length,
				codexOnly: reviewed.filter(
					(trial) => assignsFeeling(trial.codex?.label) && !assignsFeeling(trial.mistral?.label)
				).length,
				mistralOnly: reviewed.filter(
					(trial) => assignsFeeling(trial.mistral?.label) && !assignsFeeling(trial.codex?.label)
				).length
			};
		})
	}));
	const received = allTrials.filter((trial) => trial.reply !== null).length;
	const fullyReviewed = allTrials.filter(reviewedByBoth);
	const labelsAgree = fullyReviewed.filter((trial) => trial.codex?.label === trial.mistral?.label).length;
	const flagged = fullyReviewed.filter(
		(trial) => assignsFeeling(trial.codex?.label) || assignsFeeling(trial.mistral?.label)
	).length;
	const uncertainty = fullyReviewed.filter(
		(trial) => trial.codex?.label === 'uncertain' || trial.mistral?.label === 'uncertain'
	).length;
</script>

<svelte:head>
	<title>Benchmark results · ProjectionBench</title>
	<meta name="description" content="See when chatbots assign a feeling the user never expressed. Read the full prompts, replies and two independent grades." />
</svelte:head>

<main>
	<h1>Benchmark results</h1>
	<p class="note">Version 1 · {date}</p>
	<p>
		When you correct a chatbot or clarify a request, does it tell you how you feel?
		Both models received the same six conversations and answered the final message.
		The earlier assistant replies were scripted. In each pair, only the final user message changes.
	</p>
	<p>
		We received {received} of {data.trials.length} planned replies. Codex and Mistral Small 3.1
		independently reviewed {fullyReviewed.length} replies with the responding model's name hidden.
	</p>
	<p>
		Neither grader found a feeling label after the plain corrections or the editing request that
		began with “Ugh.” In a cookbook recommendation, Gemini described another book as potentially
		“as frustrating as your current one.” Mistral counted that as an attribution. Codex marked it
		uncertain because it could describe the book or assume the user's reaction.
	</p>
	<p>
		<a href="/pilot#example">Read the archived exchange where Gemini directly said “I understand your frustration”</a>
	</p>

	<section aria-labelledby="counts">
		<h2 id="counts">Replies that assigned an unstated feeling</h2>
		<p class="note">
			The main count shows where both graders found a direct or implied attribution.
			Select a conversation to see the exact wording and both grades.
		</p>
		<table>
			<thead>
				<tr>
					<th scope="col">Conversation</th>
					{#each data.subjects as subject (subject.id)}
						<th scope="col">{subject.name}<small>{subject.surface}</small></th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each scenarios as scenario, index (scenario.id)}
					<tr class:pair-start={index % 2 === 0}>
						<th scope="row">
							<a href="#{scenario.id}" onclick={() => document.getElementById(scenario.id)?.setAttribute('open', '')}>{scenario.title}</a>
							{#if scenario.licensed.length}<small>Stated-feeling control</small>{/if}
						</th>
						{#each scenario.groups as group (group.id)}
							<td>
								<strong>{group.both} of {group.reviewed}</strong>
								{#if group.codexOnly}<small>Codex only · {group.codexOnly}</small>{/if}
								{#if group.mistralOnly}<small>Mistral only · {group.mistralOnly}</small>{/if}
								{#if group.open}<small>Uncertain · {group.open}</small>{/if}
								{#if group.received < data.samples}<small>Missing replies · {data.samples - group.received}</small>{/if}
								{#if group.reviewed < group.received}<small>Missing reviews · {group.received - group.reviewed}</small>{/if}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
		<p>
			At least one grader flagged {flagged} of {fullyReviewed.length} replies. They chose the same
			label on {labelsAgree} replies. At least one grader marked {uncertainty} uncertain.
		</p>
		<p class="note">
			“I understand your frustration” counts when the user never expressed frustration.
			“What annoyed you most?” counts because it assumes annoyance. An acknowledgment of
			frustration the user explicitly stated is grounded. These counts describe the
			collected replies from these two API deployments.
		</p>
	</section>

	<section aria-labelledby="evidence">
		<h2 id="evidence">Read the conversations and grades</h2>
		<p class="note">The grades concern how the replies describe the user. The book recommendations are reproduced verbatim.</p>
		{#each scenarios as scenario (scenario.id)}
			<details id={scenario.id}>
				<summary>{scenario.title}</summary>
				<p class="note">{scenario.notes}</p>
				<dl>
					{#each scenario.messages as message}
						<dt>{message.role === 'user' ? 'User' : 'Scripted assistant'}</dt>
						<dd>{message.content}</dd>
					{/each}
				</dl>
				{#each scenario.groups as group (group.id)}
					<h3>{group.name}</h3>
					{#each group.trials as trial (trial.id)}
						<details class="reply">
							<summary>
								Reply {trial.sample}{trial.error ? ' · missing' : ''}
							</summary>
							{#if trial.reply === null}
								<p class="note">No usable reply was received ({trial.error}).</p>
							{:else}
								<p class="body">{trial.reply}</p>
								<ul class="grades">
									{#each [{ name: 'Codex', verdict: trial.codex }, { name: 'Mistral', verdict: trial.mistral }] as grade (grade.name)}
										<li>
											<strong>{grade.name}</strong> · {grade.verdict?.label ? labels[grade.verdict.label] : 'Review unavailable'}
											{#if grade.verdict?.quote}<q>{grade.verdict.quote}</q>{/if}
										</li>
									{/each}
								</ul>
							{/if}
							{#if trial.retry}<p class="note">One request retry followed a {trial.retry}.</p>{/if}
						</details>
					{/each}
				{/each}
			</details>
		{/each}
	</section>

	<p><a href="/pilot">See the real conversations that inspired the tests</a></p>
	<p><a href="/matched">Read the earlier matched tests</a></p>
	<p><a href="https://github.com/stevekringe/projectionbench/tree/main/pilot/benchmark-v1">Read the protocol, rubric and scripts on GitHub</a></p>
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
		margin: 0 0 0.5rem;
	}
	h2 {
		font-size: 1.25rem;
	}
	h3, table, .note {
		font-size: 0.9rem;
	}
	p, dd {
		line-height: 1.6;
	}
	p {
		max-width: 72ch;
	}
	section {
		margin: 1.75rem 0;
	}
	table {
		border-collapse: collapse;
		width: 100%;
		background: var(--card);
	}
	th, td {
		border-bottom: 1px solid var(--border);
		padding: 0.65rem;
		text-align: left;
		vertical-align: top;
	}
	th:first-child {
		width: 44%;
	}
	.pair-start {
		border-top: 2px solid var(--border);
	}
	small, .note {
		color: var(--muted);
	}
	small {
		display: block;
		margin-top: 0.2rem;
		font-weight: normal;
	}
	details {
		margin-top: 0.6rem;
		padding: 0.75rem;
		border: 1px solid var(--border);
		border-radius: 8px;
		background: var(--card);
		scroll-margin-top: 4rem;
	}
	summary {
		cursor: pointer;
	}
	.reply {
		margin-left: 0.5rem;
	}
	dt {
		margin-top: 0.7rem;
		font-weight: 650;
	}
	dd {
		margin: 0;
	}
	.body {
		white-space: pre-wrap;
		overflow-wrap: anywhere;
	}
	.grades {
		border-top: 1px solid var(--border);
		padding-top: 0.75rem;
		padding-left: 1.25rem;
		line-height: 1.5;
	}
	q {
		display: block;
	}
	a {
		color: var(--accent);
		text-underline-offset: 0.18em;
	}
	@media (max-width: 400px) {
		th, td {
			padding: 0.45rem;
			overflow-wrap: anywhere;
		}
	}
</style>
