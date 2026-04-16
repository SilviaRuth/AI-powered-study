# Benchmark

The starter benchmark lives in `data/eval/golden_set.json`.

The evaluation runner records:

- `hit@k`
- `recall@k`
- `MRR`
- citation correctness
- unsupported answer rate
- correct `I don't know` rate

Run it locally with:

```powershell
python scripts/run_eval.py
```

Results are written to `data/eval/last_run.json`.
