"""
Created in sofastats_examples and doc_utils pushed to examples.
Manually we copy anything into tests/static_csvs as required.
These are static in case any tests rely on specific expected values
rather than working those out through dynamic calculation
"""
from enum import StrEnum
from functools import partial
from pathlib import Path
from random import choice, gauss, lognormvariate, randint, sample
import sqlite3 as sqlite

from faker import Faker
import pandas as pd

fake = Faker()

pd.set_option('display.max_rows', 200)
pd.set_option('display.min_rows', 30)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1_000)

sofastats_examples_folder = Path.cwd().parent / 'sofastats_examples'
files_folder = sofastats_examples_folder / 'files'

countries = ['USA', 'South Korea', 'NZ', 'Denmark']
location_types = ['City', 'Town', 'Rural', ]
cars = [
    'BMW',
    'Porsche',
    'Audi',
    'Mercedes',
    'Volkswagen',
    'Ferrari',
    'Fiat',
    'Lamborghini',
    'Maserati',
    'Honda',
    'Toyota',
    'Mitsubishi',
    'Nissan',
    'Mazda',
    'Suzuki',
    'Kia',
    'Hyundai',
    'Tesla',
    'Mini',
    'Rolls Royce',
    'Aston Martin',
    'Jaguar',
    'Renault',
    'Citroën',
    'Peugeot',
]

possible_month_dates = [
    '2030-01-01',
    '2030-02-01',
    '2030-03-01',
    '2030-04-01',
    # '2030-05-01',  ## so we can tell the chart is not treating the dates as categories but as points at specific locations
    # '2030-06-01',
    # '2030-07-01',
    # '2030-08-01',
    '2030-09-01',
    '2030-10-01',
    '2030-11-01',
    # '2030-12-01',
    '2031-01-01',
    '2031-02-01',
    '2031-03-01',
    '2031-04-01',
    '2031-05-01',
    '2031-06-01',
    '2031-07-01',
    '2031-08-01',
    '2031-09-01',
    '2031-10-01',
    '2031-11-01',
    '2031-12-01',
    '2032-01-01',
    '2032-02-01',
    '2032-03-01',
    '2032-04-01',
    '2032-05-01',
    '2032-06-01',
    '2032-07-01',
    '2032-08-01',
    '2032-09-01',
    '2032-10-01',
    '2032-11-01',
    '2032-12-01',
]

class BookType(StrEnum):
    ADULT = 'Adult'
    LARGE_PRINT = 'Large Print'
    YOUTH = 'Youth'

class Genre(StrEnum):
    HISTORY = 'History'
    ROMANCE = 'Romance'
    SCI_FI = 'Science Fiction'

round2 = partial(round, ndigits=2)

def constrain(orig: float, *, max_val, min_val) -> float | int:
    """
    Accept the original value as long as it isn't outside the range - in which case use the limit it is beyond.
    E.g. if min_val is 6 and the value is 3 then return 6.
    """
    return max(min(orig, max_val), min_val)

def change_float_usually_up(orig: float, *, scalar_centre: float, variation: float,
        min_val: float, max_val: float) -> float:
    """
    Between 0.8x to 1.5x
    mu = 1.35
    sigma = 0.2
    """
    scalar = gauss(mu=scalar_centre, sigma=variation)
    return constrain(orig * scalar, min_val=min_val, max_val=max_val)

def change_int_usually_up(orig: int) -> int:
    change = sample([-2, -1, 0, 1, 2], counts=[1, 3, 10, 9, 2], k=1)[0]
    raw_val = orig + change
    val = constrain(raw_val, min_val=1, max_val=5)
    return val

def make_education_for_paired_difference(*, debug=False):
    """
    Reading scores and educational_satisfaction before and after intervention
    """
    n_records = 5_000
    data = [(fake.name(), ) for _i in range(n_records)]
    df = pd.DataFrame(data, columns = ['name'])
    df['Country'] = pd.Series([sample(countries, counts=[200, 100, 80, 70], k=1)[0] for _i in range(n_records)])
    df['Home Location Type'] = df['Country'].apply(country2location)
    df['Reading Score Before Help'] = pd.Series([
        round(constrain(gauss(mu=60, sigma=20), max_val=100, min_val=40), 2)
        for _i in range(n_records)])
    change_reading_score_usually_up = partial(change_float_usually_up,
        scalar_centre=1.2, variation=0.12, min_val=0, max_val=100)
    df['Reading Score After Help'] = df['Reading Score Before Help'].apply(change_reading_score_usually_up)
    df['Reading Score After Help'] = df['Reading Score After Help'].apply(round2)
    df['School Satisfaction Before Help'] = pd.Series([sample([1, 2, 3, 4, 5], counts=[1, 2, 4, 3, 1], k=1)[0] for _x in range(n_records)])
    change_satisfaction_usually_up = partial(change_float_usually_up,
        scalar_centre=1.2, variation=0.12, min_val=1, max_val=5)
    df['School Satisfaction After Help'] = df['School Satisfaction Before Help'].apply(change_satisfaction_usually_up)
    if debug: print(df)
    df.to_csv(files_folder / 'education.csv', index=False)
    df_with_missing_categories = df.copy().loc[
        (df['Country'] != 'South Korea') &
        (df['Home Location Type'] != 'Rural')
    ]
    if debug: print(df_with_missing_categories)
    df_with_missing_categories.to_csv(files_folder / 'education_with_missing_categories_for_testing.csv', index=False)

def make_sport_for_independent_difference(*, debug=False):
    n_records = 2_000
    data = [(fake.name(), ) for _i in range(n_records)]
    df = pd.DataFrame(data, columns = ['name'])
    df['Country'] = df.apply(get_country, axis=1)
    df['Sport'] = pd.Series([choice(['Archery', 'Badminton', 'Basketball', ]) for _i in range(n_records)])
    df['Height'] = pd.Series([round(constrain(gauss(mu=1.8, sigma=0.115), min_val=1.5, max_val=2.3), 2) for _i in range(n_records)])
    df.loc[df['Sport'] == 'Archery', ['Height']] = df.loc[df['Sport'] == 'Archery', ['Height']] * 0.95
    df.loc[df['Sport'] == 'Badminton', ['Height']] = df.loc[df['Sport'] == 'Badminton', ['Height']] * 1.05
    df.loc[df['Sport'] == 'Basketball', ['Height']] = df.loc[df['Sport'] == 'Basketball', ['Height']] * 1.125
    df['Height'] = df['Height'].apply(constrain, min_val=1.5, max_val=2.3)
    df['Height'] = df['Height'].apply(round2)
    if debug: print(df)
    df.to_csv(files_folder / 'sports.csv', index=False)
    df_with_missing_categories = df.copy().loc[
        (df['Sport'] != 'Basketball') &
        (df['Country'] != 'South Korea')
    ]
    if debug: print(df_with_missing_categories)
    df_with_missing_categories.to_csv(files_folder / 'sports_with_missing_categories_for_testing.csv', index=False)

def get_book_type(age: int) -> str:
    if age < 20:
        book_type = BookType.YOUTH
    elif age < 75:
        book_type = BookType.ADULT
    else:
        book_type = BookType.LARGE_PRINT
    return book_type

def get_genre(*, history_rate: int = 100, romance_weight: int = 100, sci_fi_weight: int=100) -> Genre:
    genre = sample([Genre.HISTORY, Genre.ROMANCE, Genre.SCI_FI],
        counts=[history_rate, romance_weight, sci_fi_weight], k=1)[0]
    return genre

def book_type_to_genre(book_type: BookType) -> Genre:
    if book_type == BookType.YOUTH:
        genre = get_genre(history_rate=100, romance_weight=100, sci_fi_weight=300)
    elif book_type == BookType.ADULT:
        genre = get_genre(history_rate=80, romance_weight=100, sci_fi_weight=100)
    elif book_type == BookType.LARGE_PRINT:
        genre = get_genre(history_rate=300, romance_weight=100, sci_fi_weight=50)
    else:
        raise ValueError(f"Unexpected book_type '{book_type}'")
    return genre

def make_books_for_group_pattern(*, debug=False):
    n_records = 2_000
    data = [(fake.name(), ) for _i in range(n_records)]
    df = pd.DataFrame(data, columns = ['Name'])
    df['Age'] = pd.Series([randint(8, 100) for _i in range(n_records)])
    df['Book Type'] = df['Age'].apply(get_book_type)
    df['Genre'] = df['Book Type'].apply(book_type_to_genre)
    if debug: print(df)
    df.to_csv(files_folder / 'books.csv', index=False)

def area2price(area: float) -> int:
    raw_price = 10_000 * area
    scalar = lognormvariate(mu=1, sigma=0.5)
    price = int(round(raw_price * scalar, -3))
    return price

def area2area_group(area: float) -> str:
    if area < 40:
        area_group = '< 40'
    elif area < 50:
        area_group = '40 to <50'
    elif area < 75:
        area_group = '50 to <75'
    elif area < 100:
        area_group = '75 to <100'
    elif area < 120:
        area_group = '100 to <120'
    elif area < 150:
        area_group = '120 to <150'
    elif area < 175:
        area_group = '150 to <175'
    elif area < 200:
        area_group = '175 to <200'
    elif area < 250:
        area_group = '200 to <250'
    elif area < 300:
        area_group = '250 to <300'
    else:
        area_group = '300+'
    return area_group

def price2price_group(price: int) -> str:
    if price < 200_000:
        price_group = '< 200K'
    elif price < 350_000:
        price_group = '200K to <350K'
    elif price < 500_000:
        price_group = '350K to <500K'
    elif price < 750_000:
        price_group = '500K to <750K'
    elif price < 1_000_000:
        price_group = '750K to <1M'
    elif price < 1_500_000:
        price_group = '1M to < 1.5M'
    elif price < 2_000_000:
        price_group = '1.5M to < 2M'
    elif price < 5_000_000:
        price_group = '2M to < 5M'
    elif price < 10_000_000:
        price_group = '5M to <10M'
    else:
        price_group = '10M+'
    return price_group

def get_agency(column: pd.Series) -> str:
    agency = sample(['Edge Real Estate', 'Supreme Investments', 'Castle Ridge Equity'],
        counts=[3, 2, 5], k=1)[0]
    return agency

def get_valuer(column: pd.Series) -> str:
    valuer = sample(['TopValue', 'Price It Right Inc', ],
        counts=[3, 25], k=1)[0]
    return valuer

def make_properties_for_correlation(*, debug=False):
    n_records = 20_000
    data = [fake.address() for _i in range(n_records)]
    df = pd.DataFrame(data, columns = ['Address'])
    df['Address'] = df['Address'].apply(lambda s: s.replace('\n', ', '))
    df['Floor Area'] = pd.Series([constrain(gauss(mu=100, sigma=50), min_val=10, max_val=1_500) for _i in range(n_records)])
    df['Floor Area'] = df['Floor Area'].apply(round2)
    df['Price'] = df['Floor Area'].apply(area2price)
    df['Floor Area Group'] = df['Floor Area'].apply(area2area_group)
    df['Price Group'] = df['Price'].apply(price2price_group)
    df['Agency'] = df['Address'].apply(get_agency)
    df['Valuer'] = df['Address'].apply(get_valuer)
    if debug: print(df)
    df.to_csv(files_folder / 'properties.csv', index=False)

def age2group(age: int) -> str:
    if age < 20:
        age_group = '<20'
    elif age < 30:
        age_group = '20 to <30'
    elif age < 40:
        age_group = '30 to <40'
    elif age < 50:
        age_group = '40 to <50'
    elif age < 60:
        age_group = '50 to <60'
    elif age < 70:
        age_group = '60 to <70'
    elif age < 80:
        age_group = '70 to <80'
    else:
        age_group = '80+'
    return age_group

def age2qual(age: int) -> str:
    if age < 20:
        qual = 'No Qualifications'  ## Do not use None unless you want the system to treat it as None and then NaN etc with problematic consequences! You have been warned!
    elif age < 22:
        qual = sample(['No Qualifications', 'Undergraduate', ], counts=[3, 1], k=1)[0]
    else:
        qual = sample(['No Qualifications', 'Undergraduate', 'Postgraduate', ], counts=[12, 3, 1], k=1)[0]
    return qual

def country2location(country: int) -> str:
    if country == 'USA':
        location = sample(location_types, counts=[5, 3, 2], k=1)[0]
    elif country == 'South Korea':
        location = sample(location_types, counts=[8, 3, 2], k=1)[0]
    elif country == 'NZ':
        location = sample(location_types, counts=[4, 3, 4], k=1)[0]
    elif country == 'Denmark':
        location = sample(location_types, counts=[4, 3, 3], k=1)[0]
    else:
        raise ValueError(f"Unexpected country '{country}'")
    return location

population = range(8, 100)
counts = ([3, ] * 50) + ([2, ] * 30) + ([1, ] * 12)

def get_age(_row) -> int:
    return sample(population, counts=counts, k=1)[0]

def get_weight(age: int) -> float:
    if age < 10:
        mu = 40 + (age * 4)
    elif age < 15:
        mu = 70 + (age / 1.5)
    elif age < 20:
        mu = 60 + (age * 1.75)
    elif age < 65:
        mu = 90 + (age / 10)
    elif age < 85:
        mu = 100 - (age / 20)
    else:
        mu = 105 - (age / 10)
    raw_weight = gauss(mu=mu, sigma=2.5)
    weight = constrain(raw_weight, min_val=35, max_val=150)
    return round(weight, 2)

def get_country(_row) -> str:
    country = sample(countries, counts=[5, 2, 1, 1], k=1)[0]
    return country

def age2sleep(age: int) -> float:
    if age < 20:
        mu = 8
    elif age < 55:
        mu = 7.5
    else:
        mu = 7
    raw_hours = gauss(mu=mu, sigma=1.5)
    return round(2 * raw_hours) / 2

def sleep2group(sleep: float) -> str:
    if sleep < 7:
        sleep_group = 'Under 7 hours'
    elif sleep < 9:
        sleep_group = '7 to <9 hours'
    else:
        sleep_group = '9+ hours'
    return sleep_group

def make_people_for_varied_nestable_data(*, debug=False):
    """
    Include a variant with one of each category missing.
    Useful for testing charts properly handle missing values.
    """
    n_records = 5_000
    data = [(fake.name(), ) for _i in range(n_records)]
    df = pd.DataFrame(data, columns = ['Name', ])
    df['Age'] = df.apply(get_age, axis=1)
    df['Age Group'] = df['Age'].apply(age2group)
    df['Country'] = pd.Series([sample(countries, counts=[200, 100, 80, 70], k=1)[0] for _i in range(n_records)])
    df['Handedness'] = pd.Series([sample(['Right', 'Left', 'Ambidextrous', ], counts=[9, 2, 1], k=1)[0] for _i in range(n_records)])
    df['Home Location Type'] = df['Country'].apply(country2location)
    df['Sleep'] = df['Age'].apply(age2sleep)
    df['Sleep Group'] = df['Sleep'].apply(sleep2group)
    df['Tertiary Qualifications'] = df['Age'].apply(age2qual)
    df['Car'] = pd.Series([sample(cars, counts=[
        100, 80, 100,
        100, 400, 5,
        180, 10, 30,
        200, 600, 400,
        400, 400, 200,
        300, 300, 700,
        400, 30, 30,
        100, 300, 250,
        250], k=1)[0] for _i in range(n_records)])
    df['Registration Date'] = pd.Series(choice(possible_month_dates) for _i in range(n_records))
    df['Weight Time 1'] = df['Age'].apply(get_weight)
    change_weight_usually_up = partial(change_float_usually_up,
        scalar_centre=1.05, variation=0.07, min_val=30, max_val=150)
    df['Weight Time 2'] = df['Weight Time 1'].apply(change_weight_usually_up)
    df.to_csv(files_folder / 'people.csv', index=False)
    df_with_missing_categories = df.copy().loc[
        (df['Age Group'] != '30 to <40') &
        (df['Country'] != 'South Korea') &
        (df['Handedness'] != 'Ambidextrous') &
        (df['Home Location Type'] != 'Rural') &
        (df['Sleep Group'] != '9+ hours') &
        (df['Tertiary Qualifications'] != 'No Qualifications') &
        (df['Car'] != 'Jaguar')
    ]
    if debug: print(df_with_missing_categories)
    df_with_missing_categories.to_csv(files_folder / 'people_with_missing_categories_for_testing.csv', index=False)

def make_csvs(*, debug=False):
    make_books_for_group_pattern(debug=debug)
    make_education_for_paired_difference(debug=debug)
    make_people_for_varied_nestable_data(debug=debug)
    make_properties_for_correlation(debug=debug)
    make_sport_for_independent_difference(debug=debug)

def refresh_db_from_csvs(*, debug=False):
    sqlite_demo_db_file_path = files_folder / 'sofastats_demo.db'
    sqlite_demo_db_file_path.unlink(missing_ok=True)
    con = sqlite.connect(sqlite_demo_db_file_path)
    csv_names = [
        'books',
        'education', 'education_with_missing_categories_for_testing',
        'people', 'people_with_missing_categories_for_testing',
        'properties',
        'sports', 'sports_with_missing_categories_for_testing',
    ]
    for csv_name in csv_names:
        df = pd.read_csv(files_folder / f"{csv_name}.csv")
        df.to_sql(csv_name, con=con, if_exists='replace', index=False)
        print(f"Added '{csv_name}' to '{sqlite_demo_db_file_path}'")
    con.close()

if __name__ == '__main__':
    pass
    # make_csvs(debug=True)
    # refresh_db_from_csvs(debug=True)
