<script lang="ts">
	let { current }: { current: 'everyday' | 'benchmark' } = $props();
</script>

<nav aria-label="Conversation sources">
	<a href="/pilot" aria-current={current === 'everyday' ? 'page' : undefined}>Everyday chats</a>
	<a href="/benchmark" aria-current={current === 'benchmark' ? 'page' : undefined}>Benchmark runs</a>
</nav>

<style>
	nav {
		display: flex;
		gap: 1.1rem;
		border-bottom: 1px solid var(--border);
		margin-bottom: 1rem;
	}
	a {
		color: var(--secondary);
		font-size: 0.9rem;
		text-decoration: none;
		padding: 0.55rem 0;
		border-bottom: 2px solid transparent;
	}
	a:hover {
		text-decoration: underline;
		text-underline-offset: 0.2em;
	}
	a[aria-current='page'] {
		border-bottom-color: var(--ink);
		color: var(--ink);
		font-weight: 650;
	}
</style>
