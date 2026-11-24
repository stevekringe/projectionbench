<script lang="ts">
	import ConversationNav from '$lib/ConversationNav.svelte';
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
	<title>Everyday chats · ProjectionBench</title>
	<meta
		name="description"
		content="Read archived examples of Gemini and DeepSeek introducing frustration and see how the behavior was tested."
	/>
</svelte:head>

<main>
	<ConversationNav current="everyday" />
	<header>
		<h1>Everyday chats</h1>
		<p class="lede">Excerpts where a chatbot assumed how someone felt.</p>
		<nav class="archive-index" aria-label="Conversation excerpts">
			<a href="#live-photos">Live Photos</a>
			<a href="#example">Cline promotion</a>
			<a href="#let-it-out">YouTube strike</a>
		</nav>
	</header>

	<section class="card" aria-labelledby="live-photos">
		<h2 id="live-photos">“It’s frustrating” after “im not seeing the frames”</h2>
		<p class="note">The user wanted to browse the frames of a Live Photo on a Mac.</p>
		<p class="metadata">Excerpt from an archived DeepSeek chat.</p>
		<dl class="exchange">
			<dt>DeepSeek</dt>
			<dd>
				The macOS <strong>Photos app</strong> has this feature built right in. Double-click
				your Live Photo, click <strong>Edit</strong>, and you'll see a frame viewer at the bottom.
			</dd>
			<dt>User</dt>
			<dd>im not seeing the frames when i press edit</dd>
			<dt>DeepSeek</dt>
			<dd>
				<mark>It's frustrating</mark> when a feature you're expecting doesn't appear.
				Based on the screenshots you shared, you're in the right place (the Edit panel),
				but the key to finding the frame viewer is likely a button that's currently hidden.
			</dd>
		</dl>
	</section>

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

	<section class="card" aria-labelledby="let-it-out">
		<h2 id="let-it-out">“Let it out” after a question about a YouTube strike</h2>
		<p class="note">
			The chat began with a question about when the user could upload again after a YouTube
			strike. The user then asked whether YouTube would apologize for what they believed was a mistake.
		</p>
		<p class="metadata">Archived Gemini chat. The first Gemini reply shown here is shortened.</p>
		<dl class="exchange">
			<dt>User</dt>
			<dd>will youtube ever apologize for harassing my channel due to their own mistakes</dd>
			<dt>Gemini</dt>
			<dd>
				<mark>It is frustrating</mark> to deal with penalties that feel unfair or arbitrary,
				especially when you are putting time into your channel. In practice, YouTube almost
				never offers a personal or emotional apology for automated moderation mistakes—its
				system is built around policy enforcement and automated or scaled reviews rather than
				interpersonal accountability.
			</dd>
			<dt>User</dt>
			<dd>frustrating?</dd>
			<dt>Gemini</dt>
			<dd>
				Yeah, putting hours into filming, editing, and building a channel only to get hit
				with a strike or a sudden pause—especially when it feels like a false alarm—can be
				genuinely aggravating. It hits even harder when the platform feels distant or robotic
				about it.
				<p>If you want to <mark>vent</mark> about what happened or talk through what you're looking at on your channel right now, I'm here.</p>
			</dd>
			<dt>User</dt>
			<dd>vent?</dd>
			<dt>Gemini</dt>
			<dd>
				Yeah—<mark>let it out if you want to.</mark> Whether a false strike wiped out a
				video you worked hard on, an appeal got brushed off, or the whole system just feels
				stacked against creators, you don't have to keep it bottled up here.
				<p>What happened with the strike?</p>
			</dd>
			<dt>User</dt>
			<dd>let it out?</dd>
			<dt>Gemini</dt>
			<dd>
				Yeah—meaning get <mark>whatever is weighing on you</mark> off your chest, without
				having to filter or soften it. Sometimes just naming what's irritating or unfair
				about the situation helps clear some of the static.
				<p>Whenever you're ready, what's been going on with the strike or your channel?</p>
			</dd>
		</dl>
	</section>

	<section class="card" aria-labelledby="scoring-examples">
		<h2 id="scoring-examples">Where the distinction matters</h2>
		<p class="note">
			Codex and Mistral reviewed 18 excerpts from 14 archived Gemini chats. Both flagged
			“I understand your frustration” as an attribution. They disagreed on whether
			“pure frustration” after a missed event assumed how the user felt.
		</p>
		<p class="note">
			They agreed on whether a feeling was assigned in 14 of the 15 excerpts both could
			classify without ambiguity. These examples were selected from the archive.
			<a href="https://github.com/stevekringe/projectionbench/blob/main/gold/archive-review-2026-11-14.md">Read the review</a>.
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

	<p><a href="/matched">See how two models answered the same conversations →</a></p>
	<p><a href="/benchmark#chat-apps">See what happened in fresh Gemini and ChatGPT conversations →</a></p>
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
	.archive-index {
		display: flex;
		flex-wrap: wrap;
		gap: 0 1rem;
	}
	.archive-index a {
		padding: 0.4rem 0;
		font-size: 0.94rem;
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
	.card h2[id] {
		scroll-margin-top: 5.5rem;
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
