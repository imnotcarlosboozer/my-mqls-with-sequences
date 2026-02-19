import csv
import requests
import time
from typing import Optional, Dict, List, Any
from apollo_config import APOLLO_API_KEY, APOLLO_API_URL, EMAIL_ACCOUNT_ID

def search_contact(first_name: str, last_name: str, email: str) -> Optional[str]:
    """Search for a contact in Apollo and return their contact ID. Create if needed."""
    url = f'{APOLLO_API_URL}/people/match'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'api_key': APOLLO_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        person = data.get('person', {})

        # Check if contact already exists
        if person.get('contact') and person['contact'].get('id'):
            return person['contact']['id']

        # Person exists but no contact record - create one
        if person.get('id'):
            print(f"  Person found but not in contacts. Creating contact record...")
            contact_id = create_contact(first_name, last_name, email, person)
            return contact_id

        return None
    except requests.exceptions.RequestException as e:
        print(f"Error searching for {first_name} {last_name}: {e}")
        return None


def create_contact(first_name: str, last_name: str, email: str, person_data: dict) -> Optional[str]:
    """Create a new contact in Apollo from person data."""
    url = f'{APOLLO_API_URL}/contacts'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'api_key': APOLLO_API_KEY,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'title': person_data.get('title', ''),
        'organization_name': person_data.get('organization', {}).get('name', ''),
        'person_id': person_data.get('id')
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('contact') and data['contact'].get('id'):
            print(f"  ✓ Created contact record")
            return data['contact']['id']
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error creating contact: {e}")
        return None


def get_all_sequences_once(sequences_cache: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch all sequences once and store in cache."""
    if 'all_sequences' in sequences_cache:
        return sequences_cache['all_sequences']

    url = f'{APOLLO_API_URL}/emailer_campaigns/search'
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    all_sequences = []
    page = 1

    try:
        while True:
            payload = {
                'api_key': APOLLO_API_KEY,
                'page': page,
                'per_page': 100
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            campaigns = data.get('emailer_campaigns', [])
            if not campaigns:
                break

            all_sequences.extend(campaigns)

            if len(campaigns) < 100:
                break

            page += 1

        sequences_cache['all_sequences'] = all_sequences
        return all_sequences

    except requests.exceptions.RequestException as e:
        print(f"Error fetching sequences: {e}")
        return []


def get_sequence_id(sequence_name: str, sequences_cache: Dict[str, Any], last_activity: str = '') -> Optional[str]:
    """Get sequence ID by name, with smart handling of ATTENDED/NO SHOW variants."""
    # Check simple cache first
    cache_key = f"{sequence_name}|{last_activity}"
    if cache_key in sequences_cache:
        return sequences_cache[cache_key]

    # Get all sequences
    all_sequences = get_all_sequences_once(sequences_cache)

    # Try exact match first
    for campaign in all_sequences:
        if campaign.get('name') == sequence_name:
            sequence_id = campaign['id']
            sequences_cache[cache_key] = sequence_id
            return sequence_id

    # If no exact match, check if this is a webinar sequence that needs ATTENDED/NO SHOW suffix
    if 'Webinar' in sequence_name or 'webinar' in sequence_name:
        # Check if ATTENDED or NO SHOW variants exist
        attended_name = f"{sequence_name} ATTENDED"
        no_show_name = f"{sequence_name} NO SHOW"

        attended_seq = None
        no_show_seq = None

        for campaign in all_sequences:
            camp_name = campaign.get('name', '')
            if camp_name == attended_name:
                attended_seq = campaign
            elif camp_name == no_show_name:
                no_show_seq = campaign

        # If both variants exist, choose based on last_activity
        if attended_seq and no_show_seq:
            if last_activity and last_activity.strip():
                # Has activity - assume attended
                print(f"  → Found activity date ({last_activity}), using ATTENDED sequence")
                sequences_cache[cache_key] = attended_seq['id']
                return attended_seq['id']
            else:
                # No activity - assume no show
                print(f"  → No activity date, using NO SHOW sequence")
                sequences_cache[cache_key] = no_show_seq['id']
                return no_show_seq['id']

        # If only one variant exists, use it
        if attended_seq:
            print(f"  → Using ATTENDED sequence variant")
            sequences_cache[cache_key] = attended_seq['id']
            return attended_seq['id']

        if no_show_seq:
            print(f"  → Using NO SHOW sequence variant")
            sequences_cache[cache_key] = no_show_seq['id']
            return no_show_seq['id']

    print(f"Warning: Sequence '{sequence_name}' not found")
    return None


def add_contact_to_sequence(contact_id: str, sequence_id: str, first_name: str, last_name: str) -> Dict[str, Any]:
    """Add a contact to a specific sequence. Returns dict with status and skip reason."""
    url = f'{APOLLO_API_URL}/emailer_campaigns/{sequence_id}/add_contact_ids'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    payload = {
        'contact_ids': [contact_id],
        'emailer_campaign_id': sequence_id,
        'send_email_from_email_account_id': EMAIL_ACCOUNT_ID,
        'api_key': APOLLO_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Check if contact was skipped
        skipped = data.get('skipped_contact_ids', {})
        if contact_id in skipped:
            reason = skipped[contact_id]
            return {
                'success': False,
                'skipped': True,
                'reason': reason,
                'contact_id': contact_id
            }

        # Check if contact was added successfully
        if data.get('contacts'):
            print(f"✓ Added {first_name} {last_name} to sequence")
            return {'success': True, 'skipped': False}

        # Unknown response
        return {
            'success': False,
            'skipped': False,
            'reason': 'Unknown error'
        }

    except requests.exceptions.RequestException as e:
        print(f"✗ Error adding {first_name} {last_name} to sequence: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text}")
        return {
            'success': False,
            'skipped': False,
            'reason': str(e)
        }


def process_csv(csv_file_path: str):
    """Process the CSV file and add prospects to their recommended sequences."""
    sequences_cache = {}
    stats = {
        'total': 0,
        'added': 0,
        'not_found': 0,
        'no_sequence': 0,
        'skipped_in_other_sequence': 0,
        'skipped_job_change': 0,
        'errors': 0
    }
    skipped_contacts = []  # Track contacts that need manual intervention

    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            email = row.get('Email', '').strip()
            sequence_name = row.get('Recommended Outreach Sequence', '').strip()
            last_activity = row.get('Last Activity', '').strip()

            stats['total'] += 1

            if not first_name or not last_name:
                print(f"Skipping row {stats['total']}: Missing name")
                stats['errors'] += 1
                continue

            if not sequence_name:
                print(f"Skipping {first_name} {last_name}: No recommended sequence")
                stats['no_sequence'] += 1
                continue

            print(f"\nProcessing: {first_name} {last_name} ({email})")
            print(f"Sequence: {sequence_name}")
            if last_activity:
                print(f"Last Activity: {last_activity}")

            # Search for contact in Apollo
            contact_id = search_contact(first_name, last_name, email)

            if not contact_id:
                print(f"✗ Contact not found in Apollo")
                stats['not_found'] += 1
                continue

            print(f"Found contact ID: {contact_id}")

            # Get sequence ID (automatically handles ATTENDED/NO SHOW variants)
            sequence_id = get_sequence_id(sequence_name, sequences_cache, last_activity)

            if not sequence_id:
                stats['errors'] += 1
                continue

            # Add contact to sequence
            result = add_contact_to_sequence(contact_id, sequence_id, first_name, last_name)

            if result['success']:
                stats['added'] += 1
            elif result.get('skipped'):
                reason = result.get('reason', 'unknown')
                if reason == 'contacts_active_in_other_campaigns':
                    print(f"⚠️  Skipped: Already in another active sequence")
                    print(f"   Action needed: Manually remove from current sequence in Apollo")
                    stats['skipped_in_other_sequence'] += 1
                    skipped_contacts.append({
                        'name': f"{first_name} {last_name}",
                        'email': email,
                        'target_sequence': sequence_name,
                        'contact_id': contact_id,
                        'reason': reason
                    })
                elif reason == 'contacts_with_job_change':
                    print(f"⚠️  Skipped: Recent job change detected")
                    print(f"   Action needed: Review in Apollo and manually add if appropriate")
                    stats['skipped_job_change'] += 1
                    skipped_contacts.append({
                        'name': f"{first_name} {last_name}",
                        'email': email,
                        'target_sequence': sequence_name,
                        'contact_id': contact_id,
                        'reason': reason
                    })
                else:
                    print(f"⚠️  Skipped: {reason}")
                    stats['errors'] += 1
            else:
                stats['errors'] += 1

            # Rate limiting: wait 0.5 seconds between requests
            time.sleep(0.5)

    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total prospects processed: {stats['total']}")
    print(f"Successfully added to sequences: {stats['added']}")
    print(f"Not found in Apollo: {stats['not_found']}")
    print(f"No recommended sequence: {stats['no_sequence']}")
    print(f"Already in other sequences (need manual removal): {stats['skipped_in_other_sequence']}")
    print(f"Job change detected (need manual review): {stats['skipped_job_change']}")
    print(f"Errors: {stats['errors']}")

    # Print details of skipped contacts
    if skipped_contacts:
        print("\n" + "="*50)
        print("CONTACTS NEEDING MANUAL INTERVENTION")
        print("="*50)

        # Group by reason
        in_other_sequences = [c for c in skipped_contacts if c['reason'] == 'contacts_active_in_other_campaigns']
        job_changes = [c for c in skipped_contacts if c['reason'] == 'contacts_with_job_change']

        if in_other_sequences:
            print("\n1. Already in other active sequences:")
            print("   Action: Remove from current sequence in Apollo, then re-run this script.\n")
            for contact in in_other_sequences:
                print(f"   • {contact['name']} ({contact['email']})")
                print(f"     Target sequence: {contact['target_sequence']}\n")

        if job_changes:
            print("\n2. Recent job change detected:")
            print("   Action: Review contact details in Apollo and manually add if appropriate.\n")
            for contact in job_changes:
                print(f"   • {contact['name']} ({contact['email']})")
                print(f"     Target sequence: {contact['target_sequence']}\n")


if __name__ == '__main__':
    csv_file = '/Users/vishwasrinivasan/Downloads/report1771535690371.csv'

    print("Apollo Sequence Enrollment Script")
    print("="*50)
    print(f"Processing file: {csv_file}")
    print()

    process_csv(csv_file)
