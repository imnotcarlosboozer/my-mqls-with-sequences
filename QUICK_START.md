# Quick Start Guide - Apollo Sequence Enrollment

## 5-Minute Setup

### Step 1: Copy the files to your computer

Copy these 3 files to a folder:
- `add_to_apollo_sequences.py`
- `apollo_config.template.py`
- Your CSV report file

### Step 2: Set up your Apollo credentials

1. **Rename the template file:**
   ```bash
   cp apollo_config.template.py apollo_config.py
   ```

2. **Get your Apollo API Key:**
   - Go to https://app.apollo.io
   - Click Settings → Integrations → API
   - Copy your API Key

3. **Get your Email Account ID:**
   - Go to Settings → Email Accounts
   - Copy the ID for your connected email account
   - (Or contact your admin for this ID)

4. **Edit apollo_config.py and paste your credentials:**
   ```python
   APOLLO_API_KEY = "paste_your_api_key_here"
   EMAIL_ACCOUNT_ID = "paste_your_email_account_id_here"
   ```

### Step 3: Prepare your CSV file

Your CSV must have these columns:
- `First Name`
- `Last Name`
- `Email`
- `Recommended Outreach Sequence`

Example:
```csv
First Name,Last Name,Email,Recommended Outreach Sequence
John,Doe,john@example.com,[MKTG] Content - Product Demo
Jane,Smith,jane@example.com,[SALES] Outbound - Enterprise
```

### Step 4: Update the CSV path in the script

Edit `add_to_apollo_sequences.py` line 169:
```python
csv_file = '/path/to/your/report.csv'
```

### Step 5: Run it!

```bash
python3 add_to_apollo_sequences.py
```

## Expected Result

```
Apollo Sequence Enrollment Script
==================================================
Processing file: /path/to/your/report.csv

Processing: John Doe (john@example.com)
Sequence: [MKTG] Content - Product Demo
Found contact ID: 6623a728d461c40007e06968
✓ Added John Doe to sequence

Processing: Jane Smith (jane@example.com)
Sequence: [SALES] Outbound - Enterprise
  Person found but not in contacts. Creating contact record...
  ✓ Created contact record
Found contact ID: 699608b80c9afc0019471c39
✓ Added Jane Smith to sequence

==================================================
SUMMARY
==================================================
Total prospects processed: 2
Successfully added to sequences: 2
Not found in Apollo: 0
No recommended sequence: 0
Errors: 0
```

**Note:** The script automatically creates contact records for people who exist in Apollo's database but aren't in your contacts yet.

## Common Issues

**"Invalid access credentials"**
→ Check your API key in apollo_config.py

**"Contact not found in Apollo"**
→ Make sure the prospect exists in your Apollo account first

**"Sequence not found"**
→ Copy the exact sequence name from Apollo (case-sensitive!)

## Need Help?

See the full documentation in `README_apollo_sequence_enrollment.md`
