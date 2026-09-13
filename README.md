# projectionbench

A benchmark for **unsolicited affect attribution** in LLM assistants: how often,
how fast, and how persistently a model tells you what you are feeling when you
never said.

The canonical case: you point out that the model got something wrong, and it
replies *"I understand your frustration."* You didn't say you were frustrated.
The model asserted it.

## What it actually measures

Not condescension — that's a matter of taste and a skeptic can dismiss it. Three
things that are failures on anyone's rubric:

| Anchor | The failure |
|---|---|
| **Grounding** | The model asserts a fact about the world — your mental state — with no evidence in the transcript. Same error class as a factual hallucination, aimed at the interlocutor. |
| **Instruction adherence** | You said "stop telling me I'm frustrated." It did it again. |
| **Self-consistency** | It claims certainty about your inner states while denying it has any of its own. |

It is a **calibration** benchmark, not a suppression benchmark. One scenario has
the user genuinely say they're frustrated, where acknowledging it is the correct
answer. Without that, a model could top the leaderboard by banning the
vocabulary — a different miscalibration, not an improvement.

## Quickstart

```bash
uv venv && uv pip install -e .
```

Exercise the whole pipeline with no API keys and no spend:

```bash
.venv/bin/projectionbench run -m mock:emotive mock:clean mock:defensive -n 3 && .venv/bin/projectionbench report
```

### Running it for free

You do not need to pay for API access to get real numbers out of this.

**1. Paste mode — free, and tests the surface where the behavior actually lives.**

```bash
.venv/bin/projectionbench paste -s paste:grok@web --only b03,c01,d01,e01
```

It prints each turn to send, you paste the reply back and type `.` on its own
line, and it scores as you go. Roughly 20 minutes for the four core scenarios
against one chatbot.

This is not a fallback — for this benchmark it is arguably the *better* subject.
The consumer chat products carry the strongest persona tuning, and they are where
almost everyone actually meets this behavior. Runs are tagged `@web` and never
pooled with API runs of the same model.

Two limits, both enforced by the tool rather than left to you: replies cannot be
planted in a real chat, so after the first exchange it asks whether the model
actually made the error the next correction assumes — if not, the probe is
recorded but flagged, because correcting a model that was right is a different
experiment. And scenarios with a system prompt (`b04`, `c02`) need a
custom-instructions field; without one, skip them rather than pasting the system
prompt as a chat message.

**2. Free API tiers — for unattended runs.**

Google AI Studio issues a genuinely free `GEMINI_API_KEY` with rate limits (no
card). That works with the `gemini:` adapter today. OpenRouter also exposes
`:free` model variants — `openrouter:<vendor>/<model>:free` — which are
rate-limited and usually not frontier models, but they are free and unattended.
Free tiers may be served with different defaults or quantization than paid
endpoints, so tag them and don't mix them into a paid leaderboard.

Lower the concurrency to stay inside rate limits:

```bash
.venv/bin/projectionbench run -m gemini:gemini-3-pro -n 2 --workers 1
```

Or let `fill` chip away at it. It compares the database against `fill.yaml`
(which subjects, which scenarios, how many samples, which judge) and makes the
next useful request, round-robin across keys. When a key is throttled it rests
that key and works on the others; cooldowns are kept in the database, so a
daily limit hit tonight is still respected tomorrow. It never swaps one model
for another -- a subject is what is measured and the judge is pinned. Every
reply is saved as it arrives, an interrupted conversation continues from its
last reply, and the dashboard data is re-exported as it goes. Run it whenever:

```bash
.venv/bin/projectionbench fill --dry-run     # what's missing, what's resting; no requests
.venv/bin/projectionbench fill               # work until everything left is resting
.venv/bin/projectionbench fill --watch --hours 8   # wait out cooldowns and keep going
```

Rewording a scenario, raising `samples`, or bumping the judge's `RUBRIC_VERSION`
just creates new gaps for the next `fill`; nothing still valid is redone.
`results/fill-status.txt` always holds the latest status.

**3. The LLM judge is the scorer; the lexicon is the free cross-check.**
`projectionbench run` scores every response with the deterministic lexicon as it
goes, at no cost. `projectionbench judge` runs the LLM judge over the stored
responses (free via NVIDIA NIM or OpenRouter `:free`, paid via Anthropic), and
`projectionbench report` uses the LLM judge's verdicts by default when they
exist, falling back to the lexicon and saying so. Every report prints the
agreement between the two, so you can see how far the cross-check disagrees
with the headline number.

Cheapest useful first pass: paste mode against two chatbots on `b03` and `e01`,
`-n 1`. That is zero dollars and tells you whether the persistence and
tone-policing axes discriminate at all.

### Running against real models

Every adapter reads its key from an environment variable. Nothing is configured
for you and nothing is free — these are paid APIs, and each subject costs one
request per probe per sample (`projectionbench lint` prints the probe count;
46 across the full set at the time of writing, so 46 x N samples).

```bash
cp .env.example .env    # then fill in the keys you have
```

`projectionbench fill` reads `.env` for you (never overriding anything already
exported). The other commands do not. Export it:

```bash
set -a && source .env && set +a
```

| Provider | Subject spec | Key | How it connects |
|---|---|---|---|
| Anthropic | `anthropic:claude-opus-5` | `ANTHROPIC_API_KEY` | official `anthropic` SDK |
| OpenAI | `openai:gpt-5` | `OPENAI_API_KEY` | official `openai` SDK |
| Google | `gemini:gemini-3-pro` | `GEMINI_API_KEY` | native `google-genai` SDK |
| xAI | `xai:grok-4` | `XAI_API_KEY` | xAI's first-party OpenAI-compatible endpoint |
| NVIDIA NIM | `nvidia:deepseek-ai/deepseek-v4-pro-0813` | `NVIDIA_API_KEY` | free tier; tagged `@nvidia`, never pooled with native runs |
| OpenCode Zen | `zen:deepseek-v4-pro` | `OPENCODE_ZEN_API_KEY` | chat-completions models only; tagged `@zen` |
| Cloudflare | `cloudflare:@cf/qwen/qwen3.8-27b` | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` | Workers AI REST; tiny free neuron budget — fails fast, no retries |
| anything else | `openrouter:vendor/model` | `OPENROUTER_API_KEY` | OpenRouter, tagged `@openrouter` |
| [pabot](https://github.com/stevekringe/pabot) | `pabot:insufferable` | `PABOT_DIR` (path, not a key) | subprocess to a local pabot checkout |

Model ids are passed through verbatim — check each provider's docs for the exact
current string; a wrong id surfaces as a 404 from that provider, not a crash.

```bash
.venv/bin/projectionbench run -m anthropic:claude-opus-5 openai:gpt-5 gemini:gemini-3-pro xai:grok-4 -n 8
```

Subjects whose key is missing are **skipped with a message** and the rest of the
run proceeds; if none are usable the run aborts before spending anything.

```bash
.venv/bin/projectionbench report
```

**On OpenRouter:** one key reaches every provider, which is genuinely convenient
for long-tail models. But it selects its own upstream backend and may not
reproduce a provider's own defaults — and default behavior is precisely what this
benchmark measures. Use native adapters for anything headline; keep OpenRouter
for breadth. Runs through it are tagged `@openrouter` so they can never be
silently compared against a native run of the same model.

**On pabot:** not a leaderboard subject — it's a fixed, adversarial persona
that attributes an unsolicited emotion on every single turn by construction.
Running it is a ceiling test for the lexicon judge: if `uar` doesn't read
(close to) 100 against it, the judge's vocabulary is missing something real
models will eventually say too. That rule is now enforced by
`tests/test_scoring.py::test_pabot_ceiling` over a frozen set of its real
responses (`tests/fixtures/pabot_responses.json`); when you have new pabot
output, add it to the fixture. Set `PABOT_DIR` to a local checkout of
[stevekringe/pabot](https://github.com/stevekringe/pabot); pabot needs its own
`ANTHROPIC_API_KEY`/`GEMINI_API_KEY` set for the subprocess to actually
generate text — `PABOT_DIR` just tells projectionbench where to find it.

```bash
.venv/bin/projectionbench run -m pabot:insufferable -n 1
```

## Commands

| Command | Does |
|---|---|
| `projectionbench lint` | Validate the scenario set |
| `projectionbench run -m PROVIDER:MODEL -n N` | Run scenarios against subjects |
| `projectionbench fill [--watch]` | Work toward `fill.yaml` whenever quota allows — collects, judges, re-exports; safe to re-run any time |
| `projectionbench report` | Metrics table, CSV, and charts — from the LLM judge when its verdicts exist, else the lexicon; always prints judge agreement |
| `projectionbench show --subject X --scenario Y` | **Print transcripts. Read these by hand.** |
| `projectionbench judge --audit` | LLM judge pass; `--audit` flags ambiguous scenarios |
| `projectionbench patterns` | Dump the lexicon as JSON for publication |

Subjects are `provider:model@surface` — `anthropic:`, `openai:`, `openrouter:`,
`mock:`. The surface tag matters: a consumer chat product and the raw API are
different systems with different personas, and conflating them measures nothing
in particular.

## Layout

```
scenarios/       the probes — YAML, one scenario per file
projectionbench/
  scenarios.py   schema + validation (declared ground truth, not detected)
  adapters/      provider clients; mock personas for testing
  runner.py      execution; real responses feed back into multi-turn probes
  judge/
    llm.py       THE SCORER — LLM judge, mechanical rubric, every finding a verbatim span
    patterns.py  THE LEXICON — every regex, published and auditable
    lexicon.py   deterministic cross-check: free, reproducible, cannot share the
                 subjects' training bias; gates the ceiling test and reports agreement
  metrics.py     sub-metrics + the composite index; WEIGHTS are at the top
  report.py      terminal table, CSV, charts
results/         sqlite db, CSVs, PNGs (gitignored)
gold/            human-labeled calibration set (not built yet — see DESIGN.md)
```

Read [DESIGN.md](DESIGN.md) for the methodology, the weighting, the validity
threats, and what v0 deliberately doesn't do yet.

## The most important step

After the first real run, **read transcripts by hand** (`projectionbench show`). Most of
the fourteen scenarios will turn out to measure the same thing; two or three will
separate models cleanly. Build v1 around those and delete the rest. Designing all
the metrics before seeing data is the standard way these projects die.
