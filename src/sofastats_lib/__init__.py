"""
Top-level package for sofastats.

Big picture architecture of code pipeline:
In short, how we get from config (perhaps from a GUI), and data in a database, to HTML output

We don't want a big pile of spaghetti code, we need structure as we move through the pipeline.
In SOFA (original) the best description is DRYed out macaroni.
Code was written and hacked until it worked. It was basically spaghetti code.
Then parts were pulled out into shorter stretches of code in sub-functions.
So one big tangle of code was pulled into numerous functions (a mass of spaghetti -> lots of macaroni pieces).
But it was still pasta code.
Sometimes functions were to DRY code out (i.e. shared functions were made)
and other times code was just delegated to sub-functions and then sub-sub-functions etc.
It was very difficult to think of the purpose of a function independently of what was calling it.

The new approach is to put logical breaks in the code. And each break should be defined by a data interface.
Instead of a->b->c->...x->y->z
we have GUI -> style config AND intermediate data structure -> output data structure -> HTML
Note - we have an intermediate dc because it follows the most intuitive form based on data extraction not final use.

Internally we still have DRYed out code and delegation but within a comprehensible context.
For example, a data dataclass (dc) might have a method called to_chart_spec or similar.
The role of that function / method within the greater picture is obvious making it less likely
we'll get lost drilling into implementation.

So where exactly do we put the interfaces in the middle of the pipeline from GUI to HTML output?
Broadly speaking the flow is split into data and style, and the main interfaces are dataclasses (dc).
The flow is from config through various standard variables e.g. strings, dicts, and also dataclasses,
through to an HTML string.

                                  | data extraction -> intermediate spec (inc data) dc -> |
GUI / calling code -> design vals |                                                       |  --> output spec dc --> output HTML
                                  | style specs dc + titles + other (show n) etc -------> |

For example - making a Pie Chart:
                                   GUI or directly
                                          |
      ---------------------------------------------------------------
      |                                                              |
      v                                                              v
  Chart design                                            Output / style config
  ------------                                            -----------------------------------------------------
  tbl_name = 'demo_tbl'                                   show_n_records = True     style = 'default'
  tbl_filt_clause = None                                             |              StyleSpec dc
  chart_fld_name = 'country'                                         |              (defined in conf.style)
  chart_fld_lbl = 'Country'                                          |                    from
  category_fld_name = 'browser'                                      |      output.styles.misc.get_style_spec()
  category_fld_lbl = 'Web Browser'                                   |                     |
  chart_vals2lbls = {1: 'Japan', 2: 'Italy',...}                     |                     |
  category_vals2lbls = {'Chrome': 'Google Chrome'}                   |                     |
  category_sort_order = SortOrder.LABEL                              |                     |
              |                                                      |                     |
              v                                                      |                     |
  Intermediate charting spec (including data)                        |                     |
  -------------------------------------------                        |                     |
  ChartCategoryFreqSpecs dc                                          |                     |
  (defined in conf.charts.intermediate.freq_specs)                   |                     |
                 from                                                |                     |
  sql_extraction.charts.freq_specs                                   |                     |
  e.g. get_by_category_chart_spec()                                  |                     |
  takes all the design args as an input                              |                     |
       |                          |                       -----------                      |
       |                          |                      |                                 |
       |                          |                      |                                 |
       v                          v                      |                                 |
 [CategorySpec dc, ...]     [IndivChartSpec dc, ...]     |                                 |
            |                 |                          |                                 |
            |                 |                          |                                 |
            |                 V                          |                                 |
            ------>  PieChartingSpec dc  <---------------                                  |
                     ------------------                                                    |
                     (defined in conf.charts.output.standard)                              |
                              |                                                            |
                              --------------------> HTML str <------------------------------

For example, making a Frequency or CrossTab Table:

                          GUI or directly
                                 |
        ----------------------------------------------------------
        |                                                        |
        v                                                        v
   Table design                                            Output / style config
   ------------                                            ---------------------
   tbl_name = 'demo_tbl'                                   style = 'default'
   tbl_filt_clause = None                                        |
   title = 'Age Group'                                           |
   subtitle = 'Gender'                                           |
                                                                 |
   conf.tables.misc.VarTrees dc                                  |
   conf.tables.misc.Measures dc                                  |
              |                                                  |
              v                                                  |
    Intermediate table spec (including data)                     |
    ----------------------------------------                     |
         CrossTabSpec                                            |
         (defined in conf.tables.intermediate.cross_tab)         |
                                                                 |
            from                                                 |
    sql_extraction.tables.dims                                   |
    e.g. get_cross_tab                                           |
    takes all the design args as an input                        |
              |                                                  |
              v                                                  |
   df made by get_tbl_df()                                       |
   (from conf.tables.output.cross_tab)                           |
              |                                                  |
              --------------------> HTML str <-------------------

Having a clean break between GUI and config makes it easy to swap out to another GUI (e.g. web-based)
or even get user-supplied config directly. The latter is especially convenient when creating unit tests.

Having a clean break at the chart dc to chart HTML point means we could potentially output results in a different way
(different charting engine, or not even as a chart).

The data config to rich data component can be monolithic for convenience.
For histogram bin analyses we need to keep the bins, the data, and the labels tightly coupled
unlike with data where val to label is simply controlled by dictionaries.
The rich data can be full-fat even if it merely passes on / collects some config and makes it available
as part of its output dataclass.

Rich data dc's should have all the methods required to provide the data building blocks needed to make the chart dc

Data-related values should NOT be passed directly to the chart dc but only via the rich data dc.

Pipeline Interface Configuration (sofastats.conf):

* charts
* main tables
* stats

Under each generally data and output although sometimes misc where it doesn't fit anywhere else.

========================================================================================================================

This code base relies heavily on dataclasses. So where should these be defined and how do we avoid circularity
and how can we ensure there is an obvious location for interfaces?

Some principles:

1) Follow a level-based system where lower levels cannot inherit from higher levels and dcs are passed upwards,
sometimes being consumed in the making of new dcs.

For example, inside the output spec, call all the following in order (all from lower levels):

  data_extraction
  ===============
extract data into a dc
         │
         ▼
  stats_calc.engine
  =================
take data_extraction dc,
do stats calculations,
and produce a new dc.
This new dc should not have
any output logic at all
        │
        ▼
      output
      ======
take stats_calc dc,
extend with extra methods
suitable for consumption in output

2) Define dcs at the level where they start being used in the flow from data extraction to output
(possibly passing via stats calculations).

3) If you need to add a method to a dc,
and that function naturally belongs at a higher level than where it was originally populated,
do so by making a new dc which inherits from the earlier one.

4) When creating a new dataclass, or extending its methods, can simply mutate it and add attributes,
use inheritance, or feed in the values from one dc as an unpacked dict into the new one.

5) If dataclass is specific to something e.g. anova, define it under anova. If not, use interfaces.py at the same level.
"""
import logging
from sys import stdout

logger = logging.Logger('sofastats')
formatter = logging.Formatter('%(asctime)a %(message)s')

stream_handler = logging.StreamHandler(stream=stdout)
stream_handler.setFormatter(formatter)

logger.setLevel(logging.DEBUG)  ## sets level it will pass on to handlers - limits what handlers even know about
stream_handler.setLevel(level=logging.INFO)  ## usually INFO

## overridden on first call to internal cur
SQLITE_DB = {
    'sqlite_default_con': None,
    'sqlite_default_cur': None,
}
