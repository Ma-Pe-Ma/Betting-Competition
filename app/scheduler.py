import schedule
from app import file_request
import time

def harvest_match_result():
    file_request.download_data_csv()

# call it like every other scheduling
def job_that_executes_once():
    
    return schedule.CancelJob

def scheduler_loop():
    schedule.every().day.at("18:01").do(harvest_match_result)

    while True:
        schedule.run_pending()
        time.sleep(1)