#!/usr/bin/env python
import sys
import warnings

from .dataExtractor import DataExtractor
from .crew import AiJobSearchFlow

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


def run():
    """
    Run the crew.
    """
    # AiJobSearch().crew().kickoff()
    AiJobSearchFlow().kickoff()
    # AiJobSearch().crew().kickoff(inputs=INPUTS)


def train():
    """
    Train the crew for a given number of iterations.
    """
    try:
        # Default values for testing
        n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        filename = sys.argv[2] if len(sys.argv) > 2 else 'default_training.txt'
        
        DataExtractor().crew().train(
            n_iterations=n_iterations,
            filename=filename,
            inputs={})
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        # Default value for testing
        task_id = sys.argv[1] if len(sys.argv) > 1 else 'default_task'
        
        DataExtractor().crew().replay(task_id=task_id)
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test_crew():
    """
    Test the crew execution and returns the results.
    """
    try:
        n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        model_name = sys.argv[2] if len(sys.argv) > 2 else 'gpt-3.5-turbo'
    except (ValueError, IndexError):
        n_iterations = 1
        model_name = 'gpt-3.5-turbo'
    
    try:
        DataExtractor().crew().test(
            n_iterations=n_iterations,
            openai_model_name=model_name,
            inputs={})
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")
