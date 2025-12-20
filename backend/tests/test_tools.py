"""
Test basic tool functionality.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools import calculate, get_available_tools


def test_calculate_tool():
    """Test the calculate tool with various expressions."""
    print("\n" + "="*70)
    print("Testing Calculator Tool")
    print("="*70)
    
    test_cases = [
        ("2 + 2", "4"),
        ("10 * 5", "50"),
        ("15 + 23", "38"),
        ("100 / 4", "25.0"),
        ("(5 + 3) * 2", "16"),
        ("2 ** 3", "8"),
    ]
    
    passed = 0
    failed = 0
    
    for expression, expected in test_cases:
        try:
            result = calculate(expression)
            # Check if result contains the expected value
            if expected in result or str(eval(expression)) in result:
                print(f"[OK] {expression} = {result}")
                passed += 1
            else:
                print(f"[FAIL] {expression} = {result} (expected: {expected})")
                failed += 1
        except Exception as e:
            print(f"[FAIL] {expression} raised error: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}\n")
    
    return failed == 0


def test_get_available_tools():
    """Test that tools are properly registered."""
    print("\n" + "="*70)
    print("Testing Tool Registration")
    print("="*70)
    
    tools = get_available_tools()
    
    if "calculate" in tools:
        print("[OK] Calculator tool is registered")
        print(f"[OK] Available tools: {list(tools.keys())}")
        return True
    else:
        print("[FAIL] Calculator tool is not registered")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TOOL TESTS")
    print("="*70)
    
    tool_test_passed = test_calculate_tool()
    registration_test_passed = test_get_available_tools()
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    if tool_test_passed and registration_test_passed:
        print("[PASSED] ALL TESTS PASSED")
    else:
        print("[FAILED] SOME TESTS FAILED")
    print("="*70 + "\n")

