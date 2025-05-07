#!/usr/bin/env python3
"""
Test script to verify GitHub rate limit handling
"""

import os
import sys
import time
import logging
import argparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_rate_limit')

# Load environment variables
load_dotenv()

def simulate_rate_limit_check(remaining=10):
    """
    Simulate GitHub API rate limit check with a specified number of remaining requests
    
    Args:
        remaining: Number of remaining requests to simulate
    """
    # Simulate rate limit data
    limit = 5000
    reset_time = time.time() + 3600  # 1 hour from now
    
    # Calculate time until reset in AM/PM format
    reset_datetime_ampm = time.strftime('%Y-%m-%d %I:%M:%S %p', time.localtime(reset_time))
    
    # Calculate time remaining until reset
    current_time = time.time()
    time_remaining_seconds = max(0, reset_time - current_time)
    hours, remainder = divmod(time_remaining_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_remaining_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    # Log rate limit information
    logger.info(f"GitHub API Rate Limit: {remaining}/{limit} requests remaining")
    logger.info(f"Rate limit resets at: {reset_datetime_ampm} (in {time_remaining_str})")
    
    # Define threshold for rate limit (at least 100 requests needed)
    threshold = 100
    
    # Check if we have enough requests remaining
    if remaining < threshold:
        message = f"\nGitHub API rate limit too low: {remaining}/{limit} requests remaining\n"
        message += f"Rate limit will reset at {reset_datetime_ampm} (in {time_remaining_str})\n"
        message += f"Please try again after {time_remaining_str} when the rate limit resets.\n"
        
        print(message)
        logger.error(f"GitHub API rate limit too low: {remaining}/{limit} requests remaining")
        logger.error(f"Rate limit will reset at {reset_datetime_ampm} (in {time_remaining_str})")
        
        # Exit with error code
        sys.exit(1)
    
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test GitHub rate limit handling")
    parser.add_argument("--remaining", "-r", type=int, default=10, help="Number of remaining requests to simulate")
    args = parser.parse_args()
    
    # Simulate rate limit check
    simulate_rate_limit_check(args.remaining)
    
    # If we get here, rate limit is sufficient
    print("\nRate limit is sufficient, proceeding with documentation generation...")
    print("(This is just a test, no actual documentation will be generated)")

if __name__ == "__main__":
    main()
