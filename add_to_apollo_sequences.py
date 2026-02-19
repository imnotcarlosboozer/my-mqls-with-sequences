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


def get_sequence_id(sequence_name: str, sequences_cache: Dict[str, str]) -> Optional[str]:
    """Get sequence ID by name, using cache to avoid repeated API calls."""
    if sequence_name in sequences_cache:
        return sequences_cache[sequence_name]

    url = f'{APOLLO_API_URL}/emailer_campaigns/search'

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    }

    try:
        # Search through multiple pages to find exact match
        # Apollo's search doesn't do exact matching, so we need to search all results
        page = 1
        max_pages = 10  # Limit search to prevent infinite loops

        while page <= max_pages:
            payload = {
                'api_key': APOLLO_API_KEY,
                'page': page,
                'per_page': 100
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            campaigns = data.get('emailer_campaigns', [])

            # Look for exact match
            for campaign in campaigns:
                if campaign.get('name') == sequence_name:
                    sequence_id = campaign['id']
                    sequences_cache[sequence_name] = sequence_id
                    return sequence_id

            # If we got fewer than 100 results, we've reached the end
            if len(campaigns) < 100:
                break

            page += 1

        print(f"Warning: Sequence '{sequence_name}' not found")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sequence '{sequence_name}': {e}")
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

            # Search for contact in Apollo
            contact_id = search_contact(first_name, last_name, email)

            if not contact_id:
                print(f"✗ Contact not found in Apollo")
                stats['not_found'] += 1
                continue

            print(f"Found contact ID: {contact_id}")

            # Get sequence ID
            sequence_id = get_sequence_id(sequence_name, sequences_cache)

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
    print(f"Errors: {stats['errors']}")

    # Print details of skipped contacts
    if skipped_contacts:
        print("\n" + "="*50)
        print("CONTACTS NEEDING MANUAL INTERVENTION")
        print("="*50)
        print("\nThese contacts are already in other active sequences.")
        print("Action: Remove them from their current sequence in Apollo, then re-run this script.\n")

        for contact in skipped_contacts:
            print(f"• {contact['name']} ({contact['email']})")
            print(f"  Target sequence: {contact['target_sequence']}")
            print(f"  Reason: {contact['reason']}\n")


if __name__ == '__main__':
    csv_file = '/Users/vishwasrinivasan/Downloads/report1771436312348.csv'

    print("Apollo Sequence Enrollment Script")
    print("="*50)
    print(f"Processing file: {csv_file}")
    print()

    process_csv(csv_file)
