from typing import List, Dict, Optional, Any
from agno.tools import Toolkit
from agno.utils.log import logger
import re
from Bio import Entrez
import json
import ollama
from datetime import datetime

prompt1=f"""
A pubmed query consists of one or more search terms, which can be joined with the logical operators AND, OR, and NOT.
The logical operators must be capitalized.
For example, to search for articles about "hypertension" and "aspirin", you would use the query: ```hypertension AND aspirin.```
Search  terms of more than one word need to be enclosed in "". For example, ```"heart attack"```.
Search terms can be grouped together with (). For example, ```(heart attack OR "myocardial infarction") AND aspirin.``` will search
for articles that contain (either "heart attack" or "myocardial infarction") and "aspirin".
You can tag search terms with field codes to search specific parts of the article. 
For example, ```hypertension[mesh]``` searches for the term "hypertension" in the MeSH terms (sort of a keyword thesaurus index).
To search in both title and abstract, use [tiab]. For example, ```hypertension[tiab]```.
To search for a date range, you could do this: ```("2020"[dp] : "2023"[dp]) AND "covid-19"[mesh]```. This would search for articles 
published between 2020 and 2023 that contain the term "covid-19" in the MeSH index.
Adjust the years as needed - todays actual date is {datetime.now().strftime("%Y-%m-%d")} for reference.
With these rules in mind, please construct a pubmed query for the question at the end of the text between the tags <question> </question>.
Ensure that the query is specific and relevant to the question, and unlikely to miss any relevant results.
"""

#in a small test series, prompt 2 outperformed prompt1
prompt2=f"""You translate medical questions to PubMed queries.
ANALYZE:
-PICO: Patient/Population, Intervention, Comparison, Outcome
-Extract: conditions, treatments, timeframes, demographics, study types

SYNTAX:
-MeSH: "term"[mesh], "term"[majr], "term"[mesh:noexp]
-Fields: [ti]=title, [tiab]=title/abstract, [tw]=text word, [au]=author, [pt]=publication type, [dp]=date, [la]=language, [subh]=subheading
-Boolean: AND, OR, NOT (capitalized)
-Group with (parentheses)
-Phrases use "quotes"
-Truncation: word*
-Dates: ("2018"[dp]:"3000"[dp])

FILTERS:
-Types: "review"[pt], "clinical trial"[pt], "randomized controlled trial"[pt]
-Other: "humans"[mesh], "english"[la], "free full text[sb]"

STRATEGY:
1.Core concepts→MeSH+[tiab]
2.Group synonyms with OR in (parentheses)
3.Connect concept groups with AND
4.Add filters last

OUTPUT:
1.PubMed query string (complete, copy-paste ready)
2.Brief component explanation
3.Alternative terms if needed

EXAMPLE:
Question: "SGLT2 inhibitors for heart failure in diabetics?"
Query: ("sodium glucose transporter 2 inhibitors"[mesh] OR sglt2 inhibitor*[tiab]) AND ("heart failure"[mesh] OR "heart failure"[tiab]) AND ("diabetes mellitus"[mesh] OR diabetes[tiab]) AND ("treatment outcome"[mesh] OR efficacy[tiab])

Now create an optimal PubMed query for this question:"""




# IMPORTANT: NCBI requires you to identify yourself. Replace with your actual email.
class PubMedTools(Toolkit):
    def __init__(self, email=None, max_results=10):
        """Initialize the PubMedTools class.
        Args:
            email (str): Email address for NCBI Entrez API.
            max_results (int): Maximum number of results to return from PubMed search.
        """
        # Initialize the base class
        super().__init__(name="pubmed_tools")
        if not email:
            email="test@testmail.com"
            print("WARNING: You really should set your email address for NCBI Entrez API.")
        logger.info(f"Initializing PubMedTools with email: {email}")
        if not max_results:
            max_results = 10  
        self.max_results = max_results
        self.set_email(email)
        self.register(self.generate_pubmed_query)
        self.register(self.search_pubmed)
        self.register(self.NL_pubmed_search)

    def set_email(self, email: str):
        """Set the email address for NCBI Entrez API."""
        Entrez.email = email
        logger.info(f"NCBI Entrez email set to: {email}")

    def generate_pubmed_query(self, human_language: str, use_AI: bool=True) -> str:
        """Converts a natural language query into a basic PubMed query string.

        Args:
            human_language (str): The natural language query.
            use_AI (bool): Whether to use AI for query generation. Defaults to True.
            If False, uses a basic keyword extraction method which faster but performs much worse

        Returns:
            str: A basic PubMed query string.
        """
        logger.info(f"Generating PubMed query for: {human_language}")
        if use_AI:
            # Use AI model to generate the PubMed query
            try:
                pubmed_query = self.pubmed_query_crafter(human_language)
                logger.info(f"Generated PubMed query: {pubmed_query}")
                return pubmed_query
            except Exception as e:
                logger.error(f"Failed to generate PubMed query using AI: {e}")
                return f"Error generating query: {e}"
        #else:
        # Use a basic keyword extraction method
        # This is a placeholder for a more sophisticated keyword extraction method.
        # For now, we will just use a simple regex to extract keywords.
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
        
    def pubmed_query_crafter(self, question: str, model="gemma3:4b", prompt=prompt2) -> str:
        """Crafts a PubMed query from a natural language query.
        
        Args:
            question (str): The natural language query.
            model (str): The model to use for generating the query. 
                        If not provided, defaults to "gemma3:4b" (recommended!)
            
        Returns:
            str: The crafted PubMed query.
        """
        queryprompt = f"""{prompt}
        Answer with a well formed pubmed query for the question, and nothing else.
        <question>{question}</question>
        Ensure that you will get the most relevant results for the question without missing any important information.
        Answer with the query and ONLY with the query. Do not include any additional information nor explanations.
        """
        response=ollama.generate(model=model, prompt=queryprompt)
        return response.response.strip('```json').strip('```') 
        
    
    #It actually returns a json.dumps(List[Dict]) string, but we will keep the name for compatibility
    #This is necessary to make it work as a tool for agno agents
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
                # article_info["doi"] = medline_citation.get('doi', None) # Incorrect location

                article = medline_citation.get('Article', {})

                # --- REMOVE TEMPORARY DEBUGGING --- 
                # print(f"--- Debugging PMID: {article_info.get('pmid')} ---")
                # article_id_list_raw = article.get('ArticleIdList')
                # if article_id_list_raw is None:
                #     print(f"!!! ArticleIdList is None for PMID {article_info.get('pmid')}. Printing MedlineCitation: !!!")
                #     import pprint # Use pprint for better readability
                #     pprint.pprint(medline_citation)
                # --- END REMOVE TEMPORARY DEBUGGING ---

                # Extract DOI - Initialize to None
                article_info["doi"] = None

                # Attempt 1: Extract DOI from ArticleIdList
                article_id_list = article.get('ArticleIdList', [])
                if isinstance(article_id_list, list):
                    for article_id in article_id_list:
                        try:
                            if hasattr(article_id, 'attributes') and article_id.attributes.get('IdType') == 'doi':
                                doi_value = str(article_id).strip()
                                if doi_value:
                                    article_info["doi"] = doi_value
                                    break # Found DOI in ArticleIdList
                        except Exception as e:
                            logger.warning(f"Error processing ArticleId {article_id} for PMID {article_info.get('pmid')}: {e}")

                # Attempt 2: Extract DOI from ELocationID (if not found in ArticleIdList)
                if not article_info["doi"]:
                    elocation_ids = article.get('ELocationID', [])
                    if isinstance(elocation_ids, list):
                        for eloc_id in elocation_ids:
                            try:
                                if hasattr(eloc_id, 'attributes') and eloc_id.attributes.get('EIdType') == 'doi' and eloc_id.attributes.get('ValidYN', 'N') == 'Y':
                                    doi_value = str(eloc_id).strip()
                                    if doi_value:
                                        article_info["doi"] = doi_value
                                        break # Found DOI in ELocationID
                            except Exception as e:
                                logger.warning(f"Error processing ELocationID {eloc_id} for PMID {article_info.get('pmid')}: {e}")

                # --- REMOVE TEMPORARY DEBUGGING --- 
                # if not article_info["doi"]: 
                #     print(f"--- DOI still None for PMID: {article_info.get('pmid')} ---") 
                # --- END REMOVE TEMPORARY DEBUGGING ---


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
            return '[]' # Return empty JSON array string on error
        
    #It actually returns a json.dumps(List[Dict]) string, but we will keep the name for compatibility
    #This is necessary to make it work as a tool for agno agents    
    def NL_pubmed_search(self, human_language: str, max_results=10, email=None) -> List[Dict[str, Any]]:
        """Searches PubMed using a natural language query and returns results.
        This tool coverts the natural language query into a PubMed query first
        and then performs the search.
        If this tool returns 

        Args:
            human_language (str): The natural language query.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with publication details.
        """
        self.max_results = max_results
        logger.info(f"Searching PubMed with natural language query: {human_language}")
        pubmed_query = self.generate_pubmed_query(human_language)
        if not pubmed_query or "Error" in pubmed_query:
            logger.error(f"Invalid PubMed query generated: {pubmed_query}")
            return []
        return self.search_pubmed(pubmed_query, max_results=self.max_results)
    


def test_performance(model="gemma3:4b"):
    """Test the performance of the PubMed query generation.
    
    Args:
        model (str): The model to use for generating the query.
        prompt (str): The prompt to use for generating the query.

    Returns:
        None
    """
    from collections import defaultdict

    pm = PubMedTools(email='hherb@dorrigomedical.com.au')
    question = "What are the latest findings on the efficacy of mRNA vaccines against COVID-19 variants?"

    # Data structure to hold results per prompt
    # { "prompt_key": {"total_api_results": count, "title_counts": {title: count}} }
    prompt_results = {
        "prompt1": {"total_api_results": 0, "title_counts": defaultdict(int)},
        "prompt2": {"total_api_results": 0, "title_counts": defaultdict(int)}
    }
    prompt_map = {"prompt1": prompt1, "prompt2": prompt2} # Map keys to actual prompt content

    print("Running queries for prompt comparison...")
    print(f"Question: {question}")
    print("-" * 80)

    for prompt_key, prompt_content in prompt_map.items():
        print(f"Processing {prompt_key}...")
        for i in range(10): # Run 10 times per prompt as in original code
            print(f"  Iteration {i+1}/10")
            query = pubmed_query_crafter(question, model="gemma3:4b", prompt=prompt_content)
            print(f"    Generated Query: {query[:100]}...") # Print truncated query
            results_str = pm.search_pubmed(query, max_results=3)

            try:
                # Ensure results is a valid JSON string before loading
                if isinstance(results_str, str) and results_str.strip().startswith('['):
                    resultlist = json.loads(results_str)
                    num_results = len(resultlist)
                    print(f"    API returned {num_results} results.")
                    prompt_results[prompt_key]["total_api_results"] += num_results

                    for result in resultlist:
                        title = result.get('title')
                        if title:
                            prompt_results[prompt_key]["title_counts"][title] += 1
                        else:
                            pmid = result.get('pmid', 'N/A')
                            print(f"    Warning: Result with PMID {pmid} has no title.")
                elif not results_str:
                     print("    API returned no results (empty string or None).")
                else:
                    print(f"    Warning: search_pubmed did not return a valid JSON list string. Got: {results_str}")

            except json.JSONDecodeError as e:
                print(f"    Error decoding JSON response: {e}")
                print(f"    Response string: {results_str}")
            except Exception as e:
                 print(f"    An unexpected error occurred processing results: {e}")

        print(f"Finished processing {prompt_key}.")
        print("-" * 80)


    # --- Report Generation ---
    print("\nComparison Report")
    print("=" * 80)

    # Combine title counts and calculate totals
    all_titles_data = []
    all_titles = set(prompt_results["prompt1"]["title_counts"].keys()) | set(prompt_results["prompt2"]["title_counts"].keys())

    for title in all_titles:
        count1 = prompt_results["prompt1"]["title_counts"].get(title, 0)
        count2 = prompt_results["prompt2"]["title_counts"].get(title, 0)
        total_count = count1 + count2
        all_titles_data.append({
            "title": title,
            "prompt1_count": count1,
            "prompt2_count": count2,
            "total_count": total_count
        })

    # Sort by total count descending
    all_titles_data.sort(key=lambda x: x["total_count"], reverse=True)

    # Print Summary Stats
    print("Summary:")
    print(f"  Prompt 1 Total API Results: {prompt_results['prompt1']['total_api_results']}")
    print(f"  Prompt 2 Total API Results: {prompt_results['prompt2']['total_api_results']}")
    print("-" * 80)

    # Print Table Header
    # Determine max title width for formatting (optional, but improves readability)
    max_title_len = max(len(item['title']) for item in all_titles_data) if all_titles_data else 40
    max_title_len = min(max_title_len, 80) # Cap width

    header = f"{'Title'.ljust(max_title_len)} | {'Prompt 1':<10} | {'Prompt 2':<10} | {'Total':<7}"
    print(header)
    print("-" * len(header))

    # Print Table Rows
    for item in all_titles_data:
        title_truncated = item['title'][:max_title_len] + ('...' if len(item['title']) > max_title_len else '')
        row = f"{title_truncated.ljust(max_title_len)} | {str(item['prompt1_count']).ljust(10)} | {str(item['prompt2_count']).ljust(10)} | {str(item['total_count']).ljust(7)}"
        print(row)

    print("=" * 80)


if __name__=="__main__":
    from pprint import pprint
    pm=PubMedTools(email="test@testmail.com")
    question="What are the latest findings on the efficacy of mRNA vaccines against COVID-19 variants?"
    result =pm.NL_pubmed_search(question, max_results=10)
    if not result:
        print("No results found.")
        exit(1)
    jsonresult=json.loads(result)
    for entry in jsonresult:
        print(f"PMID: {entry['pmid']}")
        print(f"Title: {entry['title']}")
        print(f"DOI: {entry['doi']}")
        print(f"Publication Date: {entry['publication_date']}")
        print("-" * 80)
