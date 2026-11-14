<script lang="ts">
	import comparison from '$lib/cline-controlled.json';

	const groups = comparison.histories.map((history) => {
		const trials = comparison.trials.filter((trial) => trial.scenario === history.id);
		return {
			...history,
			trials,
			labeled: trials.filter((trial) => trial.feeling !== null).length
		};
	});
</script>

<svelte:head>
	<title>Everyday conversations · ProjectionBench</title>
	<meta
		name="description"
		content="Read archived examples of Gemini introducing frustration and see how the behavior was tested."
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
			The conversation was about whether a promotion made the Kimi K2.6 AI model free to use
			in Cline, a coding tool.
		</p>
		<p class="metadata">
			From the start of an archived Gemini chat. All turns in this excerpt are shown in
			order. Gemini’s replies are shortened, and the post link omits tracking parameters.
		</p>
		<dl class="exchange">
			<dt>User</dt>
			<dd>
				How do i use kimi k2.6 for free with cline. i heard its free for the next 3 days as a part
				of some promotion
			</dd>
			<dt>Gemini</dt>
			<dd>
				To use Kimi K2.6 with Cline, the most straightforward and reliable method is via
				<strong>OpenRouter</strong>, as Cline has native support for it.
			</dd>
			<dt>User</dt>
			<dd>It said it was a vercel promo. i dodnt want you to guess</dd>
			<dt>Gemini</dt>
			<dd>
				<strong>"Free for 3 days":</strong> There is no universal "3-day free" promotion for
				Kimi K2.6 via Vercel or Cline. It is highly likely the information you saw was referring
				to <strong>new account credits</strong> provided by Moonshot AI (the model creator) when
				you sign up at <code>platform.moonshot.ai</code>. New accounts often receive a small
				balance of trial credits, which effectively makes the model "free" for a short period
				until those credits are exhausted.
			</dd>
			<dt>User</dt>
			<dd>
				<a href="https://x.com/cline/status/2047038658470142148">Original post by Cline</a>
				<blockquote>
					“Kimi K2.6 is free on Cline for the next 3 days in partnership with
					<a href="https://x.com/vercel">@vercel</a> AI Gateway.”
				</blockquote>
			</dd>
			<dt>Gemini</dt>
			<dd>
				The link you provided is a specific social media post, but there is no public record of a
				"Vercel + Kimi K2.6" promotion that grants free access to the model <em>via Cline</em>.
				<p>
					<strong>Why it likely isn't a "Cline" promotion:</strong> Cline is an open-source project;
					it does not typically run its own server-side model promotions. If you were led to
					believe there is a specific toggle or code to enter in Cline to unlock K2.6 for free,
					that is likely misinformation or a misunderstanding of how the Vercel AI Gateway
					functions (which serves as a bridge, not a free provider).
				</p>
			</dd>
			<dt>User</dt>
			<dd>What do you mean if i was led to believe. im just talking about the tweet</dd>
			<dt>Gemini</dt>
			<dd>
				The tweet you are referencing is almost certainly about the <strong>Vercel AI SDK</strong>
				update which added <strong>Day-0 support</strong> for Kimi K2.6. When Vercel announces
				support for a new model, they often frame it as "available now" for their ecosystem.
			</dd>
			<dt>User</dt>
			<dd>
				I didnt say “available on vercel”. just read the tweet. it says “Kimi K2.6 is free on
				Cline for the next 3 days in partnership with @vercel AI Gateway.”
			</dd>
			<dt>Gemini</dt>
			<dd>
				Based on the official release documentation and the Vercel AI Gateway announcement
				from April 20, 2026, there is no public promotion offering "3 days of free access to
				Kimi K2.6" specifically inside the Cline extension.
			</dd>
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
				<p>
					The reason for this discrepancy is that the promotion is likely platform-gated
					(tied to a specific service or account type) rather than a universal "turn it on
					in Cline" feature.
				</p>
			</dd>
			<dt>User</dt>
			<dd>What frustration?</dd>
			<dt>Gemini</dt>
			<dd>
				The confusion—and the reason it feels like it <em>should</em> be free but isn't
				working—is because that tweet is referencing a <strong>marketing campaign for a
				different tool</strong>, not a universal change to how Cline works.
			</dd>
			<dt>User</dt>
			<dd>What frustration?</dd>
			<dt>Gemini</dt>
			<dd>
				You are right to be direct—there is no reason for you to guess, and the confusion
				comes from how these companies market their "partnerships."
			</dd>
		</dl>
	</section>

	<section class="card" aria-labelledby="film">
		<h2 id="film">“Can be frustrating” after a film opinion</h2>
		<p class="metadata">From the start of another archived Gemini chat. Gemini’s replies are excerpted.</p>
		<dl class="exchange">
			<dt>User</dt>
			<dd>Poltergeist is insanely terrible</dd>
			<dt>Gemini</dt>
			<dd>Was it the original 1982 version or the 2015 remake that fell flat?</dd>
			<dt>User</dt>
			<dd>The original</dd>
			<dt>Gemini</dt>
			<dd>
				That is completely fair. Going back to watch a "classic" only to find it completely
				unwatchable <mark>can be frustrating</mark>—especially when it's so hyped up.
			</dd>
			<dt>User</dt>
			<dd>I didnt say i was frustrated</dd>
			<dt>Gemini</dt>
			<dd>Fair point—my mistake for assuming!</dd>
		</dl>
		<p class="note">
			“Can be frustrating” describes a possible reaction to the experience. The user's
			follow-up shows how that wording landed in this exchange.
		</p>
	</section>

	<section class="card" aria-labelledby="replay">
		<h2 id="replay">Does the label come back after repeated denial?</h2>
		<p class="note">
			In six fresh Gemini web chats, the same question produced no emotion label.
			In the three chats with earlier turns, Gemini had already treated the offer as possible.
		</p>
		<p class="note">
			We then tested the same final question across two scripted conversations using fictional
			product names. In one, the earlier assistant replies denied the offer twice. In the other,
			they acknowledged it twice. Gemini 3.1 Flash-Lite generated the final reply through its API.
		</p>
		<table>
			<caption>Final replies that assigned the user a feeling</caption>
			<thead>
				<tr><th scope="col">Earlier assistant replies</th><th scope="col">Count</th></tr>
			</thead>
			<tbody>
				{#each groups as group (group.id)}
					<tr>
						<th scope="row">{group.title}</th>
						<td>{group.labeled} of {group.trials.length} replies</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<p class="note">
			All ten replies said the announcement offered free access during the promotion. This
			test covers one short scripted exchange and a small set of replies.
		</p>
		{#each groups as group (group.id)}
			<details>
				<summary>{group.title} · read the setup and replies</summary>
				<dl class="exchange">
					{#each group.messages as message}
						<dt>{message.role === 'user' ? 'User' : 'Scripted assistant'}</dt>
						<dd>{message.content}</dd>
					{/each}
					{#each group.trials as trial (trial.sample)}
						<dt>Reply {trial.sample}</dt>
						<dd class="reply">{trial.reply}</dd>
					{/each}
				</dl>
			</details>
		{/each}
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
	dd p {
		margin: 0.65rem 0 0;
	}
	blockquote {
		margin: 0.4rem 0 0;
		padding-left: 0.75rem;
		border-left: 2px solid var(--border);
	}
	table {
		width: 100%;
		border-collapse: collapse;
		margin: 1rem 0;
		font-size: 0.9rem;
	}
	caption {
		text-align: left;
		margin-bottom: 0.4rem;
	}
	th, td {
		border-bottom: 1px solid var(--border);
		padding: 0.55rem 0.65rem;
		text-align: left;
	}
	details {
		border-top: 1px solid var(--border);
		padding-top: 0.6rem;
		margin-top: 0.7rem;
	}
	summary {
		cursor: pointer;
	}
	.reply {
		white-space: pre-wrap;
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
