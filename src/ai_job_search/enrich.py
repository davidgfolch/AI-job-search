import traceback
from typing import Optional
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery
from ai_job_search.tools.stopWatch import StopWatch
from ai_job_search.tools.terminalColor import printHR, red, yellow
from ai_job_search.tools.util import removeExtraEmptyLines


DEFAULT_CHAT_TYPE = ChatOpenAI
port = 11434
baseUrl = f"http://localhost:{port}"
hostArgsV1 = {"base_url": baseUrl + "/v1", "api_key": "xx"}
if DEFAULT_CHAT_TYPE == ChatOpenAI:
    # ChatOllama without uri /v1, ChatOpenAI with uri /v1
    baseUrl = baseUrl + "/v1"

hostArgs = {"base_url": baseUrl, "api_key": "xx", "verbose": True}

SALARY_DESCRIPTION = "Salary or salary range amount: if specified"
REQUIRED_SKILLS_DESCRIPTION = "Required skills: languages, frameworks, \
libraries, etc. (a string containing a list separated by commas)."
OPTIONAL_SKILLS_DESCRIPTION = "Optional skills: languages, frameworks, \
libraries, etc. (a string containing a list separated by commas)."

model = ChatOpenAI(
    model="llama3.2",
    # model="nuextract",
    # model="ollama/deepseek-r1:8b",  # no GPU inference
    temperature=0,
    **hostArgs)


# The json output must have the following fields and structure:
# {{
#   "salary": "",
#   "required_technologies": "",
#   "optional_technologies": ""
# }}

class JsonStructure(BaseModel):
    salary: Optional[str] = Field(description=SALARY_DESCRIPTION)
    required_skills: Optional[str] = Field(
        description=REQUIRED_SKILLS_DESCRIPTION)
    optional_skills: Optional[str] = Field(
        description=OPTIONAL_SKILLS_DESCRIPTION)


parser = JsonOutputParser(pydantic_object=JsonStructure)

parserInstructions = parser.get_format_instructions()

template = f"""Extract the following information from the job offer \
description:
- {SALARY_DESCRIPTION}
- {REQUIRED_SKILLS_DESCRIPTION}
- {OPTIONAL_SKILLS_DESCRIPTION}""" + """

{format_instructions}\nJob offer description:\n{query}\n"""

prompt = PromptTemplate(
    template=template,
    input_variables=["query"],
    partial_variables={
        "format_instructions": parserInstructions},
)

chain = prompt | model | parser


def run():
    with MysqlUtil() as mysql:
        count, jobs = mysql.getJobsForAiEnrichment()
        print(yellow(f'{count} jobs to be ai_enriched...'))
        if count > 0:
            print(f"selectedChatType={DEFAULT_CHAT_TYPE}, baseUrl={baseUrl}")
            print(f'Parser format instructions:\n{parserInstructions}')
            print(f'{prompt}')
        stopWatch = StopWatch()
        for idx, job in enumerate(jobs):
            stopWatch.start()
            try:
                id = job[0]
                title = job[1]
                company = job[3]
                printHR(yellow)
                print(
                    yellow([f'Job {idx+1}/{count} ',
                           'id={id}, title={title}, company={company}']))
                markdown = job[2]
                # DB markdown blob decoding
                markdown = markdown.decode("utf-8")
                markdown = removeExtraEmptyLines(f'# {title}\n{markdown}')
                print(f'{markdown}')
                res: JsonStructure = chain.invoke({"query": markdown})
                print(yellow(f'Response ({type(res)}):\n{res}'))
                if res is not None:
                    mysql.updateFromAI(id, company, res, 'skills')
            except Exception as ex:
                print(red(traceback.format_exc()))
                print(yellow("Skipping! (ai_enrich_error set in DB)"))
                MAX_AI_ENRICH_ERROR = 500
                params = {'ai_enrich_error': str(ex)[:MAX_AI_ENRICH_ERROR],
                          'ai_enriched': True}
                query, params = updateFieldsQuery([id], params)
                mysql.executeAndCommit(query, params)
            stopWatch.end()
            print(yellow(f'Total processed jobs: {idx+1}/{count}'))
            print()
            print()
        print(yellow(''*60))
        print(yellow('ALL ROWS PROCESSES!'))
        print(yellow(''*60))


if __name__ == '__main__':
    run()
