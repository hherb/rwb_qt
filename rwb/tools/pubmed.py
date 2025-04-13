from typing import List, Dict, Optional, Any
from agno.tools import Toolkit
from agno.utils.log import logger
import re
from Bio import Entrez
import json


# IMPORTANT: NCBI requires you to identify yourself. Replace with your actual email.


class PubMedTools(Toolkit):
    def __init__(self, email, max_results=10):
        """Initialize the PubMedTools class.
        Args:
            email (str): Email address for NCBI Entrez API.
            max_results (int): Maximum number of results to return from PubMed search.
        """
        # Initialize the base class
        super().__init__(name="pubmed_tools")
        self.max_results = max_results
        self.set_email(email)
        self.register(self.generate_pubmed_query)
        self.register(self.search_pubmed)
        self.register(self.NL_pubmed_search)

    def set_email(self, email: str):
        """Set the email address for NCBI Entrez API."""
        Entrez.email = email
        logger.info(f"NCBI Entrez email set to: {email}")

    def generate_pubmed_query(self, human_language: str) -> str:
        """Converts a natural language query into a basic PubMed query string.

        Args:
            human_language (str): The natural language query.

        Returns:
            str: A basic PubMed query string.
        """
        logger.info(f"Generating PubMed query for: {human_language}")
        try:
            # Basic implementation: Treat keywords as essential terms.
            # Remove common stop words (a more comprehensive list could be used).
            stop_words = set(["a", "an", "the", "in", "on", "at", "for", "to", "of", "is", "are", "was", "were", "and", "or", "find", "search", "articles", "about", "papers"])
            
            # Simple tokenization and stop word removal
            words = re.findall(r'\b\w+\b', human_language.lower())
            keywords = [word for word in words if word not in stop_words]
            
            # Combine keywords with [Title/Abstract] tag for basic search
            # A more advanced version could identify MeSH terms, publication types, etc.
            if not keywords:
                logger.warning("No keywords extracted from the human language query.")
                return ""
                
            pubmed_query = " AND ".join([f"{keyword}[Title/Abstract]" for keyword in keywords])
            
            logger.info(f"Generated PubMed query: {pubmed_query}")
            return pubmed_query
            
        except Exception as e:
            logger.error(f"Failed to generate PubMed query: {e}")
            return f"Error generating query: {e}"

    def search_pubmed(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Searches PubMed with the given query and returns a list of results.

        Args:
            query (str): The PubMed query string.
            max_results (int): The maximum number of results to return. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing details of a publication
                                  (pmid, publication_date, title, authors, journal, abstract).
                                  Returns an empty list if no results or an error occurs.
        """
        logger.info(f"Searching PubMed for: {query} (max_results={max_results})")
        results_list = []
        try:
            # Search PubMed
            handle = Entrez.esearch(db="pubmed", term=query, retmax=str(max_results))
            search_results = Entrez.read(handle)
            handle.close()
            
            id_list = search_results["IdList"]
            if not id_list:
                logger.info("No results found.")
                return []

            # Fetch details for the found PMIDs
            handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="xml")
            records = Entrez.read(handle)
            handle.close()

            # Parse records
            for record in records.get('PubmedArticle', []):
                # Initialize dictionary with None values
                article_info = {
                    "pmid": None,
                    "publication_date": None,
                    "title": None,
                    "authors": [],
                    "journal": None,
                    "abstract": None,
                    "doi": None
                }

                # Extract PMID
                medline_citation = record.get('MedlineCitation', {})
                article_info["pmid"] = medline_citation.get('PMID', None)
                article_info["doi"] = medline_citation.get('doi', None)

                article = medline_citation.get('Article', {})
                
                # Extract Title
                article_info["title"] = article.get('ArticleTitle', None)

                # Extract Abstract
                abstract_data = article.get('Abstract', {})
                if abstract_data:
                    abstract_texts = abstract_data.get('AbstractText', [])
                    if isinstance(abstract_texts, list):
                         # Handle structured abstracts (e.g., BACKGROUND:, OBJECTIVE:)
                        full_abstract = ""
                        for part in abstract_texts:
                            if isinstance(part, str):
                                full_abstract += part + " "
                            elif hasattr(part, 'attributes') and part.attributes.get('Label'):
                                full_abstract += f"{part.attributes['Label']}: {str(part)} "
                            else:
                                full_abstract += str(part) + " "
                        article_info["abstract"] = full_abstract.strip() if full_abstract else None
                    elif isinstance(abstract_texts, str): # Handle simple string abstract
                         article_info["abstract"] = abstract_texts
                
                # Extract Authors
                author_list = article.get('AuthorList', [])
                authors = []
                for author in author_list:
                    last_name = author.get('LastName', '')
                    fore_name = author.get('ForeName', '')
                    initials = author.get('Initials', '')
                    if last_name: # Prefer full name if available
                         name = f"{fore_name} {last_name}" if fore_name else last_name
                         authors.append(name.strip())
                    elif initials: # Fallback to initials if no last name
                         authors.append(initials)
                article_info["authors"] = authors if authors else None


                # Extract Journal and Publication Date
                journal_info = article.get('Journal', {})
                article_info["journal"] = journal_info.get('Title', None)
                
                journal_issue = journal_info.get('JournalIssue', {})
                pub_date_info = journal_issue.get('PubDate', {})
                
                pub_date_str = ""
                if 'Year' in pub_date_info:
                    pub_date_str += pub_date_info['Year']
                    if 'Month' in pub_date_info:
                        pub_date_str += f"-{pub_date_info['Month']}"
                        if 'Day' in pub_date_info:
                            pub_date_str += f"-{pub_date_info['Day']}"
                elif 'MedlineDate' in pub_date_info: # Fallback for older formats
                    pub_date_str = pub_date_info['MedlineDate']
                
                article_info["publication_date"] = pub_date_str if pub_date_str else None

                results_list.append(article_info)

            logger.info(f"Successfully retrieved {len(results_list)} results.")
            return json.dumps(results_list)

        except Exception as e:
            logger.error(f"Failed to search PubMed or parse results: {e}")
            # Optionally return the error message or specific error structure
            # return [{"error": str(e)}] 
            return [] # Return empty list on error for simplicity
        
        
    def NL_pubmed_search(self, human_language: str, ax_results=10) -> List[Dict[str, Any]]:
        """Searches PubMed using a natural language query and returns results.
        This tool coverts the natural language query into a PubMed query first
        and then performs the search.

        Args:
            human_language (str): The natural language query.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with publication details.
        """
        logger.info(f"Searching PubMed with natural language query: {human_language}")
        pubmed_query = self.generate_pubmed_query(human_language)
        if not pubmed_query or "Error" in pubmed_query:
            logger.error(f"Invalid PubMed query generated: {pubmed_query}")
            return []
        return self.search_pubmed(pubmed_query, max_results=self.max_results)

# Example Usage (for testing purposes)
if __name__ == '__main__':
    pubmed_tool = PubMedTools(email="testing@mymail.com", max_results=5)
    query1 = "Find articles about lung cancer treatment using immunotherapy"
    print(f"Human: {query1}")
    print(f"PubMed: {pubmed_tool.generate_pubmed_query(query1)}")

    query2 = "Search for papers on CRISPR gene editing in mice"
    print(f"Human: {query2}")
    print(f"PubMed: {pubmed_tool.generate_pubmed_query(query2)}")

    # Test the new search function
    test_query = pubmed_tool.generate_pubmed_query("CRISPR gene editing review")
    if test_query and "Error" not in test_query:
        print(f"\nSearching PubMed for: {test_query}")
        search_results = pubmed_tool.search_pubmed(test_query, max_results=2)
        if search_results:
            print(f"Found {len(search_results)} results:")
            for i, result in enumerate(search_results):
                print(f"\n--- Result {i+1} ---")
                print(f"  PMID: {result.get('pmid')}")
                print(f"  Date: {result.get('publication_date')}")
                print(f"  Title: {result.get('title')}")
                print(f"  Authors: {', '.join(result.get('authors', [])) if result.get('authors') else 'N/A'}")
                print(f"  Journal: {result.get('journal')}")
                # Limit abstract length for display
                abstract = result.get('abstract', '') or ""
                print(f"  Abstract: {abstract[:200]}{'...' if len(abstract) > 200 else ''}")
        else:
            print("No search results returned or error occurred.")
    else:
        print(f"Could not generate a valid PubMed query to test search: {test_query}")

    print("Testing PubMedTools natural language search:")
    nl_query = "Find articles about the effects of caffeine on sleep"
    print(f"Human: {nl_query}")
    nl_results = pubmed_tool.NL_pubmed_search(nl_query)
    if nl_results:
        print(f"Found {len(nl_results)} results:")
        for i, result in enumerate(nl_results):
            print(f"\n--- Result {i+1} ---")
            print(f"  PMID: {result.get('pmid')}")
            print(f"  Date: {result.get('publication_date')}")
            print(f"  Title: {result.get('title')}")
            print(f"  Authors: {', '.join(result.get('authors', [])) if result.get('authors') else 'N/A'}")
            print(f"  Journal: {result.get('journal')}")
            # Limit abstract length for display
            abstract = result.get('abstract', '') or ""
            print(f"  Abstract: {abstract[:200]}{'...' if len(abstract) > 200 else ''}")
    else:
        print("No results found or error occurred.")
