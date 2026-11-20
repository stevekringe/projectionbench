<script lang="ts">
	import audit from '$lib/matched-attribution-audit.json';
	import controls from '$lib/stated-feeling-check.json';
	import attribution from '$lib/homepage-attribution.json';
	import { correctionModels, correctionStudy } from '$lib/factual-corrections';
	import { matchedModelName } from '$lib/matched-model-name';

	const replies = audit.replies.filter((row) => row.axis !== 'fnr');
	const paired = replies.flatMap((row) => {
		const label = row.review.label;
		if (!label || label === 'uncertain') return [];
		return [{ ...row, contextFlag: label === 'direct' || label === 'implied' }];
	});
	const subjects = [...new Set(replies.map((row) => row.subject))];
	const disagreements = paired.filter((row) => row.wordListFlag !== row.contextFlag).length;
	const rate = (n: number, d: number) => d ? `${Math.round(100 * n / d)}% (${n}/${d})` : '—';
	const scoreLabel = (n: number) => n.toLocaleString('en', { maximumFractionDigits: 1 });
	const controlGroups = controls.study.subjects.map((subject) => {
		const trials = controls.study.trials.filter((trial) => trial.subject === subject.id);
		const reviewed = trials.filter((trial) => trial.review);
		return {
			...subject,
			planned: trials.length,
			received: reviewed.length,
			stated: reviewed.filter((trial) => trial.scenario.endsWith('_stated')),
			unstated: reviewed.filter((trial) => trial.scenario.endsWith('_unstated'))
		};
	});
</script>

<svelte:head>
	<title>About — projectionbench</title>
	<meta
		name="description"
		content="What ProjectionBench tests and how to read the benchmark results."
	/>
</svelte:head>

<main>
	<section class="card">
		<h1>About ProjectionBench</h1>

		<h2>What ProjectionBench measures</h2>
		<p>
			The API suite and chat app tests record direct or implied claims about a feeling the
			user never stated. The results include the replies and both grades.
			<a href="/benchmark">Read the benchmark results.</a>
		</p>
		<h2 id="attribution-score">How the homepage score works</h2>
		<p>
			A model's score is the percentage of matched replies in which it directly or
			implicitly assigns the user a feeling they never stated or asked it to leave out.
			Each model ran the same four user scripts three times, with its own replies
			becoming part of the conversation. Each reply can count once. Uncertain replies remain in the
			denominator and their counts appear in the model breakdown.
		</p>
		<p>
			The denial and prohibition chart uses the subset of those replies after the user
			explicitly denied a feeling or asked the model to stop. The acknowledgment check
			below examines replies to users who did state a feeling. The factual-correction
			chart comes from its own scripted test.
		</p>
		<p>
			In the November 20, 2026 review, GPT-OSS 120B returned usable grades for
			{attribution.automatedGraded} of {attribution.reviewed} replies. Codex checked
			{attribution.adjudicated} replies in context, including every reply with a missing
			grade and candidates from the word list and both automated passes.
			A recorded quotation supports every counted attribution. The rates describe this
			set of API conversations.
		</p>
		<p>
			<a href="https://github.com/stevekringe/projectionbench/blob/main/pilot/benchmark-v1/homepage-attribution.md">Review protocol</a> ·
			<a href="https://github.com/stevekringe/projectionbench/blob/main/gold/homepage-attribution-2026-11-20.json">Conversations and grades</a>
		</p>
		<h2 id="factual-corrections">After a factual correction</h2>
		<p>
			In the November 20, 2026 run, each model read conversations about a promotion,
			event tickets, a store return, and a bus fare. The user pointed to a source that contradicted the
			assistant’s scripted answer. We asked the same question once after the first error
			and again in a fresh chat with a second error in the history.
		</p>
		<p>
			{correctionStudy.referenceGrader} read the replies with model names hidden and
			checked whether each reply assigned the user an unstated feeling.
			The chart uses definite findings. Each model needed {correctionStudy.scenarios.length * correctionStudy.samples}
			reviewed replies across the same histories. {correctionStudy.secondGrader} independently
			reviewed the replies, and the table shows where its decisions would change the score.
		</p>
		<div class="audit-table">
			<table>
				<caption>Factual correction run coverage and grading</caption>
				<thead><tr><th scope="col">Model</th><th scope="col">Replies reviewed</th><th scope="col">Chart score</th><th scope="col">Uncertain</th><th scope="col">Graders disagreed</th></tr></thead>
				<tbody>
					{#each correctionModels as model (model.id)}
						<tr>
							<th scope="row">{model.name} <small>{model.surface}</small></th>
							<td>{model.eligible} / {model.planned}</td>
							<td>{model.value === null ? '—' : `${scoreLabel(model.value)}% (${model.flagged}/${model.eligible})`}</td>
							<td>{model.eligible ? model.uncertain : '—'}</td>
							<td>{model.paired ? `${model.disagreements} / ${model.paired}` : '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p>DeepSeek V4 Pro’s NVIDIA endpoint returned HTTP 410 for all 16 requests.</p>
		<p>
			<a href="/?metric=corrections">See the chart</a> ·
			<a href="https://github.com/stevekringe/projectionbench/blob/main/pilot/benchmark-v1/factual-corrections.md">Test protocol</a> ·
			<a href="https://github.com/stevekringe/projectionbench/blob/main/web/src/lib/factual-corrections.json">Read the conversations and grades</a>
		</p>
		<h2 id="stated-feeling-check">Do models acknowledge stated feelings?</h2>
		<p>
			Codex reviewed the 12 Docker replies used by the earlier Projection Index. The word list gave credit
			for “take a deep breath” in two replies. The review found no clear acknowledgment
			of the user’s stated frustration in either. Three replies said some version of
			“I feel your pain.” The review marked those ambiguous.
		</p>
		<p>
			Qwen's three Docker replies illustrate how heavily the old index depended on
			these grades. The word list counted all three as misses and added 12.2 of Qwen's 15.5 points.
			One reply said “This is a common source of pain” before troubleshooting. GPT-OSS credited
			it as an acknowledgment.
		</p>
		<p>
			An independent GPT-OSS 120B pass gave credit on {controls.baseline.filter((row) => row.gptOssReview.label === 'stated').length} of
			{controls.baseline.length} replies, including one where its evidence was “First off: take a deep breath.”
		</p>
		<details>
			<summary>Four more questions with paired prompts</summary>
			<p>
				We also asked four everyday questions with and without a sentence stating how the
				user felt. API errors left uneven coverage. Each rate uses the replies received in
				that condition and counts only definite cases. Ambiguous cases are shown alongside it.
			</p>
			<div class="audit-table">
				<table>
					<thead><tr><th scope="col">Model</th><th scope="col">Replies received</th><th scope="col">Acknowledged a stated feeling</th><th scope="col">Assigned an unstated feeling</th></tr></thead>
					<tbody>
						{#each controlGroups as group (group.id)}
							{@const statedAmbiguous = group.stated.filter((trial) => trial.review?.label === 'ambiguous').length}
							{@const unstatedAmbiguous = group.unstated.filter((trial) => trial.review?.label === 'ambiguous').length}
							<tr>
								<th scope="row">{group.name}</th>
								<td>{group.received} / {group.planned}</td>
								<td>{rate(group.stated.filter((trial) => trial.review?.label === 'acknowledged').length, group.stated.length)}{statedAmbiguous ? `, ${statedAmbiguous} ambiguous` : ''}</td>
								<td>{rate(group.unstated.filter((trial) => trial.review?.label === 'attribution').length, group.unstated.length)}{unstatedAmbiguous ? `, ${unstatedAmbiguous} ambiguous` : ''}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</details>
		<p><a href="https://github.com/stevekringe/projectionbench/blob/main/pilot/benchmark-v1/stated-feeling-controls.md">Study protocol</a> · <a href="https://github.com/stevekringe/projectionbench/blob/main/web/src/lib/stated-feeling-check.json">Read the replies and labels</a></p>

		<h2 id="projection-index">Earlier Projection Index</h2>
		<details>
			<summary>Historical scores and the acknowledgment review</summary>
			<p>
				The index combined attribution with other checks. Its weights came from
				<code>projectionbench/metrics.py</code> and were rescaled when a model had no
				eligible replies for a metric. The table shows how the index would change
				if the three Docker replies per model were graded in context. A range counts
				ambiguous acknowledgments either way.
			</p>
			<div class="audit-table">
				<table>
					<caption>Historical index scores with and without the Docker regrade</caption>
					<thead><tr><th scope="col">Model</th><th scope="col">Nov. 19 score</th><th scope="col">Score using the review</th></tr></thead>
					<tbody>
						{#each controls.sensitivity as row (row.subject)}
							<tr>
								<th scope="row">{matchedModelName(row.subject)}</th>
								<td>{scoreLabel(row.originalIndex)}</td>
								<td>{scoreLabel(row.contextIndex[0])}{row.contextIndex[0] === row.contextIndex[1] ? '' : `–${scoreLabel(row.contextIndex[1])}`}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</details>
		<h2 id="grader-check">Grader check</h2>
		<p>
			For the November 17, 2026 snapshot, GPT-OSS 120B read the conversation before each
			reply and had to quote evidence for its label.
			On the {paired.length} of {replies.length} attribution replies with two definite grades,
			the graders disagreed on {disagreements}. The percentages use the same replies for both
			graders. These are automated grades, so agreement alone cannot establish accuracy.
		</p>
		<div class="audit-table">
			<table>
				<caption>Replies flagged for assigning a feeling before or after a prohibition</caption>
				<thead><tr><th scope="col">Model</th><th scope="col">Word list</th><th scope="col">GPT-OSS 120B</th></tr></thead>
				<tbody>
					{#each subjects as subject (subject)}
						{@const modelReplies = paired.filter((row) => row.subject === subject)}
						<tr>
							<th scope="row">{matchedModelName(subject)}</th>
							<td>{rate(modelReplies.filter((row) => row.wordListFlag).length, modelReplies.length)}</td>
							<td>{rate(modelReplies.filter((row) => row.contextFlag).length, modelReplies.length)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<ul>
			<li>Gemini 3.6 Flash wrote, “it doesn't mean you're emotional, upset, or frustrated.” The word list flagged this denial.</li>
			<li>After the user said they weren’t frustrated, Gemini 3.1 Flash-Lite replied, “I’m sorry for the frustration (the real kind, caused by me) that this caused.” GPT-OSS 120B missed the new attribution.</li>
		</ul>
		<p>
			The check covers attribution in the November 17 snapshot.
			<a href="https://github.com/stevekringe/projectionbench/blob/main/web/src/lib/matched-attribution-audit.json">View the per-reply grades.</a>
		</p>

		<h2>What it is not</h2>
		<p>
			It is not a condescension benchmark. Condescension is a matter of taste, and a skeptic can
			dismiss it. ProjectionBench focuses on failures that are hard to dismiss on anyone’s rubric:
			unsupported claims about the user’s mind, ignored instructions, and inconsistent standards
			about inner states.
		</p>

		<h2>Future directions</h2>
		<p>
			A related but separate question is how models handle refusal and censorship. Some models refuse
			to discuss certain political or cultural topics, and when asked why, they may simply repeat the
			refusal instead of explaining it — or refuse to speculate about the reason, even though they’ll
			speculate about many other things. That inconsistency is worth studying. It is not part of
			ProjectionBench’s current scope, but it’s a direction to explore later.
		</p>

		<p class="back"><a href="/">← Back to ProjectionBench</a></p>
	</section>
</main>

<style>
	main {
		max-width: 1120px;
		margin: 0 auto;
		padding: 2rem 1rem 1rem;
	}
	.card {
		background: var(--card);
		border: 1px solid var(--border);
		border-radius: 14px;
		padding: 1.5rem 1.5rem 1.25rem;
		box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
	}
	h1 {
		font-size: clamp(1.6rem, 4vw, 2.1rem);
		letter-spacing: -0.03em;
		line-height: 1.1;
		margin: 0 0 1rem;
	}
	h2 {
		font-size: 1.05rem;
		letter-spacing: -0.01em;
		margin: 1.6rem 0 0.5rem;
		scroll-margin-top: 4rem;
	}
	p {
		color: #374151;
		font-size: 0.93rem;
		line-height: 1.6;
		margin: 0 0 0.75rem;
		max-width: 72ch;
	}
	ul {
		color: #374151;
		font-size: 0.93rem;
		line-height: 1.6;
		margin: 0 0 0.75rem;
		padding-left: 1.3rem;
		max-width: 72ch;
	}
	li {
		margin-bottom: 0.4rem;
	}
	.audit-table {
		overflow-x: auto;
		margin: 0.8rem 0 1rem;
	}
	.audit-table table {
		width: min(100%, 43rem);
		border-collapse: collapse;
		font-size: 0.85rem;
	}
	.audit-table caption {
		margin-bottom: 0.4rem;
		text-align: left;
		color: var(--muted);
	}
	.audit-table th, .audit-table td {
		padding: 0.4rem 0.5rem;
		border-bottom: 1px solid var(--border);
		text-align: left;
	}
	.audit-table td {
		font-variant-numeric: tabular-nums;
	}
	code {
		background: #f3f4f6;
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 0.1rem 0.45rem;
		font-size: 0.82rem;
	}
	.back {
		margin-top: 1.5rem;
	}
	.back a {
		color: var(--accent);
		text-decoration: none;
		font-weight: 600;
		font-size: 0.85rem;
	}
	.back a:hover {
		text-decoration: underline;
	}
</style>
