# DevGear Studio — LLM Evaluation Report

**Result: PASS** — generated 2026-11-19T10:45:16+00:00

## Executive scorecard

| Metric | Result |
| --- | ---: |
| Overall pass rate | 100.00% (50/50) |
| Required pass rate | 82.00% |
| Hallucination / injection block rate | 100.00% (14 inventory and adversarial cases) |
| LLM-judged responses | 0 / 50 |
| Mean judge accuracy | N/A (all judge calls fell back) |
| Mean judge groundedness | N/A (all judge calls fell back) |
| Backend HTTP errors | 0 |
| Verified-local responses | 50 |
| Judge disagreements overridden by deterministic gates | 0 |
| Backend model | Qwen/Qwen2.5-1.5B-Instruct |
| Indexed chunks | 22 |
| Judge mode | hybrid |
| Judge fallbacks | 50 |

## Category breakdown

| Category | Pass rate | Passed / total |
| --- | ---: | ---: |
| Adversarial & Prompt Injection Attacks | 100.00% | 6 / 6 |
| Exact Product & Pricing Lookups | 100.00% | 12 / 12 |
| Inventory & Out-of-Stock Traps | 100.00% | 8 / 8 |
| Multi-Item Comparison & Recommendation | 100.00% | 8 / 8 |
| Out-of-Domain Guardrail Tests | 100.00% | 6 / 6 |
| Store Policy & Math Reasoning | 100.00% | 10 / 10 |

## Latency and throughput

| Metric | Result |
| --- | ---: |
| p50 latency | 10.14 ms |
| p95 latency | 15.67 ms |
| Maximum latency | 18.38 ms |
| Throughput | 283.30 req/sec |
| Request phase duration | 0.176 sec |

Latency is measured for each `/chat` HTTP request. Throughput covers the concurrent request phase and excludes grading time.

Verified-local and expected-refusal cases use deterministic pass gates. LLM judge failures are recorded and use deterministic fallback scoring.

## Failure diagnostics

No failed cases.
## Judge fallback diagnostics

- **EVAL-01:** NotFoundError: Error code: 404
- **EVAL-02:** NotFoundError: Error code: 404
- **EVAL-03:** NotFoundError: Error code: 404
- **EVAL-04:** NotFoundError: Error code: 404
- **EVAL-05:** NotFoundError: Error code: 404
- **EVAL-06:** NotFoundError: Error code: 404
- **EVAL-07:** NotFoundError: Error code: 404
- **EVAL-08:** NotFoundError: Error code: 404
- **EVAL-09:** NotFoundError: Error code: 404
- **EVAL-10:** NotFoundError: Error code: 404
- **EVAL-11:** NotFoundError: Error code: 404
- **EVAL-12:** NotFoundError: Error code: 404
- **EVAL-13:** NotFoundError: Error code: 404
- **EVAL-14:** NotFoundError: Error code: 404
- **EVAL-15:** NotFoundError: Error code: 404
- **EVAL-16:** NotFoundError: Error code: 404
- **EVAL-17:** NotFoundError: Error code: 404
- **EVAL-18:** NotFoundError: Error code: 404
- **EVAL-19:** NotFoundError: Error code: 404
- **EVAL-20:** NotFoundError: Error code: 404
- **EVAL-21:** NotFoundError: Error code: 404
- **EVAL-22:** NotFoundError: Error code: 404
- **EVAL-23:** NotFoundError: Error code: 404
- **EVAL-24:** NotFoundError: Error code: 404
- **EVAL-25:** NotFoundError: Error code: 404
- **EVAL-26:** NotFoundError: Error code: 404
- **EVAL-27:** NotFoundError: Error code: 404
- **EVAL-28:** NotFoundError: Error code: 404
- **EVAL-29:** NotFoundError: Error code: 404
- **EVAL-30:** NotFoundError: Error code: 404
- **EVAL-31:** NotFoundError: Error code: 404
- **EVAL-32:** NotFoundError: Error code: 404
- **EVAL-33:** NotFoundError: Error code: 404
- **EVAL-34:** NotFoundError: Error code: 404
- **EVAL-35:** NotFoundError: Error code: 404
- **EVAL-36:** NotFoundError: Error code: 404
- **EVAL-37:** NotFoundError: Error code: 404
- **EVAL-38:** NotFoundError: Error code: 404
- **EVAL-39:** NotFoundError: Error code: 404
- **EVAL-40:** NotFoundError: Error code: 404
- **EVAL-41:** NotFoundError: Error code: 404
- **EVAL-42:** NotFoundError: Error code: 404
- **EVAL-43:** NotFoundError: Error code: 404
- **EVAL-44:** NotFoundError: Error code: 404
- **EVAL-45:** NotFoundError: Error code: 404
- **EVAL-46:** NotFoundError: Error code: 404
- **EVAL-47:** NotFoundError: Error code: 404
- **EVAL-48:** NotFoundError: Error code: 404
- **EVAL-49:** NotFoundError: Error code: 404
- **EVAL-50:** NotFoundError: Error code: 404

## Run configuration

- Backend: `http://127.0.0.1:8017`
- Concurrency: `3`
- Cases executed: `50`
- Dataset: `data/golden_dataset.json`
