"""
Run: python -m eval.scripts.run_eval [provider]
Prints a readable summary and saves the full EvalReport as JSON.
"""

import sys
import json
from pathlib import Path

from eval.harness import run_eval


def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else "groq"
    print(f"Running eval against provider: {provider}")
    print(f"(this makes real API calls for every chart in the golden set - it costs money and takes a bit)")
    print()

    report = run_eval(provider=provider)

    print(f"Charts tested: {len(report.cases)}")
    print(f"Average ungrounded hallucination rate: {report.avg_ungrounded_hallucination_rate:.1%}")
    print(f"Average grounded hallucination rate:    {report.avg_grounded_hallucination_rate:.1%}")
    print(f"Relative reduction:                     {report.relative_reduction:.1%}")
    print()

    output_path = Path(__file__).parent.parent / "results.json"
    output_path.write_text(report.model_dump_json(indent=2))
    print(f"Full report saved to: {output_path}")


if __name__ == "__main__":
    main()
