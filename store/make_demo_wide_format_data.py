"""
Have two sets of values that need consolidation.

One row per person. Country is wide and

"""
from pathlib import Path
from random import randint, sample
import sqlite3 as sqlite

from faker import Faker
import pandas as pd

fake = Faker()

pd.set_option('display.max_rows', 200)
pd.set_option('display.min_rows', 30)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1_000)

examples_folder = Path.cwd().parent / 'sofastats_examples'
files_folder = examples_folder / 'files'

CSV_WIDE_FORMAT_FPATH = files_folder / 'books_wide_format.csv'
CSV_LONG_FORMAT_FPATH = files_folder / 'books_long_format.csv'
TABLE_NAME_WIDE_FORMAT = 'books_wide_format'
TABLE_NAME_LONG_FORMAT = 'books_long_format'

class BookType:
    """youth, adult, large print"""
    ADULT = ('No', 'Yes', 'No')
    LARGE_PRINT = ('No', 'No', 'Yes')
    YOUTH = ('Yes', 'No', 'No')

class Genre:
    HISTORY = ('Yes', 'No', 'No')
    ROMANCE = ('No', 'Yes', 'No')
    SCI_FI = ('No', 'No', 'Yes')

def get_genre(*, history_rate: int = 100, romance_weight: int = 100, sci_fi_weight: int=100) -> tuple[str, ...]:
    """
    History, Romance, Sci Fi
    """
    genre = sample([Genre.HISTORY, Genre.ROMANCE, Genre.SCI_FI],
        counts=[history_rate, romance_weight, sci_fi_weight], k=1)[0]
    return genre

def populate_columns(age: int) -> tuple[str, ...]:
    if age < 20:
        genre = get_genre(history_rate=100, romance_weight=100, sci_fi_weight=300)
        return BookType.YOUTH + genre
    elif age < 75:
        genre = get_genre(history_rate=80, romance_weight=100, sci_fi_weight=100)
        return BookType.ADULT + genre
    else:
        genre = get_genre(history_rate=300, romance_weight=100, sci_fi_weight=50)
        return BookType.LARGE_PRINT + genre

def make_group_pattern_books(con, *, debug=False):
    n_records = 12
    data = [(fake.name(), ) for _i in range(n_records)]
    unique_names = {tup[0] for tup in data}
    if len(unique_names) != n_records:
        raise Exception(f"Should be {n_records:,} unique names but {len(unique_names):,}")
    df = pd.DataFrame(data, columns = ['Name'])
    df['Age'] = pd.Series([randint(8, 100) for _i in range(n_records)])
    df[['Youth', 'Adult', 'Large Print', 'History', 'Romance', 'Science Fiction']] = df['Age'].apply(populate_columns).tolist()
    df = df.sort_values('Name').reset_index(drop=True)
    if debug: print(df)
    df.to_csv(CSV_WIDE_FORMAT_FPATH, index=False)
    df.to_sql(TABLE_NAME_WIDE_FORMAT, con=con, if_exists='replace', index=False)

def remove_long_format_rows_with_no(df: pd.DataFrame) -> pd.DataFrame:
    new_df = df[~(df == 'No').any(axis=1)].drop(columns='value')
    return new_df

def to_long_format(con, *, debug=False):
    df_source = pd.read_csv(CSV_WIDE_FORMAT_FPATH).sort_values('Name')
    #
    # Turn wide format:
    #
    #      Name    Youth    Adult    Large Print (ignoring columns other than the ones we are "lengthening")
    #    Rachel       No      Yes             No
    #       ...      ...      ...            ...
    #
    # into naive long format:
    #
    #      Name      Book Type    value
    #    Rachel          Youth       No   <------ Just another legitimate value as far as melt is concerned
    #    Rachel          Adult      Yes
    #    Rachel    Large Print       No
    #       ...            ...      ...
    #
    # and then, finally, into Yes/No-aware long format:
    #
    #      Name      Book Type
    #    Rachel          Adult
    #       ...            ...
    #
    df_book_type_inc_no_rows = pd.melt(df_source, id_vars=['Name'],
        var_name='Book Type', value_vars=['Youth', 'Adult', 'Large Print'])
    df_book_type = remove_long_format_rows_with_no(df_book_type_inc_no_rows)
    #
    # As above but:
    #
    #      Name    History    Romance    Sci-Fi
    #    Rachel         No        Yes        No
    #       ...        ...        ...       ...
    #
    # into:
    #
    #      Name      Genre
    #    Rachel    Romance
    #       ...        ...
    #
    df_genre_inc_no_rows = pd.melt(df_source, id_vars=['Name'],
        var_name='Genre', value_vars=['History', 'Romance', 'Science Fiction'])
    df_genre = remove_long_format_rows_with_no(df_genre_inc_no_rows)
    #
    #       Name   Age        +       Book Type
    #     Rachel    21                    Adult
    #        ...   ...                      ...
    #
    # becomes:
    #
    #       Name   Age    Book Type
    #     Rachel    21        Adult
    #        ...   ...          ...
    #
    #   +   Genre
    #     Romance
    #        ...
    # becomes:
    #
    #       Name   Age    Book Type      Genre
    #     Rachel    21        Adult    Romance
    #        ...   ...          ...        ...
    #
    df_added_book_type = df_source[['Name', 'Age']].merge(df_book_type, on='Name', how='inner')
    df_added_genre = df_added_book_type.merge(df_genre, on='Name', how='inner')

    df_final = df_added_genre.sort_values('Name')
    if len(df_source) != len(df_final):
        if len(df_final) < 1_000:
            print(df_final)
        raise Exception("The number of records changed in the transformation:\n"
            f"df_source: {len(df_source):,}; df: {len(df_final):,}"
        )
    if debug: print(df_final)
    df_final.to_csv(CSV_LONG_FORMAT_FPATH, index=False)
    df_final.to_sql(TABLE_NAME_LONG_FORMAT, con=con, if_exists='replace', index=False)

def run(*, debug=False):
    pass
    sqlite_demo_db_file_path = files_folder / 'sofastats_demo.db'
    # sqlite_demo_db_file_path.unlink(missing_ok=True)  ## leave the rest alone e.g. people
    con = sqlite.connect(sqlite_demo_db_file_path)

    make_group_pattern_books(con, debug=debug)
    to_long_format(con, debug=debug)

    con.close()


if __name__ == '__main__':
    pass
    # run(debug=True)
