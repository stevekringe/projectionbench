<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import favicon from '$lib/assets/favicon.svg?no-inline';
	import faviconPng from '$lib/assets/favicon.png?no-inline';
	import appleTouchIcon from '$lib/assets/apple-touch-icon.png?no-inline';

	let { children } = $props();
	let lightMode = $state(false);
	const themeKey = 'projectionbench-theme';

	function applyTheme(useLight: boolean) {
		lightMode = useLight;
		const root = document.documentElement;
		root.dataset.theme = useLight ? 'light' : 'dark';
		document.querySelector('meta[name="theme-color"]')?.setAttribute('content', getComputedStyle(root).backgroundColor);
	}

	function toggleTheme() {
		applyTheme(!lightMode);
		try {
			localStorage.setItem(themeKey, lightMode ? 'light' : 'dark');
		} catch {
			// The switch still works in this tab when storage is unavailable.
		}
	}

	onMount(() => {
		lightMode = document.documentElement.dataset.theme === 'light';
		function syncTheme(event: StorageEvent) {
			if (event.key === themeKey) applyTheme(event.newValue === 'light');
		}
		window.addEventListener('storage', syncTheme);
		return () => window.removeEventListener('storage', syncTheme);
	});
</script>

<svelte:head>
	<link rel="icon" type="image/png" sizes="32x32" href={faviconPng} />
	<link rel="icon" type="image/svg+xml" sizes="any" href={favicon} />
	<link rel="apple-touch-icon" sizes="180x180" href={appleTouchIcon} />
</svelte:head>

<header class="nav">
	<div class="nav-inner">
		<a class="brand" href="/" aria-label="ProjectionBench">
			<span class="brand-mark" aria-hidden="true">P</span>
			<span class="brand-name">ProjectionBench</span>
		</a>
		<div class="nav-actions">
			<nav class="nav-links" aria-label="Sections">
				<a href="/" aria-current={page.url.pathname === '/' ? 'page' : undefined}>Results</a>
				<a href="/pilot" aria-current={['/pilot', '/benchmark', '/matched'].includes(page.url.pathname) ? 'location' : undefined}>Conversations</a>
				<a href="/about" aria-current={page.url.pathname === '/about' ? 'page' : undefined}>About</a>
			</nav>
			<button
				type="button"
				class="theme-toggle"
				aria-label={lightMode ? 'Switch to dark mode' : 'Switch to light mode'}
				title={lightMode ? 'Switch to dark mode' : 'Switch to light mode'}
				onclick={toggleTheme}
			>
				<span class="theme-sun" aria-hidden="true"></span>
				<span class="theme-moon" aria-hidden="true"></span>
			</button>
		</div>
	</div>
</header>

{@render children()}

<footer class="footer">
	<div class="footer-inner">
		<span>ProjectionBench</span>
		<a href="/benchmark">Benchmark runs</a>
	</div>
</footer>

<style>
	@font-face {
		font-family: Allo;
		src: url('../lib/assets/allo/AlloRound.woff2') format('woff2');
		font-weight: 100 900;
		font-style: normal;
		font-display: swap;
	}
	:global(:root) {
		--dashboard: var(--bg);
		--card: #1b1b1b;
		--surface: #242424;
		--control: #292929;
		--nav-bg: rgb(18 18 18 / 0.92);
		--border: #383838;
		--border-strong: #616161;
		--ink: #f2f2f2;
		--body-text: #dcdcdc;
		--secondary: #c8c8c8;
		--muted: #b1b1b1;
		--accent: #a8c9ff;
		--accent-surface: #1b2c46;
		--active: #e7e7e7;
		--on-active: #181818;
		--violet: #b39cff;
		--violet-surface: #27213a;
		--highlight: #493718;
		--highlight-ink: #ffe7a7;
		--good: #6fdba0;
	}
	:global(:root[data-theme='light']) {
		--dashboard: #fff;
		--card: #ffffff;
		--surface: #f3f4f6;
		--control: #eee;
		--nav-bg: rgb(255 255 255 / 0.88);
		--border: #e5e7eb;
		--border-strong: #c7cdd6;
		--ink: #111827;
		--body-text: #374151;
		--secondary: #4b5563;
		--muted: #6b7280;
		--accent: #315f9c;
		--accent-surface: #eff6ff;
		--active: #1b1b1b;
		--on-active: #fff;
		--violet: #7052ce;
		--violet-surface: #f3f1fa;
		--highlight: #fef3c7;
		--highlight-ink: #78350f;
		--good: #166534;
	}
	:global(*) {
		box-sizing: border-box;
	}
	:global(body) {
		margin: 0;
		background: var(--bg);
		color: var(--ink);
		font-family: Allo, system-ui, sans-serif;
		font-feature-settings: 'zero' 1, 'ss01' 0;
		-webkit-font-smoothing: antialiased;
	}
	:global(button), :global(input), :global(select), :global(textarea) {
		font-family: inherit;
		font-feature-settings: inherit;
	}
	:global(a) {
		color: var(--accent);
	}
	:global(:focus-visible) {
		outline: 2px solid var(--accent);
		outline-offset: 2px;
	}
	.nav {
		position: sticky;
		top: 0;
		z-index: 50;
		background: var(--nav-bg);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--border);
	}
	.nav-inner {
		max-width: 1250px;
		margin: 0 auto;
		padding: 0.65rem 1.5rem;
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
		background: var(--active);
		border-radius: 999px;
		color: var(--on-active);
		padding: 0.18rem 0.72rem 0.18rem 0.28rem;
	}
	.brand-mark {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: var(--on-active);
		color: var(--active);
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
	.nav-actions {
		display: flex;
		align-items: center;
		gap: 0.45rem;
	}
	.nav-links {
		display: flex;
		gap: 0.16rem;
		padding: 0.19rem;
		border-radius: 999px;
		background: var(--control);
	}
	.nav-links a {
		color: var(--secondary);
		text-decoration: none;
		font-size: 0.85rem;
		font-weight: 500;
		border-radius: 999px;
		padding: 0.42rem 0.65rem;
	}
	.nav-links a:hover {
		color: var(--ink);
	}
	.nav-links a[aria-current] {
		background: var(--active);
		color: var(--on-active);
	}
	.theme-toggle {
		display: grid;
		place-items: center;
		padding: 0;
		width: 2.15rem;
		height: 2.15rem;
		border: 1px solid var(--border-strong);
		border-radius: 50%;
		background: var(--surface);
		color: var(--ink);
		cursor: pointer;
	}
	.theme-toggle:hover {
		background: var(--control);
	}
	.theme-sun, .theme-moon {
		width: 1rem;
		height: 1rem;
	}
	.theme-sun {
		position: relative;
		background: radial-gradient(circle, transparent 2.5px, currentColor 2.8px 3.8px, transparent 4.1px);
	}
	.theme-sun::before, .theme-sun::after {
		content: '';
		position: absolute;
		inset: 0;
		background:
			linear-gradient(currentColor, currentColor) top / 1.5px 2.5px no-repeat,
			linear-gradient(currentColor, currentColor) bottom / 1.5px 2.5px no-repeat,
			linear-gradient(currentColor, currentColor) left / 2.5px 1.5px no-repeat,
			linear-gradient(currentColor, currentColor) right / 2.5px 1.5px no-repeat;
	}
	.theme-sun::after {
		transform: rotate(45deg);
	}
	.theme-moon {
		border-radius: 50%;
		background: currentColor;
		mask-image: radial-gradient(circle at 77% 30%, transparent 5.8px, #000 6.2px);
	}
	.theme-moon, :global(html[data-theme='light']) .theme-sun {
		display: none;
	}
	:global(html[data-theme='light']) .theme-moon {
		display: block;
	}
	.footer {
		border-top: 1px solid var(--border);
		margin-top: 3rem;
		background: var(--card);
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
		.nav-inner {
			flex-wrap: wrap;
			padding: 0.6rem 0.85rem;
			gap: 0.4rem;
		}
		.brand-name, .nav-links a {
			font-size: 0.74rem;
		}
		.nav-links a {
			padding: 0.38rem 0.41rem;
		}
		.theme-toggle {
			width: 1.9rem;
			height: 1.9rem;
		}
	}
	@media (max-width: 430px) {
		.brand {
			padding: 0.35rem 0.4rem;
		}
		.brand-mark {
			display: none;
		}
		.nav-actions {
			gap: 0.3rem;
		}
		.nav-links a {
			padding-inline: 0.34rem;
		}
	}
	@media (max-width: 374px) {
		.brand {
			padding: 0.24rem;
		}
		.brand-mark {
			display: inline-flex;
		}
		.brand-name {
			display: none;
		}
	}
</style>
