import argparse
import os
import sys
from .core import run_flatty, is_root_directory

def main():
    parser = argparse.ArgumentParser(
        description="Flatty: Flatten your codebase into a single text file for LLMs."
    )
    parser.add_argument(
        '--pattern', 
        action='append', 
        default=[], 
        help='Pattern to filter files (filename or content). Can be used multiple times.'
    )
    parser.add_argument(
        '--condition', 
        choices=['AND', 'OR'], 
        default='OR', 
        help='Condition for multiple patterns (default: OR).'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force execution even in root directory (not recommended)'
    )
    
    args = parser.parse_args()
    
    # Check if running in root directory
    if is_root_directory() and not args.force:
        print("\n⚠️  WARNING: You are trying to run flatty in the root directory!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("Running flatty in the root directory (/) is NOT recommended because:", file=sys.stderr)
        print("  • It will scan your ENTIRE filesystem", file=sys.stderr)
        print("  • This could take a very long time", file=sys.stderr)
        print("  • The output file would be extremely large", file=sys.stderr)
        print("  • It may include sensitive system files", file=sys.stderr)
        print("\nIf you REALLY want to do this, use:", file=sys.stderr)
        print("  flatty --force", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)
    
    run_flatty(patterns=args.pattern, condition=args.condition)

if __name__ == "__main__":
    main()