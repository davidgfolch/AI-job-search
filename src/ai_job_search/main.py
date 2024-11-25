#!/usr/bin/env python
import sys
import warnings

from ai_job_search.crew import AiJobSearch, AiJobSearchFlow
# from ai_job_search.inputs import INPUTS

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
        AiJobSearch().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs={})
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AiJobSearch().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    try:
        AiJobSearch().crew().test(
            n_iterations=int(sys.argv[1]),
            openai_model_name=sys.argv[2],
            inputs={})
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")
