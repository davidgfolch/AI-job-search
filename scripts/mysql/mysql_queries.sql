select count(*) from jobs where salary is not null and trim(salary)!=''  
union all
select count(*) from jobs;

select count(*) from jobs WHERE ai_enriched=False
union all
select count(*) from jobs;

select count(*) from jobs;

select * from jobs WHERE not ai_enriched and not ignored;

-- select title, company, location, url, markdown , salary, required_technologies, optional_technologies from jobs
-- TODO: 
update jobs set ai_enriched=1, flagged=1, comments='AI enrichment hangs on this job'
update jobs set ai_enriched=0, salary=null
-- WHERE ai_enriched and required_technologies like '%\\\\u%';
-- where DATE(created) >= DATE_SUB(CURDATE(), INTERVAL 48 HOUR)
-- where id=XXXXXXXX



select url, markdown from jobs WHERE trim(REGEXP_REPLACE(CONVERT(markdown USING utf8mb3),'\n','')) = '';
delete from jobs where trim(REGEXP_REPLACE(CONVERT(markdown USING utf8mb3),'\n','')) = '';

select * from jobs where jobs.company='Michael Page' and applied order by created DESC;

select * from jobs where jobs.web_page='Tecnoempleo' order by created DESC;
delete from jobs where jobs.web_page='Tecnoempleo';

update jobs set web_page='Linkedin' where url like '%linkedin%';


select id, ai_enriched, title, ai_enrich_error, modified from jobs where ai_enrich_error is not null and DATE(created) > DATE_SUB(CURDATE(), INTERVAL 7 DAY) and not (discarded or ignored);
update jobs set ai_enriched=False, ai_enrich_error = NULL where ai_enrich_error is not null and DATE(created) > DATE_SUB(CURDATE(), INTERVAL 2 DAY) and not (discarded or ignored);
update jobs set ai_enriched=False where ai_enriched and DATE(created) > DATE_SUB(CURDATE(), INTERVAL 24 HOUR);

select id, cv_match_percentage, title, ai_enriched, ai_enrich_error, modified from jobs where cv_match_percentage = -1 and DATE(created) > DATE_SUB(CURDATE(), INTERVAL 7 DAY);

SELECT url FROM jobs WHERE web_page='Indeed';
update jobs set ai_enriched=0, ai_enrich_error=null WHERE ai_enrich_error is not null;

select id, company from jobs where applied order by created desc

select title, created, ai_enriched, ai_enrich_error, salary, required_technologies, optional_technologies
from jobs
/*update jobs set ai_enriched =0, ai_enrich_error=NULL, salary=NULL, required_technologies =null, optional_technologies =null*/
where DATE(created) > DATE_SUB(CURDATE(), INTERVAL 12 HOUR) and ai_enriched and salary is not null;

select * from jobs where not (required_technologies like '%Java%' or required_technologies like '%Python%' or required_technologies like '%Scala%' or required_technologies like '%Clojure%');

select title, markdown from jobs where salary is null and required_technologies is null and optional_technologies is null


DELETE 
-- SELECT title, markdown, created 
from jobs where not ignored and not applied and DATE(created) > DATE_SUB(CURDATE(), INTERVAL 7 DAY) and comments is NULL AND web_page = 'Infojobs';

select count(*) from jobs

select * from jobs where not ignored and not applied and DATE(created) < DATE_SUB(CURDATE(), INTERVAL 1 DAY) and comments is null

select id,title,company,created, applied, flagged, seen
from jobs
where (DATE(created) < DATE_SUB(CURDATE(), INTERVAL 20 DAY) and not applied and not flagged and not seen) or
      (DATE(created) < DATE_SUB(CURDATE(), INTERVAL 30 DAY) and not applied and not flagged)
order by created desc

select id, created, title, applied, ignored
from jobs where DATE(created) < DATE_SUB(CURDATE(), INTERVAL 10 DAY) and applied is null or applied=False;
select * from jobs where DATE(created) < DATE_SUB(CURDATE(), INTERVAL 40 DAY) and not applied and not ignored;


select * from jobs where required_technologies rlike '(java|python|scala|clojure)';

select id, title, company, markdown, created from jobs 
update jobs set ignored=true  
where title rlike '(SAP|ABAP|HANA|COBOL|DevOps)' and not (ignored or applied or closed)
order by created desc;

select * from jobs where title like 'Senior Full Stack Developer (Java/Angular) - 100% Remoto'

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

select * from jobs where id = 69103

select id, title, company from jobs where jobId = 4081331701
select id, title, company, markdown from jobs where id = 32998;

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

select id, title, company, applied, modified, ignored from jobs where ignored order by modified desc limit 100;
select id, title, company, applied, created, merged, modified, ignored from jobs where merged is not null order by merged desc;
update jobs set merged=null where created=merged;

select id, title from jobs where date(modified)=CURDATE()  order by modified desc
update jobs set ignored=null where id=261283;

select `id`, title from  jobs where jobId=4313375111


SELECT id, salary, title, company
FROM jobs
WHERE (lower(required_technologies) rlike 'java([^script]|$)|spring|python|scala([^bility]|$)|clojure' or lower(title) rlike 'java([^script]|$)|spring|python|scala([^bility]|$)|clojure' or lower(CONVERT(markdown USING utf8mb4) COLLATE utf8mb4_0900_ai_ci) rlike 'java([^script]|$)|spring|python|scala([^bility]|$)|clojure')
 and DATE(created) >=     DATE_SUB(CURDATE(),  INTERVAL 1 DAY)
 and (ai_enriched)
 and not (seen or ignored or applied or discarded or closed)
ORDER BY salary desc,  created  desc



update jobs set salary=null where salary = 'Salario no disponible' or salary = 'Paquete retributivo muy competitivo acorde a la valía del candidato'
or salary = 'Salario a convenir';

/* View total # applied job offers and total # of them closed or discarded*/
select
	(select count(jobId) from jobs where applied and not discarded and not closed) as 'applied and not discarded or closed',
	(select count(jobId) from jobs where applied and (discarded or closed)) as 'applied discarded or closed';
/* View applied job offers by company, followed by applied and closed or discarded ones */
select j1.id, j1.title, j1.company as applied, j2.company as c2, isnull(j2.company) as closedOrDiscarded
from jobs j1 
left join jobs j2 on j2.id=j1.id and not j2.closed and not j2.discarded
where j1.applied
order by closedOrDiscarded, j1.company;


select distinct(company) from jobs where applied and not discarded and not closed;

select id, title, company, markdown from jobs where company like '%Aaron%' and title like 'Java spark%' and applied;


update jobs set ignored = true where (ignored is null or ignored = FALSE) and (company = 'Refonte Learning' or company = 'Refonte Technologies');

-- update jobs set comments=null, scrapper_enriched=0
-- where scrapper_enriched and comments like '%Salary scrapped from Glassdoor: https://www.glassdoor.com/Salary/Braintrust%'
-- or salary like '%From glassdoor: Sr. Software Engineer - $136K-$185K%';

update jobs set salary=null, scrapper_enriched=0
where salary = 'From glassdoor: Sr. Software Engineer - $136K-$185K';

select comments from jobs 
where comments like '%From glassdoor: Sr. Software Engineer - $136K-$185K%';

UPDATE jobs SET company='Aditelsa'
WHERE id=31097

select id,  title, salary, required_technologies, optional_technologies, 
company, client, comments, flagged, `like`, ignored, seen, applied, discarded, closed, 
interview_rh, interview, interview_tech, interview_technical_test, interview_technical_test_done, 
ai_enriched, easy_apply
    from jobs where id in (30755, 31097)
    order by created asc
    
-- Statistics
SELECT CONVERT(created,DATE) as createdDate, CONVERT(created,TIME) as createdTime from jobs order by created;
select s.createdDate, s.createdTime
from (SELECT CONVERT(created,DATE) as createdDate, CONVERT(created,TIME) as createdTime from jobs order by created) as s
group by createdDate;
 
 SELECT CONVERT(created,TIME) as timeCreated, count(*) as total
from jobs
group by timeCreated
order by timeCreated

SELECT HOUR(created) AS hour, max(web_page), COUNT(*) AS total
FROM jobs GROUP BY HOUR(created), web_page
order by web_page, hour


select concat('Applied: ',count(id)) as count from jobs where applied union all
select concat('Call or interview (rh): ',count(id)) as count from jobs where interview or interview_rh union all
select concat('Interview or tech/test: ',count(id)) as count from jobs where interview_tech or interview_technical_test union all
select concat('Discarded: ',count(id)) as count from jobs where discarded;

SELECT id, title, company, applied, ignored, discarded, closed, created, modified, ai_enrich_error
FROM jobs
where modified >= DATE_SUB(NOW(), INTERVAL 30 MINUTE) and modified <> created
order by modified desc  

SELECT id, title, markdown, company
FROM jobs
WHERE id=355109 and cv_match_percentage is null and not (ignored or discarded or closed)
ORDER BY created desc
LIMIT 2

update jobs set cv_match_percentage = 1 where cv_match_percentage=-1;

select id, markdown from jobs order by created desc;

insert into jobs (jobId,title,markdown,`location`,url) values (
    'handMade918739487293847',
    'SENIOR PYTHON FULLSTACK ENGINEER | 55-70.000 € FULL REMOTE (from Spain)',
    'todo','handMade', 'https://www.linkedin.com/posts/luismarquezperez_encontrar-trabajo-lhh-share-7396576958068891648-uwle?utm_source=share&utm_medium=member_desktop&rcm=ACoAAAZZizwBuntXrHiItXZY-quYzSMB_DQy5oM')

select * from jobs where jobId='handMade918739487293847';

select * from jobs where jobId = 'handMade912876394872983';



-- Locks
show open tables where in_use>0;

show performance_schema.processlist;


SHOW ENGINE INNODB STATUS\G;

SHOW PROCESSLIST;

SHOW FULL PROCESSLIST;   -- This shows que query locking  the table

SHOW ENGINE INNODB STATUS\G; 