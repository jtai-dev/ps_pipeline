# Public Statements Data Pipeline

Data pipeline for Votesmart's Public Statement Automation project. It consists of the Extraction, Transformation and Loading (ETL) stages of the process.


## Extraction
Structured in the python package extract with sub-packages: parser and scraper. The "parser" sub-package is the storage for scripts structuring around source websites, using BeautifulSoup to parse HTML code and to scrape designated location within the file. The "scraper" sub-package is the storage for scripts that executes WebDrivers for the purpose of iterating through websites and executing the parser modules to scrape.


## Transformation
This python package (sub-package of this entire Python package) performs basic NLP tasks that will search for patterns of writing (or speech) within a text, and only extracts the necessary text with the pattern identification. All of which now is powered by spaCy modules. 

## Loading
This python package (sub-package of this entire Python package) aims to create the harvest file for the purpose of loading processed text into VoteSmart's database.
