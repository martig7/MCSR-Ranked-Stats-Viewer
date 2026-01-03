"""Test script to reproduce the NoneType has no attribute get error"""

import json
from match import Match

# Test different scenarios that could cause the error
def test_match_creation():
    print("Testing Match creation with potential None values...")
    
    # Test 1: Basic match data
    try:
        test_data = {
            'id': 123, 
            'date': 1234567890, 
            'category': 'Any%', 
            'forfeited': False, 
            'season': 6
        }
        match = Match(test_data, 'testuser')
        print("OK: Basic match creation successful")
    except Exception as e:
        print(f"ERROR: Basic match creation failed: {e}")
    
    # Test 2: Match with None seed
    try:
        test_data_none_seed = {
            'id': 124, 
            'date': 1234567890, 
            'category': 'Any%', 
            'forfeited': False, 
            'season': 6, 
            'seed': None
        }
        match2 = Match(test_data_none_seed, 'testuser')
        print("OK: Match creation with None seed successful")
    except Exception as e:
        print(f"ERROR: Match creation with None seed failed: {e}")
    
    # Test 3: Match with missing result
    try:
        test_data_no_result = {
            'id': 125, 
            'date': 1234567890, 
            'category': 'Any%', 
            'forfeited': False, 
            'season': 6
        }
        match3 = Match(test_data_no_result, 'testuser')
        print("OK: Match creation without result successful")
    except Exception as e:
        print(f"ERROR: Match creation without result failed: {e}")
    
    # Test 4: Match with None result
    try:
        test_data_none_result = {
            'id': 126, 
            'date': 1234567890, 
            'category': 'Any%', 
            'forfeited': False, 
            'season': 6,
            'result': None
        }
        match4 = Match(test_data_none_result, 'testuser')
        print("OK: Match creation with None result successful")
    except Exception as e:
        print(f"ERROR: Match creation with None result failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Match with None players
    try:
        test_data_none_players = {
            'id': 127, 
            'date': 1234567890, 
            'category': 'Any%', 
            'forfeited': False, 
            'season': 6,
            'players': None
        }
        match5 = Match(test_data_none_players, 'testuser')
        print("OK: Match creation with None players successful")
    except Exception as e:
        print(f"ERROR: Match creation with None players failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_match_creation()