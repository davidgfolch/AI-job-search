CREATE DATABASE IF NOT EXISTS jobs DEFAULT CHARACTER SET 'utf8';

USE jobs;

DROP TABLE jobs;

CREATE TABLE IF NOT EXISTS jobs (
    id int(11) NOT NULL AUTO_INCREMENT,
    jobId varchar(100) NOT NULL,
    title varchar(300) NOT NULL,
    company varchar(200) NOT NULL,
    location varchar(200) NOT NULL,
    url varchar(300) NOT NULL,
    markdown blob NOT NULL,
    created datetime DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE KEY (jobId)
    ) ENGINE=InnoDB

ALTER TABLE jobs ADD easyApply BOOLEAN default 0;
ALTER TABLE jobs ADD closed BOOLEAN default 0;


-- ai enrich fields
ALTER TABLE jobs ADD ai_enriched BOOLEAN default 0;
ALTER TABLE jobs ADD salary varchar(100);
ALTER TABLE jobs ADD required_technologies varchar(1000);
ALTER TABLE jobs ADD optional_technologies varchar(1000);
ALTER TABLE jobs ADD relocation BOOLEAN default 0;
ALTER TABLE jobs ADD business_sector varchar(1000);
ALTER TABLE jobs ADD required_languages varchar(1000);

-- interview process
ALTER TABLE jobs ADD ignored BOOLEAN default 0;
ALTER TABLE jobs ADD applied BOOLEAN default 0;
ALTER TABLE jobs ADD discarded BOOLEAN default 0;
ALTER TABLE jobs ADD interview_rh BOOLEAN default 0;
ALTER TABLE jobs ADD interview BOOLEAN default 0;
ALTER TABLE jobs ADD interview_tech BOOLEAN default 0;
ALTER TABLE jobs ADD interview_technical_test BOOLEAN default 0;
ALTER TABLE jobs ADD interview_technical_test_done BOOLEAN default 0;
ALTER TABLE jobs ADD contacts varchar(1000);
ALTER TABLE jobs ADD comments blob;
