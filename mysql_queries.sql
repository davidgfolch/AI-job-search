select count(*) from jobs where salary is not null and trim(salary)!=''  
union all
select count(*) from jobs;

select count(*) from jobs WHERE ai_enriched
union all
select count(*) from jobs;

select title, company, location, url, markdown , salary, required_technologies, business_sector, optional_technologies, relocation
from jobs WHERE ai_enriched;

select url, markdown from jobs WHERE trim(REGEXP_REPLACE(CONVERT(markdown USING utf8mb3),'\n','')) = '';
delete from jobs where trim(REGEXP_REPLACE(CONVERT(markdown USING utf8mb3),'\n','')) = '';


select * from jobs;

update jobs set ai_enriched =0, salary=NULL, required_technologies =null, optional_technologies =null,relocation =null,business_sector =null, required_languages=null; 

select * from jobs where not (required_technologies like '%Java%' or required_technologies like '%Python%' or required_technologies like '%Scala%' or required_technologies like '%Clojure%');

select title, markdown from jobs where salary is null and required_technologies is null and optional_technologies is null

delete from jobs where salary is null and required_technologies is null and optional_technologies is null



