from pathlib import Path

from sofastats.conf import main as main_conf

examples_folder = Path(main_conf.__file__).parent.parent.parent / 'sofastats_examples'
print(f"{examples_folder=}")
files_folder = examples_folder / 'files'
output_folder = examples_folder / 'output'

sort_orders_yaml_file_path = files_folder / 'sort_orders.yaml'

education_csv_file_path = files_folder / 'education.csv'
people_csv_file_path = files_folder / 'people.csv'
sports_csv_file_path = files_folder / 'sports.csv'

sqlite_demo_db_file_path = files_folder / 'sofastats_demo.db'

print(sqlite_demo_db_file_path)
