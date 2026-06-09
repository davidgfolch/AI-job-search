db = db.getSiblingDB(process.env.MONGO_DATABASE || 'jobs')

db.createCollection('company_salary_history')
db.company_salary_history.createIndex({ job_id: 1 }, { name: 'idx_job_id' })
db.company_salary_history.createIndex({ company_normalized: 1 }, { name: 'idx_company_normalized' })
db.company_salary_history.createIndex({ job_id: 1, salary: 1, recorded_at: 1 }, { name: 'idx_unique_record', unique: true })

db.createCollection('cron_state')
