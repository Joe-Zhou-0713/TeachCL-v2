from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent  # Directory containing prompts.py
PROMPT_DIR = BASE_DIR / "prompts"  # Prompt text directory


def load_prompt(file_name):
    prompt_path = PROMPT_DIR / file_name

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


CHATBOT_PROMPT = load_prompt("System_Prompt.txt")
CODING_PROMPT = load_prompt("Coding_Prompt.txt")
PATTERN_DETECTION_PROMPT = load_prompt("Pattern_Detection_Prompt.txt")
