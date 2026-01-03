"""
Debug script to investigate detailed match data from MCSR Ranked API /matches/{id} endpoint.
This should show if ELO change data is available in the detailed match responses.
"""

import json
import requests
from mcsr_stats import MCSRAnalyzer


def debug_detailed_match_data(username: str, max_matches: int = 5):
    """
    Debug detailed match data to look for ELO change information
    """
    print(f"=== Debugging Detailed Match Data for {username} ===\n")
    
    analyzer = MCSRAnalyzer(username)
    
    # Fetch recent matches
    analyzer.fetch_all_matches(use_cache=True, max_matches=max_matches)
    
    if not analyzer.matches:
        print("No matches found")
        return
    
    print(f"Found {len(analyzer.matches)} matches\n")
    
    # Check detailed data for first few matches
    base_url = "https://api.mcsrranked.com/"
    
    for i, match in enumerate(analyzer.matches[:max_matches]):
        print(f"=== MATCH {i+1}: ID {match.id} ===")
        print(f"Date: {match.date_str()}")
        print(f"Basic match data ELO: {match.get_user_elo_rate()}")
        
        # Fetch detailed match data
        url = f"{base_url}matches/{match.id}"
        print(f"Fetching: {url}")
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                detailed_data = response.json()
                
                # Save full response for analysis
                with open(f"detailed_match_{match.id}.json", "w") as f:
                    json.dump(detailed_data, f, indent=2)
                
                print(f"✅ Detailed data saved to detailed_match_{match.id}.json")
                
                # Look for ELO-related fields
                print("Searching for ELO-related fields...")
                
                def find_elo_fields(data, path=""):
                    """Recursively search for ELO-related fields"""
                    if isinstance(data, dict):
                        for key, value in data.items():
                            current_path = f"{path}.{key}" if path else key
                            if any(elo_word in key.lower() for elo_word in ['elo', 'rating', 'rank', 'change']):
                                print(f"  📈 Found ELO field: {current_path} = {value}")
                            if isinstance(value, (dict, list)):
                                find_elo_fields(value, current_path)
                    elif isinstance(data, list):
                        for idx, item in enumerate(data):
                            current_path = f"{path}[{idx}]" if path else f"[{idx}]"
                            find_elo_fields(item, current_path)
                
                find_elo_fields(detailed_data)
                
                # Check if there are player arrays with detailed ELO info
                if 'players' in detailed_data:
                    print(f"\nPlayer data structure:")
                    for j, player in enumerate(detailed_data['players']):
                        print(f"  Player {j}: {player.keys()}")
                        if 'eloChange' in player:
                            print(f"    🎯 Found eloChange: {player['eloChange']}")
                        if 'eloRate' in player:
                            print(f"    📊 eloRate: {player['eloRate']}")
                
                print("-" * 50)
                
            else:
                print(f"❌ Failed to fetch: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        print()


if __name__ == "__main__":
    # Replace with an actual username that has matches
    username = input("Enter username to debug detailed match data: ").strip()
    if username:
        debug_detailed_match_data(username)
    else:
        print("Please provide a username")