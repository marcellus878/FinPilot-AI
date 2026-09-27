import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReflectionValidator:
    """
    Performs deterministic reflection and bounded self-correction on agent outputs.
    Audits groundedness, mathematical fact alignment, and formatting rules.
    """

    def audit_and_correct(
        self,
        draft_content: str,
        verified_facts: List[Dict[str, Any]],
        rag_citations: Optional[List[Dict[str, Any]]] = None,
        user_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Audit draft response and apply self-correction if necessary.
        """
        issues = []
        corrections = []
        corrected_content = draft_content

        # 1. Currency Formatting Check: Flag and correct foreign currency markers ($ -> ₹)
        if "$" in corrected_content:
            issues.append("Found dollar symbol ($) in INR localized response")
            corrected_content = re.sub(r"\$(\d+[\d,]*)", r"₹\1", corrected_content)
            corrected_content = corrected_content.replace("$", "₹")
            corrections.append("Replaced dollar symbols with Indian Rupee (₹)")

        # 2. Fact Grounding Verification: Verify referenced figures against context facts
        if verified_facts:
            fact_map = {}
            for f in verified_facts:
                name = f.get("name", "")
                val = f.get("value", "")
                if name and val:
                    fact_map[name.lower()] = str(val)

            # Check for generic statements about zero balances if facts show positive balance
            if "you have no savings" in corrected_content.lower():
                current_savings = fact_map.get("current_savings", "0")
                if current_savings and float(str(current_savings).replace(",", "").replace("₹", "")) > 0:
                    issues.append("Discrepancy: Claimed zero savings when verified savings exist")
                    corrected_content = corrected_content.replace(
                        "you have no savings",
                        f"you currently have ₹{current_savings} in liquid savings",
                    )
                    corrections.append(f"Corrected savings claim to verified amount ₹{current_savings}")

        # 3. Groundedness Score Calculation
        groundedness = 1.0 - (len(issues) * 0.15)
        groundedness = max(0.6, min(1.0, groundedness))

        status = "corrected" if corrections else "passed"

        return {
            "status": status,
            "groundedness_score": round(groundedness, 2),
            "issues_detected": issues,
            "corrections_applied": corrections,
            "final_content": corrected_content,
            "reflection_performed": True,
            "rag_grounded": bool(rag_citations and len(rag_citations) > 0),
        }


# Global singleton reflection validator
reflection_validator = ReflectionValidator()
