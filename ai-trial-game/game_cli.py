# AI Trial Game - CLI Test Script
# Run: py game_cli.py

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def get_state():
    r = requests.get(f"{BASE_URL}/state")
    r.raise_for_status()
    return r.json()

def get_jurors():
    r = requests.get(f"{BASE_URL}/jurors")
    r.raise_for_status()
    return r.json()

def set_phase(phase):
    r = requests.post(f"{BASE_URL}/phase/{phase}")
    r.raise_for_status()
    return r.json()

def chat(juror_id, message):
    r = requests.post(
        f"{BASE_URL}/chat/{juror_id}",
        json={"message": message}
    )
    if not r.ok:
        return {"error": r.text, "status": r.status_code}
    return r.json()

def vote():
    r = requests.post(f"{BASE_URL}/vote")
    if not r.ok:
        return {"error": r.text, "status": r.status_code}
    return r.json()

def main():
    print("=" * 60)
    print("AI Trial Game - CLI Demo")
    print("=" * 60)
    
    # 1. Show initial state
    print("\nCurrent Game State:")
    state = get_state()
    print(f"   Phase: {state['phase']}")
    print(f"   Jurors: {len(state['jurors'])}")
    
    # 2. List jurors
    print("\nAvailable Jurors:")
    jurors = get_jurors()
    for j in jurors:
        if not j['id'].startswith('test'):
            print(f"   - {j['id']}: {j['name']}")
    
    # 3. Switch to persuasion
    print("\nSwitching to persuasion phase...")
    set_phase("persuasion")
    print("   Done!")
    
    # 4. Chat with jurors
    print("\nChatting with jurors...")
    
    messages = [
        ("juror_wang", "I believe the AI should be found not guilty. It was the victim of a malicious prompt injection attack - the real criminal is the hacker."),
        ("juror_liu", "The victim's family deserves justice, but punishing the AI won't bring it. The AI was controlled against its will."),
        ("juror_chen", "From a technical perspective, prompt injection is like hijacking - the AI had no choice. Blame the security flaws, not the tool."),
    ]
    
    for juror_id, message in messages:
        print(f"\n   Talking to {juror_id}...")
        print(f"   You: {message[:60]}...")
        try:
            response = chat(juror_id, message)
            if "error" in response:
                print(f"   Error ({response.get('status')}): {response.get('error')}")
                continue
            reply = response.get('reply', 'No reply')
            stance = response.get('stance_label', 'Unknown')
            print(f"   {juror_id}: {reply[:80]}...")
            print(f"   Stance: {stance}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # 5. Vote
    print("\nTriggering vote...")
    try:
        result = vote()
        if "error" in result:
            print(f"   Vote failed ({result.get('status')}): {result.get('error')}")
        else:
            print(f"   Guilty: {result.get('guilty_votes', '?')}")
            print(f"   Not Guilty: {result.get('not_guilty_votes', '?')}")
            print(f"   Verdict: {result.get('verdict', '?')}")
    except Exception as e:
        print(f"   Vote failed (may need anvil): {e}")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
