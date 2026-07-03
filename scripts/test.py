import os
import sys
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import configs and helper from automation.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

try:
    from automation import models, problem_set, call_llm, get_prompt
except ImportError as e:
    print(f"Error importing automation script: {e}")
    sys.exit(1)

def main():
    print("=== LLM Automation Tester ===")
    
    test_dest = os.path.join(SCRIPT_DIR, "../test_results")

    # Find models with keys configured
    active_models = {name: key for name, key in models.items() if key}
    
    if not active_models:
        print("Error: No API keys found in your .env file.")
        print("Please configure at least one API key in scripts/.env to run this test.")
        return

    print("\nAvailable models configured in .env:")
    for idx, name in enumerate(active_models.keys(), 1):
        print(f"[{idx}] {name}")
        
    # Pick the first one as default
    selected_model = list(active_models.keys())[0]
    print(f"\nAutomatically selecting the first available model for test: {selected_model}")
    api_key = active_models[selected_model]
    
    # Use problem 1 for testing
    problem_id = 1
    if problem_id not in problem_set:
        print("Error: Problem 1 not found in problem_set.")
        return
        
    problem_text = problem_set[problem_id]
    prompt = get_prompt(problem_text)
    
    print(f"\nSending test prompt for Problem {problem_id} to {selected_model}...")
    
    try:
        response_text = call_llm(selected_model, api_key, prompt)
        print("\n--- Model Response ---")
        print(response_text)
        print("----------------------")
        
        # Save output
        target_dir = os.path.join(test_dest, selected_model, str(problem_id))
        os.makedirs(target_dir, exist_ok=True)
        result_file = os.path.join(target_dir, "test_result.txt")
        
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(response_text)
            
        print(f"\nSuccess! Test result saved to: {result_file}")
        
    except Exception as e:
        print(f"\nError running test: {e}")

if __name__ == "__main__":
    main()
