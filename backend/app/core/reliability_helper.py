from dataclasses import dataclass, field
from typing import List

@dataclass
class ReliabilityAssessment:
    level: str  # "UNRELIABLE" | "VERY_LIMITED" | "LIMITED" | "STANDARD"
    confidence: str  # "none" | "low" | "medium" | "high"
    severity: str  # "info" | "warning" | "critical"
    can_infer: bool
    can_model: bool
    can_hypothesis_test: bool
    can_visualize: bool
    requires_caution_flag: bool
    explanation: str
    warnings: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    policy_version: str = "1.0"

    def is_reliable(self) -> bool:
        return self.level == "STANDARD"

    def is_warning(self) -> bool:
        return self.level in ("LIMITED", "VERY_LIMITED")

    def requires_caution(self) -> bool:
        return self.requires_caution_flag


class ReliabilityHelper:
    """
    Centralized source of truth for assessing the statistical reliability of a dataset.
    Caps reliability properties and recommended actions based on row count.
    """

    @staticmethod
    def assess(rows: int) -> ReliabilityAssessment:
        if rows <= 1:
            return ReliabilityAssessment(
                level="UNRELIABLE",
                confidence="none",
                severity="critical",
                can_infer=False,
                can_model=False,
                can_hypothesis_test=False,
                can_visualize=True,
                requires_caution_flag=True,
                explanation="The dataset contains a single observation. Meaningful statistical inference cannot be performed because additional observations are required.",
                warnings=[
                    "Correlation analysis is unreliable.",
                    "Distribution analysis is not meaningful.",
                    "Hypothesis testing cannot provide valid conclusions.",
                    "Predictive modelling recommendations should be interpreted cautiously."
                ],
                recommended_actions=[
                    "Collect additional observations.",
                    "Increase sample size.",
                    "Treat findings as exploratory.",
                    "Avoid drawing statistically significant conclusions."
                ]
            )
        elif 2 <= rows <= 4:
            return ReliabilityAssessment(
                level="VERY_LIMITED",
                confidence="low",
                severity="warning",
                can_infer=False,
                can_model=False,
                can_hypothesis_test=False,
                can_visualize=True,
                requires_caution_flag=True,
                explanation="The dataset contains very few observations (2-4 rows). Statistical reliability is very limited due to the extremely small sample size.",
                warnings=[
                    "Correlation analysis is unreliable.",
                    "Distribution analysis is not meaningful.",
                    "Hypothesis testing cannot provide valid conclusions.",
                    "Predictive modelling recommendations should be interpreted cautiously."
                ],
                recommended_actions=[
                    "Collect additional observations.",
                    "Increase sample size.",
                    "Treat findings as exploratory.",
                    "Avoid drawing statistically significant conclusions."
                ]
            )
        elif 5 <= rows <= 29:
            return ReliabilityAssessment(
                level="LIMITED",
                confidence="medium",
                severity="info",
                can_infer=True,
                can_model=True,
                can_hypothesis_test=True,
                can_visualize=True,
                requires_caution_flag=True,
                explanation="The dataset has limited statistical confidence due to a small sample size (5-29 rows).",
                warnings=[
                    "Statistical inference has limited power.",
                    "Distribution and correlation estimates should be interpreted with caution.",
                    "Sample size is below the recommended 30+ row threshold."
                ],
                recommended_actions=[
                    "Collect additional observations.",
                    "Treat findings as exploratory."
                ]
            )
        else:
            return ReliabilityAssessment(
                level="STANDARD",
                confidence="high",
                severity="info",
                can_infer=True,
                can_model=True,
                can_hypothesis_test=True,
                can_visualize=True,
                requires_caution_flag=False,
                explanation="The dataset contains a standard number of observations for statistical analysis.",
                warnings=[],
                recommended_actions=[]
            )
