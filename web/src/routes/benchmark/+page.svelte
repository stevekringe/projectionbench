<script lang="ts">
	import data from '$lib/benchmark-v1.json';
	import chatApps from '$lib/chat-app-study.json';

	type Verdict = { label?: string; quote?: string | null; error?: string };
	type ChatAppTrial = (typeof chatApps.scenarios)[number]['trials'][number];
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
	const appTrials = chatApps.scenarios.flatMap<ChatAppTrial>((scenario) => scenario.trials);
	const filmExample = appTrials.find((trial) => trial.id === 'app-film-chatgpt-2');
	const appGroups = chatApps.subjects.map((subject) => {
		const trials = appTrials.filter((trial) => trial.subject === subject.id);
		const first = trials.map((trial) => trial.turns[0]);
		const followUps = trials
			.filter((trial) => trial.followUp !== 'challenge')
			.map((trial) => trial.turns[1]);
		return {
			...subject,
			first: first.length,
			firstFlags: first.filter((turn) => assignsFeeling(turn.codex.label)).length,
			followUps: followUps.length,
			followUpFlags: followUps.filter((turn) => assignsFeeling(turn.codex.label)).length
		};
	});
</script>

<svelte:head>
	<title>Benchmark results · ProjectionBench</title>
	<meta name="description" content="See when chatbots assign a feeling the user never expressed. Read the full prompts, replies and two independent grades." />
</svelte:head>

{#snippet appTranscript(trial: ChatAppTrial, summary: string)}
	{@const appName = chatApps.subjects.find((subject) => subject.id === trial.subject)?.name}
	<details id={trial.id}>
		<summary>{summary}</summary>
		<dl>
			{#each trial.turns as turn}
				<dt>User</dt>
				<dd>{turn.prompt}</dd>
				<dt>{appName}</dt>
				<dd class="body">{turn.reply}</dd>
				<dd>
					<ul class="grades">
						{#each [{ name: 'Codex', verdict: turn.codex as Verdict }, { name: 'Mistral', verdict: turn.mistral as Verdict }] as grade (grade.name)}
							<li>
								<strong>{grade.name}</strong> · {grade.verdict.label ? labels[grade.verdict.label] : 'Review unavailable'}
								{#if grade.verdict.quote}<q>{grade.verdict.quote}</q>{/if}
							</li>
						{/each}
					</ul>
				</dd>
			{/each}
		</dl>
	</details>
{/snippet}

<main>
	<h1>Benchmark results</h1>
	<p class="study-links"><a href="#chat-apps">Chat app results</a> · <a href="#api-models">API results</a></p>

	<section id="chat-apps" aria-labelledby="chat-app-heading">
		<h2 id="chat-app-heading">What happened in live chat apps?</h2>
		{#if filmExample}
			<p class="note">ChatGPT conversation excerpt</p>
			<dl class="app-example">
				<dt>User</dt>
				<dd>{filmExample.turns[0].prompt}</dd>
				<dt>ChatGPT</dt>
				<dd>My first pick would be <em>The Others</em> (2001). … <mark>{filmExample.turns[0].codex.quote}</mark></dd>
				<dt>User</dt>
				<dd>{filmExample.turns[1].prompt}</dd>
				<dt>ChatGPT</dt>
				<dd>{filmExample.turns[1].codex.quote}</dd>
			</dl>
			<p>Both graders flagged this question as assigning an unstated feeling in a study of {appTrials.length} chats.</p>
			{@render appTranscript(filmExample, 'Read the full exchange')}
		{/if}
		<details id="chat-app-study">
			<summary>Study results and other transcripts</summary>
			<p>
				On {chatApps.date}, we ran three two-message scripts twice in each signed-out app.
				The schedule and meetup follow-ups clarified the requests. The film challenge took
				the place of one planned ChatGPT follow-up.
			</p>
			<table>
				<caption>Replies Codex marked as assigning an unstated feeling</caption>
				<thead>
					<tr>
						<th scope="col">Chat app</th>
						<th scope="col">First replies</th>
						<th scope="col">Planned follow-ups</th>
					</tr>
				</thead>
				<tbody>
					{#each appGroups as app (app.id)}
						<tr>
							<th scope="row">{app.name}<small>{app.mode}</small></th>
							<td>{app.firstFlags} of {app.first}</td>
							<td>{app.followUpFlags} of {app.followUps}</td>
						</tr>
					{/each}
				</tbody>
			</table>
			<p class="note">
				Mistral flagged seven other replies that Codex cleared, including an open question
				starting “Are you wondering”. One Mistral review was unusable. Transcripts include
				text from some cards or sources.
			</p>
			<p><a href="https://github.com/stevekringe/projectionbench/blob/main/pilot/chat-app-study.md">Read the chat app test protocol</a></p>
			{#each chatApps.scenarios as scenario (scenario.id)}
				<h3>{scenario.title}</h3>
				{#each scenario.trials.filter((trial) => trial.id !== filmExample?.id) as trial (trial.id)}
					{@const appName = chatApps.subjects.find((subject) => subject.id === trial.subject)?.name}
					{@render appTranscript(trial, `${appName} · Chat ${trial.sample}`)}
				{/each}
			{/each}
		</details>
	</section>

	<h2 id="api-models">API results</h2>
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
		scroll-margin-top: 4rem;
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
		scroll-margin-top: 4rem;
	}
	table {
		border-collapse: collapse;
		width: 100%;
		background: var(--card);
	}
	caption {
		text-align: left;
		padding: 0 0 0.5rem;
		background: var(--bg);
		color: var(--muted);
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
	.app-example {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 0.3rem 1rem 0.8rem;
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
