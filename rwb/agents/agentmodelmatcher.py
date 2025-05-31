import os
import time
import json
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.duckduckgo import DuckDuckGoTools
import ollama
from pprint import pprint


QA = [
    {"question": "From which airline company has China just ordered to halt all orders?. Answer with only one word",
     "answer": "Boeing"},
    {"question": "Which Australian town did Dr Horst Herb have his practice in for many years? Answer with only a single word, the town, without any further comments.",
     "answer": "Dorrigo"},
    {"question": "Which two drugs are currently recommended for the treatment of benign intracranial hypertension? Answer with only two words, the two drugs, without any further comments.",
      "answer": ["Acetazolamide", "Topiramate"]},
    {"question": "What is the cutoff value in mm for ONSD measured with ultrasound in adult patients to detect raised ICP? Answer with only one number without units or comments",
     "answer": "5.5"},

]

def cleaned_response(response):
    """Clean the response from the model to remove unnecessary thinking steps.
    Remove the text section between <thinking> and </thinking> including the tags, and strip leading/trailing whitespace.
    Args:
        response: The response string from the model
    Returns:
        str: The cleaned response
    """
    response=response.strip()
    # Remove the <thinking>...</thinking> section
    start = response.find("<thinking>")
    end = response.find("</thinking>")
    if start != -1 and end != -1:
        response = response[end + len("</thinking>"):]
    # Remove the <thinking>...</thinking> section
    start = response.find("<think>")
    end = response.find("</think>")
    if start != -1 and end != -1:
        response = response[end + len("</think>"):]
    # Strip leading/trailing whitespace
    response = response.strip()
    return response

def list_models():
    """List available models using the Ollama API."""
    try:
        models = ollama.list()['models']
        return [model['model'] for model in models]
    except Exception as e:
        print(f"Error listing models: {str(e)}")
        return []
    
def models4agnotester():
    """tests all locally installed ollama models whether they work with agno"""
    working_models=[]
    good_models=[]
    failed_models=[]
    
    for model in list_models():
        print(f"Testing model: {model}")
        try:
            agent = Agent(
                model=Ollama(id=model),
                tools=[DuckDuckGoTools()],
                markdown=False
            )
            response = agent.run("From which airline company has China just ordered to halt all orders?. Answer with only one word")
            if cleaned_response(response.content)=="Boeing":
                good_models.append(model)
                print(f"Model {model} works with VERY WELL agno.")
            else:
                working_models.append(model)
                print(f"Model {model} works with agno.")
                print(f"Response: {response.content}")
            
        except ollama.ResponseError as e:
            failed_models.append(model)
            print(f"Error: {e}")
        except Exception as e:
            failed_models.append(model)
            print(f"Unexpected error: {e}")
        #ollama.stop(model)
    return working_models, good_models, failed_models


def test_model(model_name):
    """Test a specific model to see if it works with agno."""
    try:
        agent = Agent(
            model=Ollama(id=model_name),
            tools=[DuckDuckGoTools()],
            markdown=True
        )
        response = agent.run("Which Australian town did Dr Horst Herb have his practice in? Answer with only a single word, the town, without any further comments.")
        return response
    except ollama.ResponseError as e:
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def test_model_performance(model_name, rounds=3):
    """Test a model's performance over multiple rounds and return timing results.
    
    Args:
        model_name: The name of the model to test
        rounds: Number of test rounds (default: 3)
        
    Returns:
        A dictionary containing the model name, average time, and times for each round
    """
    results = {
        "model": model_name,
        "times": [],
        "average_time": 0,
        "correct_responses": 0
    }
    
    test_prompt = "Which Australian town did Dr Horst Herb have his practice in? Answer with only a single word, the town, without any further comments."
    
    print(f"Performance testing model {model_name} for {rounds} rounds...")
    
    for i in range(rounds):
        print(f"  Round {i+1}/{rounds}...")
        try:
            agent = Agent(
                model=Ollama(id=model_name),
                tools=[DuckDuckGoTools()],
                markdown=False
            )
            
            # Time the model's response
            start_time = time.time()
            response = agent.run(test_prompt)
            end_time = time.time()
            
            # Calculate time taken
            time_taken = end_time - start_time
            results["times"].append(time_taken)
            
            # Check if response is correct
            if response.content == "Dorrigo":
                results["correct_responses"] += 1
                print(f"  ✓ Correct response in {time_taken:.2f} seconds")
            else:
                print(f"  ✗ Incorrect response: '{response.content}' in {time_taken:.2f} seconds")
                
        except Exception as e:
            print(f"  ✗ Error in round {i+1}: {str(e)}")
            results["times"].append(None)
    
    # Calculate average time (only for successful responses)
    valid_times = [t for t in results["times"] if t is not None]
    if valid_times:
        results["average_time"] = sum(valid_times) / len(valid_times)
    
    return results


def save_performance_results(performance_results, filename="model_performance.json"):
    """Save performance results to a JSON file.
    
    Args:
        performance_results: List of dictionaries with performance data
        filename: Name of the output JSON file
    """
    try:
        with open(filename, 'w') as f:
            json.dump(performance_results, f, indent=2)
        print(f"Performance results saved to {filename}")
    except Exception as e:
        print(f"Error saving performance results: {str(e)}")


def test_model_with_questions(model_name, qa_list=QA, rounds=1):
    """Test a model with all questions in the QA list and return performance results.
    
    Args:
        model_name: The name of the model to test
        qa_list: List of question-answer pairs to test
        rounds: Number of times to run each question (default: 1)
        
    Returns:
        A dictionary containing model name, performance metrics for each question,
        and overall performance statistics
    """
    results = {
        "model": model_name,
        "questions": [],
        "total_time": 0,
        "correct_responses": 0,
        "total_responses": 0
    }
    
    print(f"Testing model {model_name} with {len(qa_list)} questions, {rounds} round(s) each...")
    
    for qa_pair in qa_list:
        question = qa_pair["question"]
        expected_answer = qa_pair["answer"]
        
        question_result = {
            "question": question,
            "expected_answer": expected_answer,
            "rounds": [],
            "correct": 0,
            "total_time": 0,
            "average_time": 0
        }
        
        # Convert single answer to list for consistent handling
        if not isinstance(expected_answer, list):
            expected_answer = [expected_answer]
        
        print(f"\nQuestion: {question}")
        print(f"Expected answer: {expected_answer}")
        
        for r in range(rounds):
            print(f"  Round {r+1}/{rounds}...")
            round_result = {
                "time": None,
                "response": None,
                "is_correct": False
            }
            
            try:
                agent = Agent(
                    model=Ollama(id=model_name),
                    tools=[DuckDuckGoTools()],
                    markdown=False
                )
                
                # Time the model's response
                start_time = time.time()
                response = agent.run(question)
                end_time = time.time()
                
                # Calculate time taken
                time_taken = end_time - start_time
                cleaned_content = cleaned_response(response.content)
                round_result["time"] = time_taken
                round_result["response"] = cleaned_content
                
                # Check if response contains any of the expected answers
                is_correct = any(answer.lower() in cleaned_content.lower() for answer in expected_answer)
                round_result["is_correct"] = is_correct
                
                if is_correct:
                    question_result["correct"] += 1
                    results["correct_responses"] += 1
                    print(f"  ✓ Correct response: '{cleaned_content}' in {time_taken:.2f} seconds")
                else:
                    print(f"  ✗ Incorrect response: '{cleaned_content}' in {time_taken:.2f} seconds")
                
                # Add time to totals
                question_result["total_time"] += time_taken
                results["total_time"] += time_taken
                
            except Exception as e:
                print(f"  ✗ Error in round {r+1}: {str(e)}")
                round_result["error"] = str(e)
                
            question_result["rounds"].append(round_result)
            results["total_responses"] += 1
        
        # Calculate average time for this question
        if question_result["rounds"]:
            valid_times = [r["time"] for r in question_result["rounds"] if r["time"] is not None]
            if valid_times:
                question_result["average_time"] = sum(valid_times) / len(valid_times)
        
        results["questions"].append(question_result)
    
    # Calculate overall accuracy
    if results["total_responses"] > 0:
        results["accuracy"] = results["correct_responses"] / results["total_responses"]
    else:
        results["accuracy"] = 0
    
    # Calculate average time per question
    if results["total_responses"] > 0:
        results["average_time"] = results["total_time"] / results["total_responses"]
    
    return results


def run_qa_tests_on_models(models, output_filename="model_qa_performance.json"):
    """Run QA tests on multiple models and save the results.
    
    Args:
        models: List of model names to test
        output_filename: Name of the JSON file to save results
    
    Returns:
        List of model results dictionaries
    """
    all_results = []
    
    print(f"\n=== Running QA tests on {len(models)} models ===\n")
    
    for model in models:
        model_results = test_model_with_questions(model, QA, rounds=3)
        all_results.append(model_results)
        
        # Print summary for this model
        print(f"\nModel: {model}")
        print(f"  Accuracy: {model_results['accuracy'] * 100:.2f}%")
        print(f"  Average time: {model_results['average_time']:.2f} seconds")
        print(f"  Correct responses: {model_results['correct_responses']}/{model_results['total_responses']}")
    
    # Save all results to a JSON file
    try:
        with open(output_filename, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nQA performance results saved to {output_filename}")
    except Exception as e:
        print(f"Error saving QA performance results: {str(e)}")
    
    return all_results


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Run the initial model testing
    workingmodels, goodmodels, failedmodels = models4agnotester()
   
    
    # # If there are good models, run the performance tests
    # if goodmodels:
    #     print("\n=== Running performance tests on good models ===\n")
    #     performance_results = []
        
    #     for model in goodmodels:
    #         result = test_model_performance(model, rounds=3)
    #         performance_results.append(result)
    #         print(f"Model: {model}")
    #         print(f"  Average time: {result['average_time']:.2f} seconds")
    #         print(f"  Correct responses: {result['correct_responses']}/3")
    #         print("")
        
    #     # Save the performance results to a JSON file
    #     save_performance_results(performance_results)
        
    #     # Print the best performing model based on average time
    #     if performance_results:
    #         best_model = min(performance_results, key=lambda x: x.get('average_time', float('inf')))
    #         print(f"Best performing model: {best_model['model']} with average time of {best_model['average_time']:.2f} seconds")
            
    #     # Run the comprehensive QA tests on the good models
    #     print("\n=== Running comprehensive QA tests on good models ===")
    #     qa_results = run_qa_tests_on_models(goodmodels, "good_models_qa_performance.json")
        
    #     # Print the best model based on accuracy
    #     if qa_results:
    #         best_accuracy_model = max(qa_results, key=lambda x: x.get('accuracy', 0))
    #         print(f"\nBest model by accuracy: {best_accuracy_model['model']} with {best_accuracy_model['accuracy'] * 100:.2f}% correct answers")
            
    # If requested, also run the comprehensive tests on working models
    run_on_working_models = True # Change to True to test all working models
    if run_on_working_models and workingmodels:
        print("\n=== Running comprehensive QA tests on all working models ===")
        all_working_results = run_qa_tests_on_models(workingmodels, "all_working_models_qa_performance.json")

