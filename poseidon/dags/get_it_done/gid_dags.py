"""Get It Done _dags file."""
import re
import glob
from airflow.operators.python_operator import PythonOperator
from airflow.models import DAG

from trident.operators.s3_file_transfer_operator import S3FileTransferOperator
from trident.operators.poseidon_sonar_operator import PoseidonSonarCreator

from trident.util import general
from trident.util.notifications import notify

from trident.util.seaboard_updates import *

from dags.get_it_done.gid_jobs import *

# All times in Airflow UTC.  Set Start Time in PST?
args = general.args
conf = general.config
schedule = general.schedule['get_it_done']
start_date = general.start_date['get_it_done']

#: Dag spec
#dag = DAG(dag_id='get_it_done', default_args=args, start_date=start_date, schedule_interval=schedule)
dag = DAG(dag_id='get_it_done',
        default_args=args,
        schedule_interval=schedule,
        start_date=start_date,
        catchup=False
        )

#: Get GID requests from Salesforce
get_streets_requests = PythonOperator(
    task_id='get_gid_streets',
    python_callable=get_gid_streets,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Get GID requests from Salesforce
get_other_requests = PythonOperator(
    task_id='get_gid_other',
    python_callable=get_gid_other,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Create mapped case record type and service name cols
update_service_name = PythonOperator(
    task_id='update_service_name',
    python_callable=update_service_name,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Fix close dates per SAP issue
update_close_dates = PythonOperator(
    task_id='update_close_dates',
    python_callable=update_close_dates,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Fix referral column
update_referral_col = PythonOperator(
    task_id='update_referral_col',
    python_callable=update_referral_col,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Add council district attribute to GID data through spatial join
join_council_districts = PythonOperator(
    task_id='join_council_districts',
    python_callable=join_council_districts,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Add comm plan district attribute to GID data through spatial join
join_community_plan = PythonOperator(
    task_id='join_community_plan',
    python_callable=join_community_plan,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Add parks attribute to GID data through spatial join
join_parks = PythonOperator(
    task_id='join_parks',
    python_callable=join_parks,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Divide records by year for prod files
create_prod_files = PythonOperator(
    task_id='create_prod_files',
    python_callable=create_prod_files,
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

#: Update data inventory json
update_json_date = PythonOperator(
    task_id='update_json_date',
    python_callable=update_json_date,
    provide_context=True,
    op_kwargs={'ds_fname': 'get_it_done_reports'},
    on_failure_callback=notify,
    on_retry_callback=notify,
    on_success_callback=notify,
    dag=dag)

services = [
    'graffiti_removal', 'illegal_dumping', 'pothole',
    '72_hour_violation'
]

service_tasks = []

for i in services:
    service_name = i.replace("_"," ").title()
    machine_service_name = i

    get_task = PythonOperator(
        task_id='get_' + machine_service_name,
        python_callable=get_requests_service_name,
        op_kwargs={
            'service_name': service_name,
            'machine_service_name': machine_service_name
        },
        on_failure_callback=notify,
        on_retry_callback=notify,
        on_success_callback=notify,
        dag=dag)

    service_tasks.append(get_task)

    #: join_council_districts must run before get_task
    create_prod_files >> get_task

filename = conf['prod_data_dir'] + "/get_it_done_*_v1.csv"
files = [os.path.basename(x) for x in glob.glob(filename)]

for index, file_ in enumerate(files):
    file_name = file_.split('.')[0]
    name_parts = file_name.split('_')

    if 'v1' in name_parts:
        name_parts.remove('datasd')
        name_parts.remove('v1')
        task_name = '_'.join(name_parts[3:-1])
        md_name = '-'.join(name_parts[3:-1])

        #: Upload prod gid file to S3
        upload_task = S3FileTransferOperator(
            task_id='upload_' + task_name,
            source_base_path=conf['prod_data_dir'],
            source_key='get_it_done_{}_requests_datasd_v1.csv'.format(
                task_name),
            dest_s3_conn_id=conf['default_s3_conn_id'],
            dest_s3_bucket=conf['dest_s3_bucket'],
            dest_s3_key='get_it_done_311/get_it_done_{}_requests_datasd_v1.csv'.
            format(task_name),
            on_failure_callback=notify,
            on_retry_callback=notify,
            on_success_callback=notify,
            replace=True,
            dag=dag)

        if task_name in services:
            for service_index, service in enumerate(services):
                if task_name == service:
                    service_update_task = get_seaboard_update_dag('gid-' + md_name + '.md', dag)
                    upload_task << service_tasks[service_index]
                    service_update_task << upload_task
        else:
            upload_task << create_prod_files

        if index == len(files)-1:
            md_update_task = get_seaboard_update_dag('get-it-done-311.md', dag)
            [update_json_date, md_update_task] << upload_task
            
#: Execution rules
[get_streets_requests, get_other_requests] >> update_service_name >> update_close_dates >> update_referral_col
update_referral_col >> join_council_districts >> join_community_plan >> join_parks >> create_prod_files

