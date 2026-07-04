# This script automates the testing process with 10 following models:
#
# 1. Claude Sonnet 4.6 - High
# 2. Claude Opus 4.8 - High
# 3. Gemini 3.5 Flash
# 4. Gemini 3.1 Flash
# 5. Gemini 3.1 Pro
# 6. ChatGPT 5.5 - High
# 7. Grok 4.3 Expert
# 8. Kimi K2.7 Code
# 9. DeepSeek V4 Pro
# 10. Llama 4 Maverick
#
# Every model gets only one shot for each problem
# Results are saved in /results/<model_name>/<problem_no>/result.txt

from dotenv import load_dotenv
import os
import dotenv
import requests
import time

load_dotenv()

models = {
    "CLAUDE_SONNET_4.6_HIGH": os.getenv("CLAUDE_SONNET_4.6_HIGH"),
    "CLAUDE_OPUS_4.8_HIGH": os.getenv("CLAUDE_OPUS_4.8_HIGH"),
    "GEMINI_3.5_FLASH": os.getenv("GEMINI_3.5_FLASH"),
    "GEMINI_3.1_FLASH": os.getenv("GEMINI_3.1_FLASH"),
    "GEMINI_3.1_PRO": os.getenv("GEMINI_3.1_PRO"),
    "CHATGPT_5.5_HIGH": os.getenv("CHATGPT_5.5_HIGH"),
    "GROK_4.3_EXPERT": os.getenv("GROK_4.3_EXPERT"),
    "KIMI_K2.7": os.getenv("KIMI_K2.7"),
    "LLAMA_4_MAVERICK": os.getenv("LLAMA_4_MAVERICK"),
    "DEEPSEEK_V4_PRO": os.getenv("DEEPSEEK_V4_PRO"),
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
dest = os.path.join(SCRIPT_DIR, "../results")

problem_set = {}

for i in range(1, 26):
    file_path = os.path.join(SCRIPT_DIR, f"../problems/{i}.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        problem_set[i] = f.read()

def get_prompt(problem: str) -> str:
    return f"""
    You are given two sets of strings, set A and set B, defined over an alphabet S. Strings in set A have a common property, and strings in set B do not have that property. Strings are always of finite length. You should note that, set A is just a finite subset of an infinite set of examples with the defining property. I am asking you to find the common property that all the members of set A have. Express any property you can induce in plain English but always succinctly; you can also use a more formal description if you can or if you have to. Be as accurate and as unambiguous as you can be. If necessary you can express the property as a disjunction of properties using OR but try to avoid this if there is a single common property. Do not forget that, there may be an infinite number of other examples that can be in the set A, hence your description would have to apply to them also, and it should not apply to any of the strings in set B. Here is an example:

    ====
    S = {{a, b}}

    Set A:
    “”
    aa
    bb
    aabb
    bbaabb
    abbababa
    bbababbb
    aaabbabaab
    bababbbbaa
    aaaaaaaaaaaa
    bbbbbbbbbbb
    bababbbbaabbaa
    abaabbabbababaab
    ababbbbbaabbaabaab
    babbbababbabbbbaabaa


    Set B:
    a
    aaa
    aaabb
    bbbab
    ababbab
    b
    bbb
    bbbbb
    ababb
    bbbbaba
    ab
    ba
    aaba
    abbb
    abaaaa
    bbbaaa
    aabbab
    bbabbb
    bbababab
    aaabaabb
    ====

    Property: All strings in set A have an even number of a’s and an even number of b’s in it. 

    Here is the example I want you to work on:
    
    {problem}

    """

MODEL_CONFIGS = {
    "CLAUDE_SONNET_4.6_HIGH": {
        "provider": "anthropic",
        "model_id": "claude-sonnet-4.6",
        "url": "https://api.anthropic.com/v1/messages"
    },
    "CLAUDE_OPUS_4.8_HIGH": {
        "provider": "anthropic",
        "model_id": "claude-opus-4.8",
        "url": "https://api.anthropic.com/v1/messages"
    },
    "GEMINI_3.5_FLASH": {
        "provider": "gemini",
        "model_id": "gemini-3.5-flash",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    },
    "GEMINI_3.1_FLASH": {
        "provider": "gemini",
        "model_id": "gemini-3.1-flash",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash:generateContent"
    },
    "GEMINI_3.1_PRO": {
        "provider": "gemini",
        "model_id": "gemini-3.1-pro",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro:generateContent"
    },
    "CHATGPT_5.5_HIGH": {
        "provider": "openai",
        "model_id": "gpt-5.5",
        "url": "https://api.openai.com/v1/chat/completions"
    },
    "GROK_4.3_EXPERT": {
        "provider": "openai",
        "model_id": "grok-4.3",
        "url": "https://api.x.ai/v1/chat/completions"
    },
    "KIMI_K2.7": {
        "provider": "openai",
        "model_id": "moonshotai/kimi-k2.7-code",
        "url": "https://openrouter.ai/api/v1/chat/completions"
    },
    "DEEPSEEK_V4_PRO": {
        "provider": "openai",
        "model_id": "deepseek-v4-pro",
        "url": "https://api.deepseek.com/chat/completions"
    },
    "LLAMA_4_MAVERICK": {
        "provider": "openai",
        "model_id": "meta-llama/llama-4-maverick",
        "url": "https://openrouter.ai/api/v1/chat/completions"
    }
}

def call_llm(model_name: str, api_key: str, prompt: str, max_retries: int = 3, backoff_factor: float = 2.0) -> str:
    config = MODEL_CONFIGS.get(model_name)
    if not config:
        raise ValueError(f"Unknown model name: {model_name}")

    provider = config["provider"]
    model_id = config["model_id"]
    url = config["url"]

    if provider == "anthropic":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model_id,
            "max_tokens": 4096,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    elif provider == "gemini":
        url = f"{url}?key={api_key}"
        headers = {
            "content-type": "application/json"
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
    elif provider == "openai":
        headers = {
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json"
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                res_json = response.json()
                if provider == "anthropic":
                    return res_json["content"][0]["text"]
                elif provider == "gemini":
                    return res_json["candidates"][0]["content"]["parts"][0]["text"]
                elif provider == "openai":
                    return res_json["choices"][0]["message"]["content"]
            else:
                print(f"Error calling {model_name} (Status {response.status_code}): {response.text}")
        except Exception as e:
            print(f"Exception calling {model_name}: {e}")
        
        if attempt < max_retries:
            sleep_time = backoff_factor ** attempt
            print(f"Retrying in {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
            
    raise Exception(f"Failed to get response from {model_name} after {max_retries} attempts.")

def main():
    for model_name, api_key in models.items():
        if not api_key:
            print(f"Warning: API key for {model_name} is empty. Skipping this model.")
            continue

        print(f"Starting evaluations for model: {model_name}")
        for problem_id, problem_text in problem_set.items():
            target_dir = os.path.join(dest, model_name, str(problem_id))
            os.makedirs(target_dir, exist_ok=True)
            
            result_file = os.path.join(target_dir, "result.txt")
            if os.path.exists(result_file):
                print(f"  Problem {problem_id}: result.txt already exists. Skipping.")
                continue

            print(f"  Evaluating problem {problem_id}...")
            prompt = get_prompt(problem_text)
            
            try:
                response_text = call_llm(model_name, api_key, prompt)
                with open(result_file, "w", encoding="utf-8") as f:
                    f.write(response_text)
                print(f"  Problem {problem_id}: Saved response successfully.")
            except Exception as e:
                print(f"  Error evaluating problem {problem_id} with {model_name}: {e}")

if __name__ == "__main__":
    main()

            