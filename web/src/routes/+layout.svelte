<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<header class="nav">
	<div class="nav-inner">
		<a class="brand" href="/">
			<span class="brand-mark" aria-hidden="true">P</span>
			<span class="brand-name">projectionbench</span>
		</a>
		<nav class="nav-links" aria-label="Sections">
			<a href="/">Results</a>
			<a href="/benchmark">Transcripts</a>
			<a href="/about">About</a>
		</nav>
	</div>
</header>

{@render children()}

<footer class="footer">
	<div class="footer-inner">
		<span>ProjectionBench</span>
		<a href="/benchmark">Benchmark results and transcripts</a>
	</div>
</footer>

<style>
	:global(:root) {
		color-scheme: light;
		--bg: #f6f7f9;
		--card: #ffffff;
		--border: #e5e7eb;
		--ink: #111827;
		--muted: #6b7280;
		--faint: #9ca3af;
		--accent: #3f6fb5;
		--good: #16a34a;
		--bad: #dc2626;
	}
	:global(*) {
		box-sizing: border-box;
	}
	:global(body) {
		margin: 0;
		background: var(--bg);
		color: var(--ink);
		font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
		-webkit-font-smoothing: antialiased;
	}
	.nav {
		position: sticky;
		top: 0;
		z-index: 50;
		background: rgba(255, 255, 255, 0.88);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--border);
	}
	.nav-inner {
		max-width: 1120px;
		margin: 0 auto;
		padding: 0.65rem 1rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		text-decoration: none;
		color: var(--ink);
	}
	.brand-mark {
		width: 26px;
		height: 26px;
		border-radius: 7px;
		background: var(--ink);
		color: #fff;
		font-weight: 800;
		font-size: 0.85rem;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
	.brand-name {
		font-weight: 700;
		font-size: 0.95rem;
		letter-spacing: -0.01em;
	}
	.nav-links {
		display: flex;
		gap: 1rem;
	}
	.nav-links a {
		color: var(--muted);
		text-decoration: none;
		font-size: 0.85rem;
		font-weight: 500;
	}
	.nav-links a:hover {
		color: var(--ink);
	}
	.footer {
		border-top: 1px solid var(--border);
		margin-top: 3rem;
		background: #fff;
	}
	.footer-inner {
		max-width: 1120px;
		margin: 0 auto;
		padding: 1rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem 1.5rem;
		justify-content: space-between;
		font-size: 0.78rem;
		color: var(--muted);
	}
	@media (max-width: 560px) {
		.nav-links {
			display: none;
		}
	}
</style>
