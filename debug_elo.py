"""
Debug script to investigate ELO data structure from MCSR Ranked API.
This will help understand if the issue is with current vs historical ELO.
"""

import json
from mcsr_stats import MCSRAnalyzer
from match import Match


def debug_elo_data(username: str, max_matches: int = 10):
    """
    Debug ELO data from API responses to understand the structure
    """
    print(f"=== Debugging ELO Data for {username} ===\n")
    
    analyzer = MCSRAnalyzer(username)
    
    # Fetch a small number of recent matches
    analyzer.fetch_all_matches(use_cache=True, max_matches=max_matches)
    
    if not analyzer.matches:
        print("No matches found")
        return
    
    print(f"Found {len(analyzer.matches)} matches\n")
    
    # Get ELO progression 
    elo_progression = analyzer.get_elo_progression()
    
    if not elo_progression:
        print("No ELO data available in matches")
        return
    
    print("=== ELO PROGRESSION ANALYSIS ===")
    print(f"{'Date':<12} {'ELO Before':<10} {'Change':<8} {'ELO After':<10} {'Result':<8}")
    print("-" * 60)
    
    for i, point in enumerate(elo_progression[:10]):  # Show first 10
        date_str = point['date'].strftime('%m/%d/%y')
        elo_before = point['elo_before'] or 'N/A'
        elo_change = point['elo_change'] or 'N/A'
        elo_after = point['elo_after'] or 'N/A'
        result = point['result'][:6]  # Truncate result
        
        print(f"{date_str:<12} {str(elo_before):<10} {str(elo_change):<8} {str(elo_after):<10} {result:<8}")
        
        # Check if progression makes sense
        if i > 0:
            prev_point = elo_progression[i-1]
            if (prev_point['elo_after'] is not None and 
                point['elo_before'] is not None and 
                prev_point['elo_after'] != point['elo_before']):
                print(f"  ⚠️  WARNING: ELO gap detected! Previous after: {prev_point['elo_after']}, Current before: {point['elo_before']}")
    
    print("\n=== RAW MATCH DATA SAMPLE ===")
    # Show raw data for first match with ELO
    for match in analyzer.matches[:5]:
        if match.get_user_elo_rate() is not None:
            print(f"Match ID: {match.id}")
            print(f"Date: {match.date_str()}")
            print(f"Raw user_player_info: {match.user_player_info}")
            print(f"Calculated ELO before: {match.get_user_elo_before()}")
            print(f"ELO change: {match.get_user_elo_change()}")
            print(f"ELO after: {match.get_user_elo_rate()}")
            print()
            break
    
    print("\n=== POTENTIAL ISSUES TO CHECK ===")
    print("1. Are eloRate values showing current ELO instead of historical?")
    print("2. Is eloChange calculation correct?")
    print("3. Should we be using a different API endpoint?")
    print("4. Are matches sorted in the correct chronological order?")
    
    # Check chronological order
    dates = [point['date'] for point in elo_progression]
    is_sorted = dates == sorted(dates)
    print(f"5. Matches are chronologically sorted: {is_sorted}")


if __name__ == "__main__":
    # Replace with an actual username that has ELO data
    username = input("Enter username to debug ELO data: ").strip()
    if username:
        debug_elo_data(username)
    else:
        print("Please provide a username")