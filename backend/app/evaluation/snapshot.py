from app.evaluation.cache import DEFAULT_REQUEST, SNAPSHOT_PATH
from app.evaluation.comparison import run_comparison


def main() -> None:
  """Regenerate the committed default comparison. Run after changing any strategy, the
  generator, or the scoring, or tests/test_comparison.py will flag the snapshot as stale.
  """
  result = run_comparison(DEFAULT_REQUEST)
  SNAPSHOT_PATH.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
  print(f"Wrote {SNAPSHOT_PATH} ({len(result.per_seed)} per-seed rows)")


if __name__ == "__main__":
  main()
