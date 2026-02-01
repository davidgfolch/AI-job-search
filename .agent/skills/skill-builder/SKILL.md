---
name: skill_builder
description: Use this skill to create new skills for the agent. This skill automates the creation of the skill directory and the boilerplate SKILL.md file.
---

# Skill Builder Instructions

Follow these steps to create a new skill for the agent.

1.  **Understand the Request**: Identify the name of the skill the user wants to create and its purpose/description. If the name is not clear, ask the user or propose a name (kebab-case preferred, e.g., `feature-implementer`).

2.  **Create Skill Directory**:
    -   Determine the path: `.agent/skills/<skill_name>` (where `<skill_name>` is the name of the new skill).
    -   Create the directory if it does not exist.

3.  **Create SKILL.md**:
    -   Create a file named `SKILL.md` inside the new directory.
    -   Populate it with the following template:

    ```markdown
    ---
    name: <skill_name>
    description: <short description of what the skill does>
    ---
    # <Skill Name> Instructions

    <Detailed instructions on how to perform the skill. Break it down into steps.>
    
    ## Usage
    <Examples of when to use this skill>
    ```

4.  **Optional: Create Support Directories**:
    -   If the skill likely needs scripts or examples, create `scripts/` or `examples/` directories within the skill folder.

5.  **Notify User**:
    -   Inform the user that the skill scaffold has been created at `.agent/skills/<skill_name>`.
    -   Ask if they want to populate the detailed instructions now.
