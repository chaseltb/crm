"""
utils/import_contacts.py — Parse Excel/CSV uploads into contact row dicts.
"""

import base64
import io
import pandas as pd

# Common column name → CRM field aliases (lowercased, stripped)
FIELD_ALIASES = {
    'first_name': ['first name', 'firstname', 'first_name', 'fname', 'given name'],
    'last_name':  ['last name', 'lastname', 'last_name', 'lname', 'surname', 'family name'],
    'full_name':  ['name', 'full name', 'full_name', 'contact name', 'contact'],
    'company':    ['company', 'business', 'organization', 'org', 'account', 'employer'],
    'email':      ['email', 'e-mail', 'email address', 'email_address', 'mail'],
    'phone':      ['phone', 'mobile', 'cell', 'telephone', 'phone number', 'phone_number'],
    'city':       ['city', 'town', 'locality'],
    'state':      ['state', 'province', 'region'],
    'source':     ['source', 'lead source', 'lead_source', 'channel', 'origin'],
    'tags':       ['tags', 'tag', 'labels', 'category', 'categories'],
}

DISPLAY_NAMES = {
    'first_name': 'First Name', 'last_name': 'Last Name', 'full_name': 'Full Name',
    'company': 'Company', 'email': 'Email', 'phone': 'Phone',
    'city': 'City', 'state': 'State', 'source': 'Source', 'tags': 'Tags',
}


def parse_upload(contents: str, filename: str) -> pd.DataFrame:
    """Decode a dcc.Upload data URL and return a cleaned DataFrame."""
    _, content_string = contents.split(',', 1)
    decoded = base64.b64decode(content_string)
    fname = filename.lower()
    if fname.endswith('.csv'):
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        except UnicodeDecodeError:
            df = pd.read_csv(io.StringIO(decoded.decode('latin-1')))
    elif fname.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(decoded))
    else:
        raise ValueError(f"Unsupported file type '{filename}'. Use .xlsx, .xls, or .csv.")
    df.columns = [str(c) for c in df.columns]
    df.dropna(how='all', inplace=True)
    return df


def auto_map(columns: list) -> dict:
    """Returns {crm_field: original_column_name} for columns we recognise."""
    col_lower = {str(c).lower().strip(): c for c in columns}
    mapping = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in col_lower:
                mapping[field] = col_lower[alias]
                break
    return mapping


def df_to_contact_rows(df: pd.DataFrame, mapping: dict) -> list:
    """Convert DataFrame rows to contact dicts; skips rows with no name."""
    contacts = []

    def _get(row, field):
        col = mapping.get(field)
        if not col or col not in row.index:
            return ''
        val = row[col]
        return str(val).strip() if pd.notna(val) else ''

    for _, row in df.iterrows():
        first = _get(row, 'first_name')
        last  = _get(row, 'last_name')

        if not first and not last:
            full = _get(row, 'full_name')
            if full:
                parts = full.split(' ', 1)
                first = parts[0]
                last  = parts[1] if len(parts) > 1 else ''

        if not first and not last:
            continue

        contacts.append({
            'first_name': first,
            'last_name':  last,
            'company': _get(row, 'company'),
            'email':   _get(row, 'email'),
            'phone':   _get(row, 'phone'),
            'city':    _get(row, 'city'),
            'state':   _get(row, 'state'),
            'source':  _get(row, 'source'),
            'tags':    _get(row, 'tags'),
        })
    return contacts
