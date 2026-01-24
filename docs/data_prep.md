# Data Preparation

## tl;dr
> <span class="large-quote">`sofastats` needs long-format data</span>

## Overview

Your data might come from a database, or you might have entered it manually into a spreadsheet.
But however you get your data, `sofastats` needs your data to be in a structure called "long format"
(sometimes called "long-data format").
This is explained in more detail [below](#long-format-vs-wide-format), but it has nothing to do with colour or style -
it is to do with the way the data is structured.

Hopefully, your data is already in the long format structure and everything Just Works™.
If not, it should be possible to transform your data into the correct structure.
[Here](#converting-to-long-format) are some suggestions for how to make any required changes.

## Long Format vs Wide Format

The internet has numerous user-friendly and in-depth explanations of long-format versus wide-format.
If the explanation below doesn't help, have a look for something that works better for you.

Wide format splits values for variables into different columns.
Long format split variables into values in the same column.
Confused?
The best way to understand the difference is probably by example.

Let's start with a simple dataset and, as we change it, we can see the difference between wide-format and long-format.

| Wide Format (easiest for humans to read)                                                       | Long Format (easiest for computers to read)                                         |
|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| <img alt="Simple data structure" src="https://sofastats.github.io/sofastats_lib/images/wide_and_long.png" />                             | <img alt="Simple data structure" src="https://sofastats.github.io/sofastats_lib/images/wide_and_long.png" />                  |
| <img alt="Scores by game wide format" src="https://sofastats.github.io/sofastats_lib/images/wide_games.png" />                           | <img alt="Scores by game long format" src="https://sofastats.github.io/sofastats_lib/images/long_games.png" />                |
| <img alt="Scores by game and year wide format" src="https://sofastats.github.io/sofastats_lib/images/wide_games_years.png" width='450'/> | <img alt="Scores by game and year long format" src="https://sofastats.github.io/sofastats_lib/images/long_games_years.png" /> |

The [example CSVs in the sofastats_examples package](https://github.com/sofastats/sofastats_examples/tree/main/src/sofastats_examples/files)
are all long-format.

## Converting to Long Format

If you need to change the data structure, you have at least three options.

1. Manually shift round blocks of data. This is possible with small amounts of data.
2. Write your own Python script using a library like Pandas or Polars.
3. Ask an AI for help about your specific data - it should be able to provide some customised Python code you can run to transform your specific data.

Here is an example of some working code to transform some synthetic library data.

<img alt="Data for transformation from wide to long Python example" src="https://sofastats.github.io/sofastats_lib/images/data_for_example_wide_to_long_transformation_using_python.png" />

```python
import pandas as pd

def remove_long_format_rows_with_no(df: pd.DataFrame) -> pd.DataFrame:
    """
    We need this because 'No' is not an actual value - this makes sense when you follow the code step-by-step
    """
    new_df = df[~(df == 'No').any(axis=1)].drop(columns='value')
    return new_df

def to_long_format(con, *, debug=False):
    df_source = pd.read_csv('/path/to/wide_format.csv').sort_values('Name')
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
```