# Presidents of the United States

This repo provides a free, organized **dataset**—scraped and cleaned from [Wikipedia](https://en.wikipedia.org/wiki/List_of_presidents_of_the_United_States#Presidents).

## 📁 Dataset Overview


Delivered as a Pandas `DataFrame`, with clear typing and minimal preprocessing required.


| Column Name | Data Type | What is Stored | Example |
| ----------- | --------- | -------------- | ---: |
| `number` | `int64` | Presidential number | 1 |
| `name` | `string` | Full name of the president | George Washington |
| `birth` | `Int64` | Birth year | 1732 |
| `death` | `Int64` | Death year (nullable) | 1799 |
| `term_start` | `datetime64` | Start of first presidential term | 1789-04-30 |
| `term_end` | `datetime64` | End of final presidential term (nullable) | 1797-03-04 |
| `party` | `list[string]` | Political parties, in order of affiliation | [Unaffiliated] |
| `election` | `list[Int64]` | Years the president's elections took place | [1788, 1792] |
| `vice_president` | `list[string]` | Associated vice presidents <br>or descriptive `vacancy messages` | [John Adams] |

### 📝 Notes

- Lists are ordered from __earliest to latest__

- Lists for `election` may contain null values `pd.NA` representing no election

- `vacancy messages` are strings that describe a duration without any vice president

### Pandas Example

```
            name     birth    death    term_start      term_end            party        election    vice_president
number                                
43  George W. Bush    1946     <NA>    2001-01-20    2009-01-20     [Republican]    [2000, 2004]    [Dick Cheney]
44  Barack Obama      1961     <NA>    2009-01-20    2017-01-20     [Democratic]    [2008, 2012]    [Joe Biden]
45  Donald Trump      1946     <NA>    2017-01-20    2021-01-20     [Republican]    [2016]          [Mike Pence]
46  Joe Biden         1942     <NA>    2021-01-20    2025-01-20     [Democratic]    [2020]          [Kamala Harris]
47  Donald Trump      1946     <NA>    2025-01-20           NaT     [Republican]    [2024]          [JD Vance]
```

## 💾 Data Storage

This project aims to store information in a human-readable CSV format that can be neatly displayed in Excel.

- __Dates__ are formatted as: `Month Day, YYYY`

- __Lists__ are stored as pipe-separated strings for readability (e.g., `1788–89 | 1792`)

- Nulls are represented by the string `NA`

Inside the `data/` folder are __frozen__ CSV files—pre-scraped and processed snapshots of the dataset.  
These files are guaranteed to follow the correct structure, although they may not be the most up-to-date.

## Accessing the Dataset

You can load the dataset directly with a single line of Python:

```python
from us_presidents import fetch

df = fetch(save=True, dataset_name='presidents')
```

This downloads the frozen CSV from GitHub and saves it locally under `presidents.csv`.

You can also scrape the most recent version from Wikipedia using:

```python
df = fetch(update=True)
```

You may save and load CSVs directly with:

```python
from us_presidents import load_csv, save_csv

df = load_csv('data/us_presidents_2025.csv')
save_csv(df, filename='presidents_copy') # Saves to local directory
```

The main utilities are:

- `fetch(...)` – __loads or scrapes the dataset__
	- If `update=False` _(default)_, loads the stable snapshot from GitHub
	- If `update=True`, scrapes fresh data from Wikipedia and cleans it
	- If `save=True`, save the dataset to a `.csv`
	- `dataset_name`: filename of the `.csv`
	- `output`: optional folder or full path for saving the CSV

- `save_csv(df, filename, output=None)` – __saves to a pipe-delimited__ `.csv`

- `load_csv(filepath)` – __restores a DataFrame from a__ `.csv`

## 📊 Notebooks

Explore the `notebooks/` folder to see how the dataset was created and how it can be used.

- `cleaning_walkthrough.ipynb` – full tutorial on how the data was scraped, parsed, and cleaned

- `presidents_eda.ipynb` – examples of exploratory data analysis, using the dataset to answer real questions

You can launch them with:

```
jupyter notebook notebooks/
```

## 📦 Installation

You can clone the repo and use it locally:

```bash
git clone https://github.com/jray-8/us-presidents-dataset.git
cd us-presidents-dataset
```

Then import directly:

```python
from us_presidents import fetch
```

No `pip` installation is required. Just ensure your Python environment has:

- `pandas`

- `lxml` or `html5lib` (for `pd.read_html`)

# Folder structure

```bash
us-presidents-dataset/
├── data/                  # Frozen CSVs
├── notebooks/             # Tutorials and analysis notebooks
├── us_presidents.py       # Core data API
├── README.md              # This file
```