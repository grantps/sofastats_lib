# sofastats_lib

<img src="https://sofastats.github.io/sofastats_lib/images/sofa_logo_text_horiz.svg" width="500" />

## Package Overview

Statistics Open For All the Python Library.

`sofastats_lib` is a Python library for statistical analysis and reporting
based on the design of the SOFA Statistics package.

The goal was keep all the tried-and-true elements of the original package
but without any of the original design mistakes.

We also wanted to make SOFA more friendly for beginners.

Let us know if you think we succeeded `grant@sofastatistics.com`.

The `sofastats` distribution package sits on top of `sofastats_lib` distribution package and adds a web GUI.
See [How UX Can Improve Your Python Project by Grant and Charlotte Paton-Simpson](https://www.youtube.com/watch?v=5DDZa46g3Yc)
for how we're trying to improve the User Experience (UX) for SOFA users, and for a peek at the GUI.

<a href="https://www.youtube.com/watch?v=5DDZa46g3Yc" target="_blank">
  <img src="https://sofastats.github.io/sofastats_lib/images/ux_pycon_presentation.png" alt="How UX Can Improve Your Python Project by Grant and Charlotte Paton-Simpson" width="400" />
</a>

## Usage Overview

### Step 0 - Install sofastats_lib

[Installation Instructions](README.md#installation)

### Step 1 - Configure Design

Configure a Design object e.g. a `CrossTabDesign`, a `SimpleBarChartDesign`, or an `AnovaDesign`.
See [API reference for Charts, Tables, and Statistical Tests](https://sofastats.github.io/sofastats_lib/API/)
for the full list.

### Step 2 - Get Output

Use the Design's `make_output()` method to make the output as an HTML file.

If the Design is for a statistical test (vs a chart or table) you can also use the `to_result()` method
to generate a results [dataclass](https://lean.python.nz/blog/dataclasses-considered-sweet.html)
which you can extract details from or just print.

#### Configuration

There are three main settings types:

1. **Inputs** - where is the data source for the design? What sort of data source is it?
2. **Outputs** - where should the output go and what should it look like?
3. **Analysis Details** - which variables are involved and is there any special sorting required - 
for example, so that '<20' is before '20-39' even though it is the other way round in the default alphabetical order
(see [Sorting](https://sofastats.github.io/sofastats_lib/API/#sorting)).

#### Inputs

There are three alternatives so you need to select one and provide the necessary details:

1. CSV - data will be ingested into internal sofastats SQLite database
(`source_table_name` optional - later analyses might be referring to that ingested table
so you might as well give it a friendly name)
2. `cur`, `database_engine_name`, and `source_table_name`
3. or just a `source_table_name` (assumed to be using internal sofastats SQLite database)

Full API here: [API reference for Charts, Tables, and Statistical Tests](https://sofastats.github.io/sofastats_lib/API/)

#### Outputs

The main setting needed is the specific file location for the HTML output.
This is optional, but you may want to control where the file goes. 

Full API here: [API reference for Charts, Tables, and Statistical Tests](https://sofastats.github.io/sofastats_lib/API/)

#### Analysis Details

For example, the `SimpleBarChartDesign` requires `variable_name` at the minimum.

### Step 3 - Think about the Output Results

<img src="https://sofastats.github.io/sofastats_lib/images/bunny_sleepy.svg" width="300" />

This is the hardest step, and we've tried really hard to provide useful information in the output
to make this as easy as possible. If you can think of better ways of providing output or explaining results
let us know at `grant@sofastatistics.com`.

## Examples

### Example Simple Bar Chart

```python
from sofastats.conf.main import SortOrder
from sofastats.output.charts.bar import SimpleBarChartDesign

chart_design = SimpleBarChartDesign(
    csv_file_path='/path/to/csv',
    output_file_path= '/path/to/output/demo_simple_bar_chart_from_csv.html',
    output_title="Simple Bar Chart (Frequencies)",
    show_in_web_browser=True,
    sort_orders_yaml_file_path='/path/to/sort_orders_yaml_file_path',
    style_name='default',
    category_field_name='Age Group',
    category_sort_order=SortOrder.CUSTOM,
    rotate_x_labels=False,
    show_borders=False,
    show_n_records=True,
    x_axis_font_size=12,
)
chart_design.make_output()
```

### Example ANOVA

```python
from sofastats.conf.main import SortOrder
from sofastats.output.stats.anova import AnovaDesign

stats_design = AnovaDesign(
    csv_file_path='/path/to/csv',
    output_file_path='/path/to/output/demo_anova_age_by_country.html',
    output_title='ANOVA',
    show_in_web_browser=True,
    sort_orders_yaml_file_path='/path/to/sort_orders_yaml_file_path',
    style_name='prestige_screen',
    grouping_field_name='Country',
    group_values=['South Korea', 'NZ', 'USA'],
    measure_field_name='Age',
    high_precision_required=False,
    decimal_points=3,
)
stats_design.make_output()
print(stats_design.to_result())
```

### More Examples

See `sofastats_lib/examples`

### `sofastats_examples` Library

Install the sofastats_examples library and run the demo scripts - fake data and a sort order YAML file are included
so you can see the code in operation for every chart, table, and statistical report Design type.

### Full API

[API reference for Charts, Tables, and Statistical Tests](https://sofastats.github.io/sofastats_lib/API/)

## Installation

### Step 1 - Create a new project

Create a project. If you’re using `uv`, the commands would be:

cd /my/projects/folder

For example:

```bash
cd ~/projects
```
Then initialise project. Continuing with `uv`:

uv init my_project_name

For example:

![uv initialisation](https://sofastats.github.io/sofastats_lib/images/uv_init.png)

We can check what uv has made by looking at contents of the new project folder, in this case using the tree command:

![uv initialisation](https://sofastats.github.io/sofastats_lib/images/folders_and_files_made.png)

As you can see, a lot of boilerplate has been set up.
Don’t worry if you can’t use the tree command on your machine – we just wanted to show you what has been made by `uv`.

<img src="https://sofastats.github.io/sofastats_lib/images/no_trees.png" width="300" />

### Step 2 - Install sofastats_lib as a project library

Inside the demo folder, add `sofastats_lib` to the demo project. Here’s how you do it with `uv`:

<img src="https://sofastats.github.io/sofastats_lib/images/uv_add.png" width="500" />

Now `sofastats_lib` is installed as a library ready to use somewhere under demo like
`demo/.venv/lib/python3.13/site-packages/sofastats_lib/`
