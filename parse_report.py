import sys

try:
    with open(r'd:\51-DEMO\docs\AI_Collaboration\Local_Agent\In_Progress\2026-01-26_AI_Trial_Game_Development\Report_API_Integration_Testing_Codex.md', 'rb') as f:
        content = f.read().decode('latin-1', errors='ignore')
    
    print("=" * 60)
    print("CODEX API INTEGRATION TEST REPORT SUMMARY")
    print("=" * 60)
    print()
    
    # Extract test results
    if 'chat_juror_wang' in content:
        print("✅ LLM Integration Tests: FOUND")
        # Find all chat test results
        import re
        chat_tests = re.findall(r'chat_juror_\w+.*?200.*?(\d+\.\d+)s', content)
        if chat_tests:
            print(f"   - Successfully completed {len(chat_tests)} chat interactions")
            print(f"   - Average response time: ~{sum(float(t) for t in chat_tests)/len(chat_tests):.1f}s")
    
    # Check for errors
    if '500' in content or 'Error' in content or 'error' in content:
        print("\n⚠️  Errors Found:")
        errors = re.findall(r'(error|Error|500).*', content, re.IGNORECASE)
        for err in errors[:5]:
            print(f"   - {err[:80]}")
    
    # Check success criteria
    if 'Success Criteria' in content or 'Met' in content:
        print("\n📊 Success Criteria:")
        criteria = re.findall(r'- .*?:\s*\*\*(Met|Not met)\*\*', content)
        for c in criteria[:10]:
            print(f"   {c}")
    
    # Check for key functionalities
    print("\n🔍 Key Test Areas:")
    test_areas = [
        ('Basic endpoints', 'health_check'),
        ('Juror listing', 'get_jurors'),
        ('Juror chat (Wang)', 'chat_juror_wang'),
        ('Juror chat (Liu)', 'chat_juror_liu'),
        ('Juror chat (Chen)', 'chat_juror_chen'),
        ('Voting', 'vote'),
    ]
    
    for name, pattern in test_areas:
        status = "✅ TESTED" if pattern in content else "❌ NOT FOUND"
        print(f"   {status}: {name}")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"Error reading report: {e}")
    sys.exit(1)
