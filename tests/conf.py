from pathlib import Path

from sofastats.conf import main as main_conf

tests_folder = Path(main_conf.__file__).parent.parent.parent.parent / 'tests'
print(f"{tests_folder=}")
csvs_folder = tests_folder / 'static_csvs'
sort_orders_yaml_file_path = tests_folder / 'sort_orders.yaml'
