CREATE DATABASE IF NOT EXISTS jobs DEFAULT CHARACTER SET 'utf8';

USE jobs;

DROP TABLE jobs;

CREATE TABLE IF NOT EXISTS jobs (
    id int(11) NOT NULL AUTO_INCREMENT,
    jobId varchar(100) NOT NULL,
    title varchar(300) NOT NULL,
    company varchar(200),
    client varchar(200),
    location varchar(200) NOT NULL,
    url varchar(300) NOT NULL,
    markdown blob NOT NULL,
    created datetime DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE KEY (jobId)
    ) ENGINE=InnoDB

ALTER TABLE jobs ADD easy_apply BOOLEAN default 0;
--ALTER TABLE jobs CHANGE easyApply easy_apply BOOLEAN default 0;
ALTER TABLE jobs ADD closed BOOLEAN default 0;
ALTER TABLE jobs ADD client varchar(200);
ALTER TABLE jobs ADD flagged BOOLEAN default 0;

ALTER TABLE jobs ADD web_page varchar(100);

ALTER TABLE jobs ADD `modified` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- ai enrich fields
ALTER TABLE jobs ADD ai_enriched BOOLEAN default 0;
ALTER TABLE jobs ADD ai_enrich_error varchar(500);
ALTER TABLE jobs ADD salary varchar(200);
ALTER TABLE jobs ADD required_technologies varchar(1000);
ALTER TABLE jobs ADD optional_technologies varchar(1000);
ALTER TABLE jobs ADD business_sector varchar(1000);
ALTER TABLE jobs ADD required_languages varchar(1000);

-- scrapper enrich fields
ALTER TABLE jobs ADD scrapper_enriched BOOLEAN default 0;

-- search process
ALTER TABLE jobs ADD ignored BOOLEAN default 0;
ALTER TABLE jobs ADD applied BOOLEAN default 0;
ALTER TABLE jobs ADD seen BOOLEAN default 0;
ALTER TABLE jobs ADD `like` BOOLEAN default 0;
ALTER TABLE jobs ADD discarded BOOLEAN default 0;
ALTER TABLE jobs ADD interview_rh BOOLEAN default 0;
ALTER TABLE jobs ADD interview BOOLEAN default 0;
ALTER TABLE jobs ADD interview_tech BOOLEAN default 0;
ALTER TABLE jobs ADD interview_technical_test BOOLEAN default 0;
ALTER TABLE jobs ADD interview_technical_test_done BOOLEAN default 0;
ALTER TABLE jobs ADD contacts varchar(1000);
ALTER TABLE jobs ADD comments blob;

-- Indexes
ALTER TABLE jobs ADD INDEX title_index (title);
ALTER TABLE jobs ADD INDEX company_index (company);
ALTER TABLE jobs ADD INDEX client_index (client);
-- ALTER TABLE jobs ADD INDEX markdown_index (markdown);
-- ALTER TABLE jobs ADD INDEX comments_index (comments);
ALTER TABLE jobs ADD INDEX salary_index (salary);
ALTER TABLE jobs ADD INDEX ignored_index (ignored);
ALTER TABLE jobs ADD INDEX seen_index (seen);
ALTER TABLE jobs ADD INDEX applied_index (applied);
ALTER TABLE jobs ADD INDEX discarded_index (discarded);
ALTER TABLE jobs ADD INDEX closed_index (closed);
