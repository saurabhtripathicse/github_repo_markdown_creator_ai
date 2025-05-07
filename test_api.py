#!/usr/bin/env python3
"""
Simple test script for the GitHub Documentation Generator API
"""

import requests
import json
import sys

def main():
    """Test the API directly with Python requests"""
    
    print("Testing GitHub Documentation Generator API...")
    
    # Test the health endpoint
    try:
        health_response = requests.get("http://localhost:8000/health")
        print(f"Health check status: {health_response.status_code}")
        print(f"Health check response: {health_response.json()}")
        print()
    except Exception as e:
        print(f"Error checking health: {str(e)}")
        return 1
    
    # Test the generate-docs endpoint
    try:
        payload = {
            "repo_url": "https://github.com/psf/requests",
            "diagram": False
        }
        
        print(f"Sending request to generate docs for {payload['repo_url']}...")
        docs_response = requests.post(
            "http://localhost:8000/generate-docs",
            json=payload
        )
        
        print(f"Generate docs status: {docs_response.status_code}")
        print(f"Generate docs response: {docs_response.text}")
        
        if docs_response.status_code == 200:
            response_data = docs_response.json()
            if response_data.get("ok"):
                print("\nDocumentation generated successfully!")
                print("Generated files:")
                for file_path in response_data.get("files", []):
                    print(f"- {file_path}")
            else:
                print("\nError in response:", response_data)
        else:
            print("\nError status code:", docs_response.status_code)
            
    except Exception as e:
        print(f"Error generating docs: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
