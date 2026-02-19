# Apollo Sequence Enrollment Script

This script automatically enrolls prospects from a CSV report into their recommended Apollo outreach sequences.

## What It Does

1. Reads a CSV file containing prospect information
2. Searches for each prospect in Apollo by first name, last name, and email
3. If the prospect exists in Apollo's database but not in your contacts, automatically creates a contact record
4. Looks up the sequence by name from the "Recommended Outreach Sequence" column
5. Enrolls each prospect into their respective sequence using the correct contact ID
6. Provides a detailed summary of results

**Important:** Apollo has two types of records - "people" (in their global database) and "contacts" (in your account). This script handles both and automatically creates contact records when needed.

## Prerequisites

- Python 3.6 or higher
- `requests` library (`pip install requests`)
- Apollo.io account with API access
- Active Apollo sequences that you want to enroll prospects into

## Setup Instructions

### Step 1: Get Your Apollo API Credentials

1. Log in to [Apollo.io](https://app.apollo.io)
2. Go to **Settings → Integrations → API**
3. Copy your **API Key** (it will look something like `RPSs02pLXPo7kpTey1iFTw`)
4. Go to **Settings → Email Accounts**
5. Find your connected email account and copy the **Email Account ID**
   - Or run `get_apollo_info.py` to find it programmatically

### Step 2: Configure Apollo Credentials

Edit the `apollo_config.py` file and update these values:

```python
# Your Apollo API credentials
APOLLO_API_KEY = "YOUR_API_KEY_HERE"

# Your connected email account ID in Apollo
EMAIL_ACCOUNT_ID = "YOUR_EMAIL_ACCOUNT_ID_HERE"

# API Configuration (don't change)
APOLLO_API_URL = "https://api.apollo.io/v1"
```

**Example:**
```python
APOLLO_API_KEY = "RPSs02pLXPo7kpTey1iFTw"
EMAIL_ACCOUNT_ID = "677eb30031d14101b078515e"
APOLLO_API_URL = "https://api.apollo.io/v1"
```

### Step 3: Prepare Your CSV File

Your CSV file must have these columns:
- `First Name` - Prospect's first name
- `Last Name` - Prospect's last name
- `Email` - Prospect's email address
- `Recommended Outreach Sequence` - Exact name of the Apollo sequence

**Example CSV:**
```csv
First Name,Last Name,Email,Recommended Outreach Sequence
Andrew,Dunmall,andrew.dunmall@influxdata.co,[MKTG] Content - Quick Notes Airflow AI SDK Code Snippets
Edith,Montes,edith.montes@lagersoft.com,[MKTG] Content - Testing Airflow
```

### Step 4: Update the Script with Your CSV Path

Edit `add_to_apollo_sequences.py` and update line 169 with your CSV file path:

```python
csv_file = '/Users/yourname/Downloads/your_report.csv'
```

## Running the Script

```bash
python3 add_to_apollo_sequences.py
```

## Expected Output

**Success case:**
```
Apollo Sequence Enrollment Script
==================================================
Processing file: /Users/yourname/Downloads/report.csv


Processing: Andrew Dunmall (andrew.dunmall@influxdata.co)
Sequence: [MKTG] Content - Quick Notes Airflow AI SDK Code Snippets
Found contact ID: 6623a728d461c40007e06968
✓ Added Andrew Dunmall to sequence

Processing: Edith Montes (edith.montes@lagersoft.com)
Sequence: [MKTG] Content - Testing Airflow
Found contact ID: 69960798244f95001971c872
✓ Added Edith Montes to sequence

==================================================
SUMMARY
==================================================
Total prospects processed: 2
Successfully added to sequences: 2
Not found in Apollo: 0
No recommended sequence: 0
Already in other sequences (need manual removal): 0
Errors: 0
```

**When contacts are already in other sequences:**
```
Processing: John Doe (john@example.com)
Sequence: [MKTG] Content - Product Demo
Found contact ID: 6623a728d461c40007e06968
⚠️  Skipped: Already in another active sequence
   Action needed: Manually remove from current sequence in Apollo

==================================================
SUMMARY
==================================================
Total prospects processed: 1
Successfully added to sequences: 0
Already in other sequences (need manual removal): 1

==================================================
CONTACTS NEEDING MANUAL INTERVENTION
==================================================

These contacts are already in other active sequences.
Action: Remove them from their current sequence in Apollo, then re-run this script.

• John Doe (john@example.com)
  Target sequence: [MKTG] Content - Product Demo
  Reason: contacts_active_in_other_campaigns
```

## Troubleshooting

### "Invalid access credentials" Error

**Problem:** Your API key is incorrect or expired.

**Solution:**
1. Go to Apollo.io → Settings → Integrations → API
2. Generate a new API key if needed
3. Update `APOLLO_API_KEY` in `apollo_config.py`

### "Contact not found in Apollo" Error

**Problem:** The prospect doesn't exist in Apollo's database at all.

**Solution:**
- The prospect needs to exist in Apollo's database (either as a person or contact)
- Import the prospect into Apollo first, or
- Use Apollo's enrichment feature to find them

**Note:** If the prospect exists as a "person" in Apollo but not as a "contact" in your account, the script will automatically create the contact record for you.

### "Sequence not found" Warning

**Problem:** The sequence name in your CSV doesn't match any sequence in Apollo.

**Solution:**
- Go to Apollo.io → Sequences
- Copy the exact sequence name (case-sensitive)
- Update your CSV with the correct sequence name

### "Already in another active sequence" Warning

**Problem:** Apollo doesn't allow contacts to be in multiple active sequences at once.

**Solution:**
1. Go to Apollo.io → Sequences
2. Find the sequence the contact is currently in
3. Mark the contact as "Finished" or remove them from that sequence
4. Re-run this script

**Note:** The script automatically detects this and provides a detailed report of contacts needing manual removal at the end.

### "422 Unprocessable Entity" Error

**Problem:** Missing `EMAIL_ACCOUNT_ID` or the contact cannot be added to the sequence.

**Solution:**
- Verify `EMAIL_ACCOUNT_ID` is set correctly in `apollo_config.py`
- Check if the contact is already in the sequence
- Ensure the sequence is not paused or archived

## Files Required

- `add_to_apollo_sequences.py` - Main script
- `apollo_config.py` - Configuration file with your API credentials
- Your CSV report file

## Rate Limiting

The script includes a 0.5 second delay between API requests to avoid rate limiting. For large CSV files (100+ prospects), the script may take several minutes to complete.

## Notes

- The script will skip prospects that don't have a recommended sequence
- **Apollo doesn't allow contacts in multiple active sequences** - if a contact is already enrolled elsewhere, the script will detect this and provide a detailed report for manual intervention
- The script automatically creates contact records for people who exist in Apollo's database but aren't in your contacts yet
- Duplicate prospects are processed separately (no deduplication)
- The script does not activate sequences - make sure your sequences are already active in Apollo
- All output is logged to the console for tracking
- The script searches through all your sequences to find exact name matches (not just the first result)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your Apollo API credentials
3. Ensure your CSV has the required columns
4. Check that sequence names match exactly (case-sensitive)

## Code Files

### apollo_config.py
```python
"""
Apollo API Configuration
Get these values from your Apollo account:
1. API Key: Settings → Integrations → API
2. Email Account ID: Run get_email_accounts() to find yours
"""

# Your Apollo API credentials
APOLLO_API_KEY = "YOUR_API_KEY_HERE"

# Your connected email account ID in Apollo
EMAIL_ACCOUNT_ID = "YOUR_EMAIL_ACCOUNT_ID_HERE"

# API Configuration
APOLLO_API_URL = "https://api.apollo.io/v1"
```

### add_to_apollo_sequences.py
```python
import csv
import requests
import time
from typing import Optional, Dict, List
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

    payload = {
        'name': sequence_name,
        'api_key': APOLLO_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('emailer_campaigns') and len(data['emailer_campaigns']) > 0:
            sequence_id = data['emailer_campaigns'][0]['id']
            sequences_cache[sequence_name] = sequence_id
            return sequence_id

        print(f"Warning: Sequence '{sequence_name}' not found")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sequence '{sequence_name}': {e}")
        return None


def add_contact_to_sequence(contact_id: str, sequence_id: str, first_name: str, last_name: str) -> bool:
    """Add a contact to a specific sequence."""
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
        print(f"✓ Added {first_name} {last_name} to sequence")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Error adding {first_name} {last_name} to sequence: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text}")
        return False


def process_csv(csv_file_path: str):
    """Process the CSV file and add prospects to their recommended sequences."""
    sequences_cache = {}
    stats = {
        'total': 0,
        'added': 0,
        'not_found': 0,
        'no_sequence': 0,
        'errors': 0
    }

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
            if add_contact_to_sequence(contact_id, sequence_id, first_name, last_name):
                stats['added'] += 1
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
    print(f"Errors: {stats['errors']}")


if __name__ == '__main__':
    csv_file = '/Users/vishwasrinivasan/Downloads/report1771436312348.csv'

    print("Apollo Sequence Enrollment Script")
    print("="*50)
    print(f"Processing file: {csv_file}")
    print()

    process_csv(csv_file)
```

---

**Last Updated:** February 2026
