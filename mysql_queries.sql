select count(*) from jobs where salary is not null and trim(salary)!=''  
union all
select count(*) from jobs;

select count(*) from jobs WHERE ai_enriched
union all
select count(*) from jobs;

select count(*) from jobs;

select * from jobs WHERE not ai_enriched and not ignored;

select title, company, location, url, markdown , salary, required_technologies, business_sector, optional_technologies
from jobs WHERE ai_enriched;

select url, markdown from jobs WHERE trim(REGEXP_REPLACE(CONVERT(markdown USING utf8mb3),'\n','')) = '';
delete from jobs where trim(REGEXP_REPLACE(CONVERT(markdown USING utf8mb3),'\n','')) = '';


select * from jobs where jobs.web_page='Linkedin' order by created DESC;

update jobs set web_page='Linkedin' where url like '%linkedin%';

update jobs set ai_enriched =0, salary=NULL, required_technologies =null, optional_technologies =null,business_sector =null, required_languages=null; 

select * from jobs where not (required_technologies like '%Java%' or required_technologies like '%Python%' or required_technologies like '%Scala%' or required_technologies like '%Clojure%');

select title, markdown from jobs where salary is null and required_technologies is null and optional_technologies is null

delete from jobs where not ignored and not applied and DATE(created) > DATE_SUB(CURDATE(), INTERVAL 1 DAY) and comments is null;

select count(*) from jobs

select * from jobs where not ignored and not applied and DATE(created) < DATE_SUB(CURDATE(), INTERVAL 1 DAY) and comments is null

select * from jobs where required_technologies rlike '(java|python|scala,clojure)';

select id from jobs where title = 'Remote Coding Expertise for AI Training - Tier 3 Non US'

select * from jobs where url like '%glassdoor%'

select * from jobs where  DATE(created) < DATE_SUB(CURDATE(), INTERVAL 7 DAY) and not (seen or `like` or ignored or applied or discarded or closed or  
interview_rh or interview or interview_tech or interview_technical_test or interview_technical_test_done)

select r.counter, r.ids, r.title, r.company
from (select count(*) as counter, GROUP_CONCAT(CAST(id as CHAR(50)) SEPARATOR ',') as ids, title, company 
		from jobs 
		where DATE(created) < DATE_SUB(CURDATE(), INTERVAL 7 DAY) and not (seen or `like` or ignored or applied or discarded or closed or
				interview_rh or interview or interview_tech or interview_technical_test or interview_technical_test_done)
		group by title, company
	) as r
where r.counter>1
order by r.counter desc

delete from jobs where id in (2426 , 2308)

select title, company from jobs where id in (8505, 8518)

select * from jobs where id = 18104

select id, title, company from jobs where jobId = 4081331701

update jobs set salary=NULL where 
salary LIKE '%Salary range not specified%' or
salary like '%Salario a convenir%' or 
salary like '%Not specified%' or 
salary like '%No salary information%'

update jobs set
applied = 1,
comments ='Applied in https://job-boards.greenhouse.io/outlier/jobs/4490427005?gh_src=e2e12c345us'
where id = 4147


select r.counter, r.ids, r.title, r.company, r.max_created, created_ids
from (select count(*) as counter,
            GROUP_CONCAT(CAST(id as CHAR(50)) SEPARATOR ',') as ids,
            max(created) as max_created,
            GROUP_CONCAT(CAST(created as CHAR(50)) SEPARATOR ',') as created_ids,
            title, company
        from jobs
        where not (seen or `like` or ignored or applied or discarded or
                    closed or interview_rh or interview or interview_tech or
                    interview_technical_test or interview_technical_test_done)
        group by title, company
    ) as r
where r.counter>1
order by r.counter desc, r.title, r.company, r.max_created desc

select title, company, applied, modified from jobs where applied order by modified desc;

select ai_enrich_error from jobs where ai_enrich_error is not null;
update jobs set ai_enriched=False, ai_enrich_error = NULL where ai_enrich_error is not null;

select id, title, company from jobs where company like '%GT Motive Spain%';


update jobs set ignored = true where (ignored is null or ignored = FALSE) and (company = 'Refonte Learning' or company = 'Refonte Technologies');

-- update jobs set comments=null, scrapper_enriched=0
-- where scrapper_enriched and comments like '%Salary scrapped from Glassdoor: https://www.glassdoor.com/Salary/Braintrust%'
-- or salary like '%From glassdoor: Sr. Software Engineer - $136K-$185K%';

update jobs set salary=null, scrapper_enriched=0
where salary = 'From glassdoor: Sr. Software Engineer - $136K-$185K';

select comments from jobs 
where comments like '%From glassdoor: Sr. Software Engineer - $136K-$185K%';

