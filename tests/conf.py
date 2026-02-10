from pathlib import Path

from sofastats.conf import main as main_conf

tests_folder = Path(main_conf.__file__).parent.parent.parent.parent / 'tests'
print(f"{tests_folder=}")
csvs_folder = tests_folder / 'static_csvs'
sort_orders_yaml_file_path = tests_folder / 'sort_orders.yaml'

books_csv_fpath = csvs_folder / 'books.csv'
education_csv_fpath = csvs_folder / 'education.csv'
people_csv_fpath = csvs_folder / 'people.csv'
sports_csv_file_path = csvs_folder / 'sports.csv'

age_groups_sorted = ['<20', '20 to <30', '30 to <40', '40 to <50', '50 to <60', '60 to <70', '70 to <80', '80+']
age_groups_unsorted = ['20 to <30', '30 to <40', '40 to <50', '50 to <60', '60 to <70', '70 to <80', '80+', '<20', ]
countries_sorted = ['USA', 'NZ', 'South Korea', 'Denmark', ]
handedness_sorted = ['Right', 'Left', 'Ambidextrous', ]
home_location_types_sorted = ['City', 'Town', 'Rural']
home_location_types_unsorted = ['City', 'Rural', 'Town']
sleep_groups_sorted = ['Under 7 hours', '7 to <9 hours', '9+ hours']
