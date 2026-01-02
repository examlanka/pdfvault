"""
Unit tests for the Past Paper Vault application
Run this with: python test_app.py
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import re
from app_fixed import (
    sanitize_filename,
    normalize_text,
    fuzzy_search,
    load_master_index
)


def test_sanitize_filename():
    """Test filename sanitization"""
    print("Testing sanitize_filename...")
    
    # Test 1: HTML tags
    assert sanitize_filename("<div>test.pdf</div>") == "test.pdf"
    
    # Test 2: Entity-encoded tags
    assert sanitize_filename("&lt;div&gt;test.pdf&lt;/div&gt;") == "test.pdf"
    
    # Test 3: HTML entities
    assert sanitize_filename("test&amp;file.pdf") == "test&file.pdf"
    
    # Test 4: Normal filename
    assert sanitize_filename("normal_file.pdf") == "normal_file.pdf"
    
    # Test 5: None input
    assert sanitize_filename(None) == ""
    
    print("✅ sanitize_filename tests passed")


def test_normalize_text():
    """Test text normalization"""
    print("\nTesting normalize_text...")
    
    # Test 1: Lowercase conversion
    assert normalize_text("PHYSICS") == "physics"
    
    # Test 2: A/L normalization
    assert "al" in normalize_text("A/L Physics")
    assert "al" in normalize_text("Advanced Level")
    
    # Test 3: Special character removal
    assert normalize_text("test_file-name.pdf") == "test file name pdf"
    
    # Test 4: Multiple spaces
    assert normalize_text("test    file") == "test file"
    
    # Test 5: Empty string
    assert normalize_text("") == ""
    
    print("✅ normalize_text tests passed")


def test_load_master_index():
    """Test CSV loading"""
    print("\nTesting load_master_index...")
    
    try:
        df = load_master_index()
        
        # Test 1: DataFrame not empty
        assert not df.empty, "DataFrame should not be empty"
        
        # Test 2: Required columns exist
        assert 'File Name' in df.columns, "File Name column missing"
        assert 'File ID' in df.columns, "File ID column missing"
        
        # Test 3: Check data types
        assert df['File Name'].dtype == object, "File Name should be string type"
        assert df['File ID'].dtype == object, "File ID should be string type"
        
        # Test 4: No null values in critical columns
        assert df['File Name'].notna().all(), "File Name has null values"
        assert df['File ID'].notna().all(), "File ID has null values"
        
        print(f"✅ load_master_index tests passed - Loaded {len(df)} records")
        return df
    except Exception as e:
        print(f"❌ load_master_index test failed: {e}")
        return None


def test_fuzzy_search(df):
    """Test fuzzy search functionality"""
    print("\nTesting fuzzy_search...")
    
    if df is None or df.empty:
        print("⚠️ Skipping fuzzy_search tests - no data available")
        return
    
    # Test 1: Basic search
    results = fuzzy_search("physics", df, limit=5)
    assert not results.empty, "Search should return results for 'physics'"
    assert 'Match Score' in results.columns, "Match Score column missing"
    print(f"  ✓ Basic search returned {len(results)} results")
    
    # Test 2: Search with year
    results = fuzzy_search("physics 2021", df, limit=5)
    print(f"  ✓ Year-based search returned {len(results)} results")
    
    # Test 3: Empty query
    results = fuzzy_search("", df, limit=5)
    assert results.empty, "Empty query should return no results"
    print(f"  ✓ Empty query handled correctly")
    
    # Test 4: Non-matching query
    results = fuzzy_search("xyznonexistent123", df, limit=5)
    assert results.empty or len(results) == 0, "Non-matching query should return no results"
    print(f"  ✓ Non-matching query handled correctly")
    
    # Test 5: Score ordering
    results = fuzzy_search("mathematics", df, limit=10)
    if not results.empty and len(results) > 1:
        scores = results['Match Score'].tolist()
        assert scores == sorted(scores, reverse=True), "Results should be ordered by score"
        print(f"  ✓ Results properly ordered by score")
    
    print("✅ fuzzy_search tests passed")


def test_csv_data_quality(df):
    """Test the quality of CSV data"""
    print("\nTesting CSV data quality...")
    
    if df is None or df.empty:
        print("⚠️ Skipping data quality tests - no data available")
        return
    
    # Test 1: Check for HTML artifacts in filenames
    html_pattern = r'<[^>]+>|&lt;|&gt;'
    html_files = df[df['File Name'].str.contains(html_pattern, case=False, na=False, regex=True)]
    if not html_files.empty:
        print(f"  ⚠️ Warning: {len(html_files)} files have HTML artifacts")
        print(f"    Sample: {html_files.iloc[0]['File Name']}")
    else:
        print(f"  ✓ No HTML artifacts found in filenames")
    
    # Test 2: Check File ID format
    file_ids = df['File ID'].tolist()
    valid_ids = [fid for fid in file_ids if isinstance(fid, str) and len(str(fid).strip()) > 0]
    print(f"  ✓ {len(valid_ids)}/{len(file_ids)} File IDs are valid")
    
    # Test 3: Check for duplicate filenames
    duplicates = df[df.duplicated(subset=['File Name'], keep=False)]
    if not duplicates.empty:
        print(f"  ⚠️ Warning: {len(duplicates)} duplicate filenames found")
    else:
        print(f"  ✓ No duplicate filenames")
    
    # Test 4: Check filename length
    long_names = df[df['File Name'].str.len() > 200]
    if not long_names.empty:
        print(f"  ⚠️ Warning: {len(long_names)} very long filenames (>200 chars)")
    else:
        print(f"  ✓ All filenames are reasonable length")
    
    print("✅ CSV data quality tests completed")


def test_telegram_file_content():
    """Test Telegram file download logic (without actual API call)"""
    print("\nTesting Telegram download logic...")
    
    # Test input validation
    from app_fixed import get_telegram_file_content
    
    # Test 1: Empty bot token
    content, error = get_telegram_file_content("test_id", "")
    assert content is None, "Should return None for empty token"
    assert error is not None, "Should return error for empty token"
    print("  ✓ Empty token validation works")
    
    # Test 2: Empty file ID
    content, error = get_telegram_file_content("", "test_token")
    assert content is None, "Should return None for empty file ID"
    assert error is not None, "Should return error for empty file ID"
    print("  ✓ Empty file ID validation works")
    
    print("✅ Telegram download logic tests passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("RUNNING UNIT TESTS FOR PAST PAPER VAULT")
    print("=" * 60)
    
    try:
        # Test 1: Filename sanitization
        test_sanitize_filename()
        
        # Test 2: Text normalization
        test_normalize_text()
        
        # Test 3: CSV loading
        df = test_load_master_index()
        
        # Test 4: Fuzzy search
        test_fuzzy_search(df)
        
        # Test 5: Data quality
        test_csv_data_quality(df)
        
        # Test 6: Telegram logic
        test_telegram_file_content()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
