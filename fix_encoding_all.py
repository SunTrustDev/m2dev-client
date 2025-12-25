#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix encoding issues in files (EUC-KR to UTF-8 conversion)
Finds files with corrupted Korean characters and converts them to UTF-8
"""

import os
import sys
import codecs
from pathlib import Path

# Korean character ranges
KOREAN_RANGES = [
    ('\uAC00', '\uD7A3'),  # Hangul Syllables
    ('\u1100', '\u11FF'),  # Hangul Jamo
    ('\u3130', '\u318F'),  # Hangul Compatibility Jamo
]

def is_korean_char(c):
    """Check if character is Korean"""
    for start, end in KOREAN_RANGES:
        if start <= c <= end:
            return True
    return False

def has_corrupted_korean(content):
    """Check if content has corrupted Korean characters (mojibake)"""
    # Common mojibake patterns for Korean - check for sequences that look corrupted
    # These are typical when EUC-KR is read as UTF-8
    corrupted_indicators = [
        '\u01ae', '\u01b0', '\u01b1',  # Common corrupted patterns
    ]
    # Check for sequences that shouldn't appear in normal text
    for indicator in corrupted_indicators:
        if indicator in content:
            return True
    # Check for isolated high bytes that suggest mojibake
    return False

def has_korean_characters(content):
    """Check if content has Korean characters"""
    return any(is_korean_char(c) for c in content)

def try_fix_encoding(file_path):
    """Try to fix encoding of a file"""
    try:
        # Read as binary
        with open(file_path, 'rb') as f:
            raw_bytes = f.read()
        
        # Try different encodings
        encodings = ['euc-kr', 'cp949', 'utf-8']
        
        best_encoding = None
        best_korean_count = 0
        best_decoded = None
        
        for enc in encodings:
            try:
                decoded = raw_bytes.decode(enc, errors='ignore')
                korean_count = sum(1 for c in decoded if is_korean_char(c))
                
                # Check if it has corrupted patterns when read as UTF-8
                if enc == 'utf-8':
                    if has_corrupted_korean(decoded):
                        continue  # Skip UTF-8 if it has corrupted patterns
                
                if korean_count > best_korean_count:
                    best_korean_count = korean_count
                    best_encoding = enc
                    best_decoded = decoded
            except Exception:
                continue
        
        # If we found Korean characters with EUC-KR/CP949, convert to UTF-8
        if best_encoding and best_encoding in ['euc-kr', 'cp949'] and best_korean_count > 0:
            # Save as UTF-8
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(best_decoded)
            return True, best_encoding, best_korean_count
        
        # If UTF-8 already has corrupted patterns, try to fix from EUC-KR
        if best_encoding == 'utf-8' and has_corrupted_korean(best_decoded):
            for enc in ['euc-kr', 'cp949']:
                try:
                    decoded = raw_bytes.decode(enc, errors='ignore')
                    korean_count = sum(1 for c in decoded if is_korean_char(c))
                    if korean_count > 0:
                        with open(file_path, 'w', encoding='utf-8', newline='') as f:
                            f.write(decoded)
                        return True, enc, korean_count
                except Exception:
                    continue
        
        return False, None, 0
        
    except Exception as e:
        return False, f"ERROR: {str(e)}", 0

def find_files_to_fix(root_dir, extensions=None):
    """Find all files that might need encoding fixes"""
    if extensions is None:
        extensions = ['.py', '.txt', '.cpp', '.h', '.c', '.hpp']
    
    files_to_check = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                files_to_check.append(file_path)
    
    return files_to_check

def main():
    root_dir = os.getcwd()
    
    print("=" * 70)
    print("Encoding Fix Script - EUC-KR to UTF-8 Converter")
    print("=" * 70)
    print(f"Scanning directory: {root_dir}\n")
    
    # Find all files
    files = find_files_to_fix(root_dir)
    print(f"Found {len(files)} files to check\n")
    
    fixed_files = []
    skipped_files = []
    error_files = []
    
    for file_path in files:
        rel_path = os.path.relpath(file_path, root_dir)
        
        # Check if file needs fixing
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Skip if no Korean characters and no corruption
            if not has_korean_characters(content) and not has_corrupted_korean(content):
                continue
        except Exception:
            pass
        
        # Try to fix
        fixed, encoding, korean_count = try_fix_encoding(file_path)
        
        if fixed:
            if isinstance(encoding, str) and encoding.startswith('ERROR'):
                error_files.append((rel_path, encoding))
            else:
                fixed_files.append((rel_path, encoding, korean_count))
                # Use ASCII-safe output
                try:
                    print(f"[FIXED] {rel_path} (from {encoding}, {korean_count} Korean chars)")
                except UnicodeEncodeError:
                    print(f"[FIXED] {rel_path} (from {encoding}, {korean_count} Korean chars)")
        else:
            skipped_files.append(rel_path)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files fixed: {len(fixed_files)}")
    print(f"Files skipped: {len(skipped_files)}")
    print(f"Files with errors: {len(error_files)}")
    
    if fixed_files:
        print("\nFixed files:")
        for rel_path, encoding, korean_count in fixed_files:
            print(f"  - {rel_path} ({encoding}, {korean_count} Korean chars)")
    
    if error_files:
        print("\nFiles with errors:")
        for rel_path, error in error_files:
            print(f"  - {rel_path}: {error}")
    
    print("\nDone!")

if __name__ == '__main__':
    main()
