"""
The eval harness: for each chart in the golden set, generate both an
ungrounded narrative (no computed data given) and a grounded narrative
(the real pipeline), verify both against the same real ComputedChart,
and aggregate into an EvalReport.

Both conditions are checked by the exact same verifier - the only
difference between them is what the generator was given to work with.
That symmetry is what makes the comparison fair: it isn't grounded
narratives getting an easier grader, it's the same grader applied to
two different inputs.
"""

import uuid

from app.compute.chart_builder import build_chart
from app.generation.generator import generate_narrative, generate_ungrounded_narrative
from app.verification.verifier import verify_narrative
from app.models.eval import EvalCase, EvalReport
from eval.golden_set.charts import GOLDEN_SET


def run_eval(provider: str = "groq", test_charts: list | None = None) -> EvalReport:
    charts_to_test = test_charts if test_charts is not None else GOLDEN_SET
    cases: list[EvalCase] = []

    for birth in charts_to_test:
        chart = build_chart(birth)
        chart_id = str(uuid.uuid4())

        ungrounded_narrative, ungrounded_model = generate_ungrounded_narrative(birth, provider)
        ungrounded_result = verify_narrative(
            narrative=ungrounded_narrative,
            chart=chart,
            model_used=ungrounded_model,
            chart_id=chart_id,
        )

        grounded_narrative, grounded_model = generate_narrative(chart, provider)
        grounded_result = verify_narrative(
            narrative=grounded_narrative,
            chart=chart,
            model_used=grounded_model,
            chart_id=chart_id,
        )

        cases.append(EvalCase(
            birth_details=birth,
            ungrounded_result=ungrounded_result,
            grounded_result=grounded_result,
        ))

    return EvalReport(provider=provider, cases=cases)
