# AiJobSearch Crew

Welcome to the AiJobSearch Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

### UV Package manager

AiEnrich uses CrewAI framework, and CrewAI uses UV

> <https://docs.crewai.com/en/installation>

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux
uv tool update-shell
```

## Install crewai

> <https://docs.crewai.com/en/installation>

In `apps/crewAi` folder:

```bash
uv tool install crewai
uv tool list
crewai install
```

> uv tool install crewai --upgrade

### Customizing

- Modify `config/agents.yaml` to define your agents
- Modify `config/tasks.yaml` to define your tasks
- Modify `crew.py` to add your own logic, tools and specific args
- Modify `main.py` to add custom inputs for your agents and tasks

#### CV match (optional)

CV matching % against job offer can be enabled setting `AI_CV_MATCH=True` in your `.env` file.

Copy your cv to `apps/aiEnrich/cv/cv.txt`

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
crewai run
```

This command initializes the ai-job-search Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The ai-job-search Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the AiJobSearch Crew or crewAI.

- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
