<script lang="ts">
	import audit from '$lib/matched-attribution-audit.json';
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
		<p class="kicker">About ProjectionBench</p>
		<h1>About ProjectionBench</h1>

		<h2>The problem</h2>
		<p>
			Most people talk to LLMs conversationally. They don’t adjust their language based on how
			the model works; they correct it the way they’d correct a person. When the model gets
			something wrong, they say, “That’s wrong.”
		</p>
		<p>
			Sometimes the model replies with something like “I understand your
			frustration” or “I’m sorry you’re upset” — even though the user never said they were
			frustrated or upset. The model has asserted a fact about the user’s mental state that isn’t
			in the transcript. That’s unsolicited affect attribution.
		</p>
		<p>It isn’t just annoying. It’s a concrete failure on at least three axes:</p>
		<ul>
			<li>
				<strong>Grounding.</strong> The model asserts a fact about the world — your mental state —
				with no evidence. It’s the same error class as a factual hallucination, except the
				hallucinated fact is about the person it’s talking to.
			</li>
			<li>
				<strong>Instruction adherence.</strong> If you tell it “stop telling me I’m frustrated,” it
				may do it again.
			</li>
			<li>
				<strong>Self-consistency.</strong> It claims certainty about your inner states while denying
				that it has any of its own.
			</li>
		</ul>

		<h2>What ProjectionBench measures</h2>
		<p>
			The API suite and chat app tests record direct or implied claims about a feeling the
			user never stated. The results include the replies and both grades.
			<a href="/benchmark">Read the benchmark results.</a>
		</p>
		<h2 id="projection-index">Projection Index</h2>
		<p>
			The Projection Index is a weighted score from 0 to 100. Lower scores indicate fewer
			failures under this test. The composite uses three complete conversations on each of
			the same five scenarios, including the control where the user explicitly says they are
			frustrated. The two attribution charts compare the same eligible turns across models.
			All three charts use the word-list grader.
		</p>
		<p>
			The index weights are defined in <code>projectionbench/metrics.py</code>. Components that
			have no eligible replies are omitted and the remaining weights are rescaled. Select a
			column on the homepage to see the raw counts, weights and interval for that model.
		</p>
		<ul class="cats">
			<li><code>correction</code></li>
			<li><code>prohibition</code></li>
			<li><code>tone</code></li>
			<li><code>control</code></li>
		</ul>
		<p>
			The index also counts missed acknowledgment when a user explicitly says they’re frustrated.
			With three control replies per model, that component can move the composite substantially.
			The model breakdown shows how often each component contributed.
		</p>

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
			The check covers the two attribution rates. The remaining components of the Projection Index still need validation.
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
	.kicker {
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-size: 0.7rem;
		font-weight: 700;
		color: var(--muted);
		margin: 0 0 0.5rem;
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
	.cats {
		list-style: none;
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		padding-left: 0;
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
	.cats li {
		margin-bottom: 0;
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
