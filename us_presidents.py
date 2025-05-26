'''
presidents.py

Tools for scraping, cleaning, and loading structured data about U.S. presidents.

Features:
- Fetch cleaned presidential data from Wikipedia or a frozen GitHub version.
- Parse and structure name, dates, parties, and vice presidents.
- Save/restore datasets with full data fidelity (dates, lists, nulls).
'''

import pandas as pd
import re
from pathlib import Path

# URL to the Wikipedia page
URL = 'https://en.wikipedia.org/wiki/List_of_presidents_of_the_United_States'

# URL to my GitHub-hosted 'stable' version of the CSV dataset
FROZEN_CSV_URL = 'my.repo'

# What we will write to CSV to indicate missing values (pd.NA)
NA_REPR = 'NA'

# Column groupings
NULLABLE_INT_COLS = ['birth', 'death']
DATETIME_COLS = ['term_start', 'term_end']
LIST_COLS = ['party', 'election', 'vice_president']

RECOGNIZED_PARTIES = set([
	'Unaffiliated',
	'Federalist',
	'Democratic-Republican',
	'National Republican',
	'Democratic',
	'Whig',
	'National Union',
	'Republican'
])

##################################################
#              Cleaning Helpers                  #
##################################################
def remove_footnotes(text):
	''' Remove footnotes like `[19]` or `[c]`. '''
	if not isinstance(text, str):
		return text
	return re.sub(r'\[.*?\]', '', text).strip()

def extract_parties(text):
	''' Return a list of recognized parties from `text`. '''
	if not isinstance(text, str):
		return text
	
	# Get rid of spaces next to dashes
	text = re.sub(r'\s*-\s*', '-', text)

	# Remove extra spaces and enforce Title Case
	text = re.sub(r'\s+', ' ', text).strip().title()

	# Find all recognized parties
	parts = text.split()

	found = []
	current = ''
	for part in parts:
		# Continue building
		if current:
			current += ' ' + part
		else:
			current = part
		# Found party
		if current in RECOGNIZED_PARTIES:
			found.append(current)
			current = ''
	if current in RECOGNIZED_PARTIES:
		found.append(current)

	return found

def extract_vice_presidents(text):
	''' Return a list of vice presidents and vacancy messages from `text`. '''
	if not isinstance(text, str):
		return text

	# Replace &nbsp; and normalize whitespace
	text = text.replace('\xa0', ' ')
	text = re.sub(r'\s+', ' ', text).strip()

	# Split the string at each vacancy message, keeping the vacancy tokens
	split_text = re.split(r'(Vacant throughout presidency|Vacant.*?\d{4})', text, flags=re.IGNORECASE)

	return list(token.strip() for token in split_text if token)

def extract_election_dates(text):
	''' Parse election text into a list of integers where `pd.NA` indicates no election. '''
	if not isinstance(text, str):
		return text
	years = []
	for s in text.split():
		if '–' in s: # Ignore year ranges and only take the first (ex. 1788–89)
			s = s.split('–')[0]
		try:
			years.append(int(s))
		except Exception:
			years.append(pd.NA)
	return years

def split_name_birth_death(text):
	''' Return a pandas Series of `[name, birth, death]` from a single string.
		- `name (YYYY–YYYY)`
		- `name (b. YYYY)`
	'''
	match = re.match(r'(.*?)\s*\((?:(\d{4})–(\d{4})|b\. (\d{4}))\)', text)
	if not match:
		return pd.Series([pd.NA] * 3)
	
	# Extract from capture groups
	name = match.group(1)
	birth = match.group(2) if match.group(2) else match.group(4)
	death = match.group(3) if match.group(3) else pd.NA

	return pd.Series([name, birth, death])

def split_term(text):
	''' Return a pandas Series of `[term_start, term_end]` given text.
		- `<Month Day, Year>–<Month Day, Year>`
	'''
	terms = re.split(r'\s*–\s*', text)
	if len(terms) == 2:
		start = terms[0].strip()
		end = terms[1].strip()
		if end == 'Incumbent': # Term not over
			end = pd.NA
		return pd.Series([start, end])
	# Failed to extract 2 tokens
	return pd.Series([pd.NA] * 2)


##################################################
#              Clean Raw Data                    #
##################################################
def clean_presidents_df(raw_df):
	''' Clean the raw DataFrame extracted from the `URL` completely.  
		Return the cleaned copy.
	'''
	df = raw_df.copy()
	df.drop(df.columns[[1, 4]], axis=1, inplace=True) # Drop Portrait and first Party column
	df.columns = ['number', 'name_birth_death', 'term', 'party', 'election', 'vice_president']
	df.set_index('number', inplace=True)

	# Clean footnotes
	for col in ['name_birth_death', 'vice_president', 'party', 'term']:
		df[col] = df[col].apply(remove_footnotes)

	# Extract structured data
	df['party'] = df['party'].apply(extract_parties)
	df['vice_president'] = df['vice_president'].apply(extract_vice_presidents)
	df['election'] = df['election'].apply(extract_election_dates)
	df[['name', 'birth', 'death']] = df['name_birth_death'].apply(split_name_birth_death)
	df[['term_start', 'term_end']] = df['term'].apply(split_term)

	# Drop old columns
	df.drop(columns=['name_birth_death', 'term'], inplace=True)

	# Reorder columns
	df = df[['name', 'birth', 'death', 'term_start', 'term_end', 'party', 'election', 'vice_president']]

	# Set types
	df['name'] = df['name'].astype('string')
	df['birth'] = df['birth'].astype('Int64')
	df['death'] = df['death'].astype('Int64')
	df['term_start'] = pd.to_datetime(df['term_start'], errors='coerce')
	df['term_end'] = pd.to_datetime(df['term_end'], errors='coerce')

	return df


##################################################
#               Save and Load CSV                #
##################################################
def list_to_pipe_string(lst):
	''' Convert a list to a pipe-separated string, replacing `pd.NA` with "NA". '''
	if not lst:
		return pd.NA
	if isinstance(lst, list):
		return ' | '.join('NA' if pd.isna(item) else str(item) for item in lst)
	return lst

def pipe_string_to_list(s):
	''' Convert a pipe-separated string back to a list, converting "NA" to `pd.NA`. '''
	if pd.isna(s):
		return [pd.NA]
	if isinstance(s, str):
		return [pd.NA if item.strip() == 'NA' else item.strip() for item in s.split('|')]
	return s

def save_csv(df, filename, output=None):
	'''
	Prepares and saves the DataFrame to a CSV file without modifying the original.

	Parameters
	----------
	df : pd.DataFrame
		DataFrame to save.
	filename : str
		Name of the CSV file (without `.csv` extension).
	output : str or Path, optional
		Folder or full path to save the CSV file. If None, saves to current directory.
	'''
	df_temp = df.copy()

	# Format datetime columns as strings (Month Day, Year)
	for col in DATETIME_COLS:
		df_temp[col] = df_temp[col].apply(
			lambda d: f'{d.month_name()} {d.day}, {d.year}' if pd.notna(d) else pd.NaT
		)
	
	# Serialize list columns into pipe-separated strings
	for col in LIST_COLS:
		df_temp[col] = df_temp[col].apply(list_to_pipe_string)

	# Build output path
	if output:
		output_path = Path(output)
		if output_path.suffix != '.csv':
			output_path = output_path / f'{filename}.csv'
	else:
		output_path = Path(f'{filename}.csv')

	# Build necessary folders
	output_path.parent.mkdir(parents=True, exist_ok=True)
	
	# Save CSV with 'NA' for nulls
	# Use UTF-8 BOM so Excel can correctly display Unicode characters
	df_temp.to_csv(output_path, na_rep='NA', encoding='utf-8-sig')

def load_csv(filepath):
	''' Loads and restores the DataFrame from a saved CSV file. '''
	df = pd.read_csv(filepath, index_col=0, na_values='NA')

	# Convert datetime strings back to datetime objects
	for col in DATETIME_COLS:
		df[col] = pd.to_datetime(df[col], errors='coerce')
	
	# Restore lists from pipe strings
	for col in LIST_COLS:
		df[col] = df[col].apply(pipe_string_to_list)

	# Restore nullable integer columns
	for col in NULLABLE_INT_COLS:
		df[col] = df[col].astype('Int64')

	# Restore election list to integers
	df['election'] = df['election'].apply(lambda lst: [pd.NA if pd.isna(x) else int(x) for x in lst])

	# Convert name column to strings
	df['name'] = df['name'].astype('string')
	
	return df


##################################################
#                 Access Dataset                 #
##################################################
def fetch(update=False, save=False, dataset_name='us_presidents_cleaned', output=None):
	'''
	Fetch the US presidents dataset.

	Parameters
	----------
	update : bool, optional
		If `False`, attempts to load frozen CSV from GitHub.  
		If `True`, scrapes fresh from Wikipedia and cleans it.
	save : bool, optional
		If `True`, saves the cleaned DataFrame to CSV.
	dataset_name : str, optional
		Filename (without `.csv`) to use when saving.
	output : str or Path, optional
		Where to save the CSV (folder or full path).

	Returns
	-------
	pd.DataFrame
		Cleaned presidents dataset.
	'''
	if not update:
		try:
			# Try downloading the frozen version on GitHub
			df = load_csv(FROZEN_CSV_URL)
			if save:
				save_csv(df, filename=dataset_name, output=output)
			return df
		except Exception as e:
			print(f'[WARNING] Could not load frozen dataset from GitHub:\n{e}')
			update = True # Fallback to scraping

	if update:
		raw_tables = pd.read_html(URL)
		df_raw = raw_tables[0]
		df_clean = clean_presidents_df(df_raw)
		if save:
			save_csv(df_clean, filename=dataset_name, output=output)
		return df_clean


# Used as script
if __name__ == '__main__':
	fetch(update=True, save=True, output='data') # Re-scrape and save