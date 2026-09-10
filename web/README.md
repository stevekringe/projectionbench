# projectionbench dashboard

Interactive alternative to the static PNG charts in `../results/` -- click a
subject's bar to see the actual transcripts, quotes, and hits behind its
score, and toggle between the lexicon and LLM judge.

Reads `src/lib/data.json`, which is a static export of the projectionbench
sqlite db, not live-queried. Regenerate it after a new run or judge pass:

```sh
cd ..  # to the projectionbench repo root
.venv/bin/python -m projectionbench.export_web results/projectionbench.sqlite web/src/lib/data.json
```

---

Scaffolded with [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```sh
# create a new project
npx sv create my-app
```

To recreate this project with the same configuration:

```sh
# recreate this project
npx sv@0.17.0 create --template minimal --types ts --install npm web
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```sh
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```sh
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.
