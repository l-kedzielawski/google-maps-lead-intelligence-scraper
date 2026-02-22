#!/usr/bin/env python3
"""
Test phone number parsing for different countries
Verifies that the country code parameter works correctly
"""

from src.utils import normalize_phone_number, extract_phone_numbers

# Test data: sample phone numbers from different countries
test_cases = [
    # Germany (DE)
    {
        'country': 'DE',
        'raw_numbers': ['030 12345678', '0211 987654', '+49 30 12345678', '(030) 123-456'],
        'expected_prefix': '+49'
    },
    # Italy (IT)
    {
        'country': 'IT',
        'raw_numbers': ['06 12345678', '02 87654321', '+39 06 12345678', '(02) 8765-4321'],
        'expected_prefix': '+39'
    },
    # Spain (ES)
    {
        'country': 'ES',
        'raw_numbers': ['91 1234567', '93 7654321', '+34 91 1234567', '(91) 123-4567'],
        'expected_prefix': '+34'
    },
    # Netherlands (NL)
    {
        'country': 'NL',
        'raw_numbers': ['020 1234567', '010 7654321', '+31 20 1234567', '(020) 123-4567'],
        'expected_prefix': '+31'
    },
    # Portugal (PT)
    {
        'country': 'PT',
        'raw_numbers': ['21 1234567', '22 7654321', '+351 21 1234567', '(21) 123-4567'],
        'expected_prefix': '+351'
    },
    # Belgium (BE)
    {
        'country': 'BE',
        'raw_numbers': ['2 123 45 67', '3 765 43 21', '+32 2 123 45 67', '(02) 123-4567'],
        'expected_prefix': '+32'
    },
    # Switzerland (CH)
    {
        'country': 'CH',
        'raw_numbers': ['44 123 45 67', '22 765 43 21', '+41 44 123 45 67', '(044) 123-4567'],
        'expected_prefix': '+41'
    },
    # Austria (AT)
    {
        'country': 'AT',
        'raw_numbers': ['1 1234567', '316 876543', '+43 1 1234567', '(01) 123-4567'],
        'expected_prefix': '+43'
    },
]

print("=" * 80)
print("PHONE NUMBER PARSING TEST")
print("=" * 80)
print()

total_tests = 0
passed_tests = 0
failed_tests = 0

for test_case in test_cases:
    country = test_case['country']
    expected_prefix = test_case['expected_prefix']
    
    print(f"Testing {country} ({expected_prefix}):")
    print("-" * 80)
    
    for raw_number in test_case['raw_numbers']:
        total_tests += 1
        normalized = normalize_phone_number(raw_number, country)
        
        if normalized:
            if normalized.startswith(expected_prefix):
                status = "✓ PASS"
                passed_tests += 1
            else:
                status = f"✗ FAIL (wrong prefix: expected {expected_prefix}, got {normalized[:len(expected_prefix)]})"
                failed_tests += 1
        else:
            status = "✗ FAIL (returned None)"
            failed_tests += 1
        
        print(f"  {raw_number:20s} → {normalized or 'None':20s} {status}")
    
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total tests: {total_tests}")
print(f"Passed: {passed_tests} ({round(passed_tests/total_tests*100, 1)}%)")
print(f"Failed: {failed_tests}")
print()

if failed_tests == 0:
    print("✓ ALL TESTS PASSED! Phone parsing is working correctly for all countries.")
    exit(0)
else:
    print(f"✗ {failed_tests} tests failed. Please review the output above.")
    exit(1)
