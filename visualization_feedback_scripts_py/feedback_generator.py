import json

from pathlib import Path

from llm_client import call_openai


# Locate the prompts folder relative to this Python file.
BASE_DIR = Path(__file__).resolve().parent
FEEDBACK_PROMPT_PATH = (
    BASE_DIR / "prompts" / "Scaffolding Feedback.txt"
)


def load_feedback_prompt():
    """
    Load the Function 4 feedback instructions from
    prompts/Scaffolding Feedback.txt.
    """
    if not FEEDBACK_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Feedback prompt file not found: "
            f"{FEEDBACK_PROMPT_PATH}"
        )

    return FEEDBACK_PROMPT_PATH.read_text(
        encoding="utf-8"
    )


def count_words(text):
    """
    Count words in the generated feedback.
    """
    return len(text.split())


def validate_feedback(feedback_text):
    """
    Perform basic checks against the Function 4 feedback format.

    This function checks formatting only.
    It does not determine whether the feedback is pedagogically appropriate.
    """
    errors = []

    required_prefix = "📋 Feedback on our collaboration"

    if not feedback_text.startswith(required_prefix):
        errors.append(
            "Feedback does not start with the required prefix."
        )

    word_count = count_words(feedback_text)

    if word_count > 60:
        errors.append(
            f"Feedback exceeds the 60-word limit "
            f"({word_count} words)."
        )

    # Remove the required heading before counting sentences.
    body = feedback_text.replace(
        required_prefix, "", 1
    ).strip()

    # Basic sentence count based on common sentence-ending punctuation.
    sentence_count = sum(body.count(mark) for mark in [".", "!", "?", "。", "！", "？"])

    if not 2 <= sentence_count <= 4:
        errors.append(
            f"Feedback should contain 2–4 sentences; "
            f"detected {sentence_count}."
        )

    if not feedback_text.rstrip().endswith(("?", "？")):
        errors.append(
            "Feedback should end with an open question."
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "word_count": word_count,
        "sentence_count": sentence_count,
    }


def generate_feedback(
    conversation_history,
    pattern_result,
    interaction_codes=None,
    api_key=None,
    teacher_declined=False,
):
    """
    Generate Function 4 reflection feedback.

    Parameters
    ----------
    conversation_history : list
        Conversation history for the current design task.

    pattern_result : dict
        Result from the interaction pattern detection module.

    interaction_codes : dict or list, optional
        Interaction coding results, if available.

    api_key : str, optional
        OpenAI API key.

    teacher_declined : bool
        Whether the teacher declined to receive feedback.

    Returns
    -------
    dict
        Generated feedback and basic validation results.
    """

    # If the teacher declines feedback, do not call the model.
    if teacher_declined:
        return {
            "feedback": (
                "Understood. We can close our reflection here."
            ),
            "validation": {
                "is_valid": True,
                "errors": [],
                "word_count": None,
                "sentence_count": None,
            },
        }

    # Load the dedicated Function 4 feedback instructions.
    feedback_prompt = load_feedback_prompt()

    # Prepare the information for the feedback model.
    feedback_input = {
        "conversation_history": conversation_history,
        "interaction_codes": interaction_codes,
        "pattern_result": pattern_result,
    }

    user_input = json.dumps(
        feedback_input,
        ensure_ascii=False,
        indent=2,
    )

    # Generate feedback using the dedicated prompt.
    feedback_text = call_openai(
        system_prompt=feedback_prompt,
        user_input=user_input,
        api_key=api_key,
    )

    # Check the output format.
    validation_result = validate_feedback(
        feedback_text
    )

    return {
        "feedback": feedback_text,
        "validation": validation_result,
    }
