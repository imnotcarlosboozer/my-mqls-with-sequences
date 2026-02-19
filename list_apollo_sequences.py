import requests
from apollo_config import APOLLO_API_KEY, APOLLO_API_URL
from difflib import get_close_matches

def get_all_sequences():
    """Fetch all sequences from Apollo."""
    url = f'{APOLLO_API_URL}/emailer_campaigns/search'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    all_sequences = []
    page = 1

    print("Fetching sequences from Apollo...")

    while True:
        payload = {
            'api_key': APOLLO_API_KEY,
            'page': page,
            'per_page': 100
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            campaigns = data.get('emailer_campaigns', [])

            if not campaigns:
                break

            for campaign in campaigns:
                all_sequences.append({
                    'id': campaign.get('id'),
                    'name': campaign.get('name'),
                    'active': campaign.get('active')
                })

            print(f"  Fetched page {page} ({len(campaigns)} sequences)")

            if len(campaigns) < 100:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching sequences: {e}")
            break

    return all_sequences


def find_matching_sequences(target_sequences, all_sequences):
    """Find close matches for target sequence names."""
    sequence_names = [seq['name'] for seq in all_sequences]

    print("\n" + "="*70)
    print("SEQUENCE MATCHING RESULTS")
    print("="*70)

    for target in target_sequences:
        print(f"\nLooking for: '{target}'")
        print("-" * 70)

        # Try exact match first
        exact_match = next((seq for seq in all_sequences if seq['name'] == target), None)
        if exact_match:
            print(f"✓ EXACT MATCH FOUND: {exact_match['name']}")
            print(f"  ID: {exact_match['id']}")
            print(f"  Active: {exact_match['active']}")
            continue

        # Find close matches
        close_matches = get_close_matches(target, sequence_names, n=5, cutoff=0.6)

        if close_matches:
            print("Possible matches:")
            for i, match in enumerate(close_matches, 1):
                seq = next(seq for seq in all_sequences if seq['name'] == match)
                print(f"{i}. {match}")
                print(f"   ID: {seq['id']} | Active: {seq['active']}")
        else:
            print("❌ No close matches found")
            # Show sequences containing key words from target
            keywords = [word.lower() for word in target.split() if len(word) > 3]
            if keywords:
                print("\nSequences containing similar keywords:")
                found_any = False
                for seq in all_sequences:
                    seq_lower = seq['name'].lower()
                    if any(keyword in seq_lower for keyword in keywords):
                        print(f"  • {seq['name']}")
                        print(f"    ID: {seq['id']} | Active: {seq['active']}")
                        found_any = True
                if not found_any:
                    print("  (none found)")


if __name__ == '__main__':
    # These are the sequences that weren't found
    missing_sequences = [
        '[MKTG] Webinar - State of Airflow 2026',
        '[MKTG] Webinar - ETL',
        '[MKTG] Webinar_Best practices for writing ETL-ELT pipelines',
        '[MKTG] Content - Testing Airflow'
    ]

    print("Apollo Sequence Finder")
    print("="*70)

    all_sequences = get_all_sequences()
    print(f"\nTotal sequences found: {len(all_sequences)}")

    find_matching_sequences(missing_sequences, all_sequences)

    # Also show all MKTG sequences for reference
    print("\n" + "="*70)
    print("ALL [MKTG] SEQUENCES")
    print("="*70)
    mktg_sequences = [seq for seq in all_sequences if '[MKTG]' in seq['name']]
    for seq in sorted(mktg_sequences, key=lambda x: x['name']):
        status = "✓ Active" if seq['active'] else "✗ Inactive"
        print(f"{status} | {seq['name']}")
