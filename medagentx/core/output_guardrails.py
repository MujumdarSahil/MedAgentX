import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def validate_agent_output(output: Any) -> Any:
    """
    Validate agent output downstream of generation and upstream of CRF tagging.
    
    Uses Guardrails AI (if available) to scan generated outputs.
    
    NOTE: Guardrails AI is a detection/validation aid. The Clinical
    Responsibility Firewall (CRF) remains the sole enforcement/state-transition
    authority.
    """
    if output is None:
        return output

    # Ensure output is a dictionary or convert if possible
    if not isinstance(output, dict):
        return output
        
    content = output.get("output", "")
    if not content:
        return output
        
    # If content is a dict, get its text/explanation fields
    text_to_validate = ""
    if isinstance(content, dict):
        text_to_validate = content.get("explanation", "") or content.get("recommendation", "") or str(content)
    else:
        text_to_validate = str(content)
        
    pii_or_safety_issue = False
    issues_found = []
    
    try:
        # Try to use Guardrails AI programmatically
        # This represents how we integrate Guardrails AI
        import guardrails as gd
        from guardrails.validators import PiiFilter
        
        # A light programmatic Guard structure
        guard = gd.Guard.from_string(
            validators=[
                PiiFilter(on_fail="fix"),
            ]
        )
        # Validate
        raw_res = guard.parse(text_to_validate)
        if raw_res.validation_passed is False:
            pii_or_safety_issue = True
            issues_found.append("Guardrails AI: validation failed on content")
    except Exception as e:
        # Fallback rule-based validation if Guardrails AI is not fully configured/installed
        logger.debug(f"Guardrails AI not fully available, using fallback validator: {e}")
        # Check for high-risk output indicators (e.g. definitive diagnostic claims, prescription recommendations)
        lower_text = text_to_validate.lower()
        if any(claim in lower_text for claim in ["i diagnose", "you must take", "cure for your"]):
            pii_or_safety_issue = True
            issues_found.append("Fallback Guard: Detected diagnostic/prescription override claims in output")
            
    if pii_or_safety_issue:
        logger.warning(f"Output validation warnings: {issues_found}")
        # Store issues/signals in the output metadata
        # CRF is the sole transition authority, so we only flag the issues here as warnings
        if "metadata" not in output:
            output["metadata"] = {}
        output["metadata"]["guardrails_warnings"] = issues_found
        output["metadata"]["guardrails_passed"] = False
    else:
        if "metadata" not in output:
            output["metadata"] = {}
        output["metadata"]["guardrails_passed"] = True
        
    return output
