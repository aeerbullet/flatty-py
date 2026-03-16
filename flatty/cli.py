import argparse
from .core import run_flatty

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
    
    args = parser.parse_args()
    
    run_flatty(patterns=args.pattern, condition=args.condition)

if __name__ == "__main__":
    main()
