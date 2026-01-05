from pathlib import Path

examples_folder = Path.cwd().parent
files_folder = examples_folder / 'files'
output_folder = examples_folder / 'output'

sort_orders_yaml_file_path = files_folder / 'sort_orders.yaml'

education_csv_file_path = files_folder / 'education.csv'
people_csv_file_path = files_folder / 'people.csv'
sports_csv_file_path = files_folder / 'sports.csv'

sqlite_demo_db_file_path = files_folder / 'sofastats_demo.db'
