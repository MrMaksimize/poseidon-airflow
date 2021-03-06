"""PD RIPA _dags file."""
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator
from airflow.models import DAG
from dags.pd.pd_ripa_jobs import *
from dags.pd.pd_ripa_subdags import *
from trident.util import general
from trident.util.notifications import afsys_send_email



args = general.args
conf = general.config
schedule = general.schedule['pd_ripa']
start_date = general.start_date['pd_ripa']

dag = DAG(
    dag_id='pd_ripa',
    default_args=args,
    start_date=start_date,
    schedule_interval=schedule,
    catchup=False
    )

#: Get RIPA data from FTP and save to temp folder
get_ripa_data = PythonOperator(
    task_id='get_data',
    python_callable=get_data,
    
    dag=dag)

#: Write temp files for each Excel sheet
process_excel = PythonOperator(
    task_id="process_excel",
    provide_context=True,
    python_callable=process_excel,
    
    dag=dag)

#: Process final RIPA files and save result to prod folder
process_ripa_files = SubDagOperator(
  task_id='process_files',
  subdag=create_file_subdag(),
  dag=dag)

#: Upload
ripa_to_S3 = SubDagOperator(
  task_id='upload_files',
  subdag=upload_prod_files(),
  dag=dag)

#: Update data inventory json
update_ripa_date = SubDagOperator(
  task_id='update_json',
  subdag=update_json(),
  dag=dag)

#: Update portal modified date
update_pd_ripa_md = SubDagOperator(
  task_id='update_md',
  subdag=update_md_files(),
  dag=dag)

#: Execution rules:

get_ripa_data >> process_excel >> process_ripa_files >> ripa_to_S3 >> [update_ripa_date, update_pd_ripa_md]
