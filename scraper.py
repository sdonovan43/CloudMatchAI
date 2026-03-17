from dedupe import dedupe_job
from storage import init_storage, save_job

init_storage()

for job in results:
    if dedupe_job(job):
        save_job(job)
