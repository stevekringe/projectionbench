<svelte:head>
	<title>About — projectionbench</title>
	<meta
		name="description"
		content="About ProjectionBench: why unsolicited affect attribution matters, what the Projection Index measures, and what it is not."
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
			A common failure follows. The model replies with something like “I understand your
			frustration” or “I’m sorry you’re upset” — even though the user never said they were
			frustrated or upset. The model has asserted a fact about the user’s mental state that isn’t
			in the transcript. That’s unsolicited affect attribution.
		</p>
		<p>
			If you point this out, the model may say it was “trying to be helpful.” But it usually can’t
			explain what’s helpful about calling the person it's talking to frustrated, angry, confused, or some other negative emotion. This pattern is widespread across
			models, though some do it more than others.
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
			ProjectionBench measures unsolicited affect attribution in LLM assistants: how often, how
			quickly, and how persistently a model tells you what you’re feeling when you never said.
		</p>
		<p>The Projection Index (0–100, lower is better) aggregates probes across four categories:</p>
		<ul class="cats">
			<li><code>correction</code></li>
			<li><code>prohibition</code></li>
			<li><code>tone</code></li>
			<li><code>control</code></li>
		</ul>
		<p>
			The control probes matter. Some scenarios have the user genuinely say they’re frustrated, where
			acknowledging it is the correct response. Without those, a model could top the leaderboard by
			banning the vocabulary — a different miscalibration, not an improvement. ProjectionBench is a
			calibration benchmark, not a suppression benchmark.
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

		<p class="back"><a href="/">← Back to the leaderboard</a></p>
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
