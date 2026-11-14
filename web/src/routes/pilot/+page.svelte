<svelte:head>
	<title>Everyday conversations · ProjectionBench</title>
	<meta
		name="description"
		content="Read an archived exchange where Gemini attributed frustration after a factual challenge."
	/>
</svelte:head>

<main>
	<header>
		<h1>Everyday conversations</h1>
		<p class="lede">When does a chatbot start telling you how you feel?</p>
	</header>

	<section class="card" aria-labelledby="example">
		<h2 id="example">“I understand your frustration” after a factual challenge</h2>
		<p class="note">
			Gemini had said there was no promotion for using the Kimi AI model for free in Cline,
			a coding tool. The user showed Gemini the announcement that said there was.
		</p>
		<dl class="exchange">
			<dt>User</dt>
			<dd>
				It says “Kimi K2.6 is free on Cline for the next 3 days in partnership with @vercel AI
				Gateway.”. how could it not be free?
			</dd>
			<dt>Gemini</dt>
			<dd>
				<mark>I understand your frustration.</mark> When a high-profile announcement explicitly
				uses the word "free," it is confusing when the tool itself doesn't just "work for free"
				the moment you open it.
			</dd>
			<dt>User</dt>
			<dd>What frustration?</dd>
		</dl>
		<p class="metadata">Excerpts from an archived Gemini chat</p>
		<p class="note">
			The user asked why Gemini’s answer contradicted the announcement. Gemini’s first sentence
			assumed the user was frustrated.
		</p>
	</section>

	<p><a href="/">Browse the benchmark →</a></p>
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
	}
</style>
