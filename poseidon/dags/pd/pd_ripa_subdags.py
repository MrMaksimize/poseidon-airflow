"""PD ripa subdags file."""
from airflow.operators.python_operator import PythonOperator
from trident.operators.s3_file_transfer_operator import S3FileTransferOperator
from airflow.models import DAG
from trident.util import general
from dags.pd.pd_ripa_jobs import *
from trident.util.notifications import notify
from trident.util.seaboard_updates import update_seaboard_date, get_seaboard_update_dag, update_json_date
conf = general.config
args = general.args
schedule = general.schedule['pd_ripa']
start_date = general.start_date['pd_ripa']

sheets = ['stops',
'race',
'gender',
'disability',
'stop_reason',
'actions_taken',
'search_basis',
'contraband_evid',
'prop_seize_basis',
'prop_seize_type',
'stop_result']

def create_file_subdag():
  """
  Generate a DAG to be used as a subdag 
  that creates permit files 
  """

  dag_subdag = DAG(
    dag_id='pd_ripa.process_files',
    default_args=args,
    start_date=start_date,
    schedule_interval=schedule,
    catchup=False
  )

  for sheet in sheets:

    process_data = PythonOperator(
      task_id=f"process_{sheet}",
      provide_context=True,
      python_callable=process_prod_files,
      op_kwargs={'mode': sheet},
      on_failure_callback=notify,
      on_retry_callback=notify,
      on_success_callback=notify,
      dag=dag_subdag,
    )

  return dag_subdag

def upload_prod_files():
  """
  Generate a DAG to be used as a subdag 
  that creates permit files 
  """

  dag_subdag = DAG(
    dag_id='pd_ripa.upload_files',
    default_args=args,
    start_date=start_date,
    schedule_interval=schedule,
    catchup=False
  )

  for sheet in sheets:

    #: Upload prod file to S3
    ripa_to_S3 = S3FileTransferOperator(
      task_id=f'{sheet}_file_to_S3',
      source_base_path=conf['prod_data_dir'],
      source_key=f'ripa_{sheet}_datasd.csv',
      dest_s3_bucket=conf['dest_s3_bucket'],
      dest_s3_conn_id=conf['default_s3_conn_id'],
      dest_s3_key=f'pd/ripa_{sheet}_datasd.csv',
      on_failure_callback=notify,
      on_retry_callback=notify,
      on_success_callback=notify,
      dag=dag_subdag)

  return dag_subdag

def update_md_files():
  """
  Update md file for each dataset
  """
  dag_subdag = DAG(
    dag_id='pd_ripa.update_md',
    default_args=args,
    start_date=start_date,
    schedule_interval=schedule,
    catchup=False
  )

  for sheet in sheets:

    sheet = sheet.replace('_','-')

    get_seaboard_update_dag(f'police-ripa-{sheet}.md', dag_subdag)

  return dag_subdag

def update_json():
  """
  Update json info for each dataset
  """
  dag_subdag = DAG(
    dag_id='pd_ripa.update_json',
    default_args=args,
    start_date=start_date,
    schedule_interval=schedule,
    catchup=False
  )

  for sheet in sheets:

    update_ripa_date = PythonOperator(
      task_id=f'update_json_date_{sheet}',
      python_callable=update_json_date,
      provide_context=True,
      op_kwargs={'ds_fname': ''},
      on_failure_callback=notify,
      on_retry_callback=notify,
      on_success_callback=notify,
      dag=dag_subdag)

  return dag_subdag

