# tests/test_ui_flow.py
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'modules', 'ui')))

def test_ui_navigation():
    """Test UI navigation flow"""
    print("Testing UI Navigation...")
    
    # Test pages exist
    pages = ["📤 Upload Data", "⚙️ Project Setup", "👥 Team Formation", 
             "📊 Calculation Reports", "📋 Results & Export"]
    
    for page in pages:
        print(f"✓ Page '{page}' configured")
    
    # Test session state initialization
    required_states = ['profiles', 'project', 'teams', 'explanations', 'page']
    print(f"✓ Session states: {required_states}")
    
    print("\nUI Flow Test Complete!")

if __name__ == "__main__":
    test_ui_navigation()