"""
Note - output.utils.get_report() replies on the template param names here so keep aligned.
Not worth formally aligning them given how easy to do manually and how static.
"""
from abc import ABC
from dataclasses import dataclass, fields
import datetime
from enum import StrEnum
from pathlib import Path
import sqlite3 as sqlite
from typing import Any, Protocol  #, SupportsKeysAndGetItem (from https://github.com/python/typeshed but not worth another dependency)
from webbrowser import open_new_tab

import jinja2
import pandas as pd

from sofastats import SQLITE_DB, logger
from sofastats.conf.main import (
    INTERNAL_DATABASE_FPATH, SOFASTATS_WEB_RESOURCES_ROOT, ChartMetric, DbeName, SortOrderSpecs)
from sofastats.data_extraction.db import ExtendedCursor, get_dbe_spec
from sofastats.output.charts.conf import DOJO_CHART_JS
from sofastats.output.styles.utils import (get_generic_unstyled_css, get_style_spec, get_styled_dojo_chart_css,
    get_styled_placeholder_css_for_main_tbls, get_styled_stats_tbl_css)
from sofastats.utils.misc import get_safer_name

from ruamel.yaml import YAML

DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY = '__default_supplied_but_mandatory_anyway__'  ## enforced through add_post_init_with_mandatory_cols decorator (curried with mandatory col names)


@dataclass(frozen=False)
class CommonDesign(ABC):
    """
    Output dataclasses (e.g. MultiSeriesBoxplotChartSpec) inherit from Source.
    Can't have defaults in Source attributes (which go first) and then missing defaults for the output dataclasses.
    Therefore, we are required to supply defaults for everything in the output dataclasses.
    That includes mandatory fields.
    So how do we ensure those mandatory field arguments are supplied.
    We use a decorator (add_post_init_enforcing_mandatory_cols) to add a __post_init__ handler
    which runs Source.__post_init__ and then enforces the supply of values for every attribute
    which has DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY.
    """
    ## inputs ***********************************
    csv_file_path: Path | str | None = None
    csv_separator: str = ','
    cur: Any | None = None
    database_engine_name: str | None = None
    source_table_name: str | None = None
    table_filter: str | None = None
    ## outputs **********************************
    output_file_path: Path | str | None = None
    output_title: str | None = None
    show_in_web_browser: bool = True
    sort_orders: SortOrderSpecs | None = None
    sort_orders_yaml_file_path: Path | str | None = None

    def handle_inputs(self):
        """
        Three main paths:
          1) CSV - will be ingested into internal pysofa SQLite database (tbl_name optional - later analyses
             might be referring to that ingested table so nice to let user choose the name)
          2) cursor, dbe_name, and tbl_name
          3) or just a tbl_name (assumed to be using internal pysofa SQLite database)
        Any supplied cursors are "wrapped" inside an ExtendedCursor so we can use .exe() instead of execute
        so better error messages on query failure.

        Client code supplies dbe_name rather than dbe_spec for simplicity but internally
        Source supplies all code that inherits from it dbe_spec ready to use.
        """
        if self.csv_file_path:
            if self.cur or self.database_engine_name or self.source_table_name or self.table_filter:
                raise Exception("If supplying a CSV path don't also supply database requirements")
            if not self.csv_separator:
                self.csv_separator = ','
            if not SQLITE_DB.get('sqlite_default_cur'):
                SQLITE_DB['sqlite_default_con'] = sqlite.connect(INTERNAL_DATABASE_FPATH)
                SQLITE_DB['sqlite_default_cur'] = ExtendedCursor(SQLITE_DB['sqlite_default_con'].cursor())
            self.cur = SQLITE_DB['sqlite_default_cur']
            self.dbe_spec = get_dbe_spec(DbeName.SQLITE)
            if not self.source_table_name:
                self.source_table_name = get_safer_name(Path(self.csv_file_path).stem)
            ## ingest CSV into database
            df = pd.read_csv(self.csv_file_path, sep=self.csv_separator)
            try:
                df.to_sql(self.source_table_name, SQLITE_DB['sqlite_default_con'], if_exists='replace', index=False)
            except Exception as e:  ## TODO: supply more specific exception
                logger.info(f"Failed at attempt to ingest CSV from '{self.csv_file_path}' "
                    f"into internal pysofa SQLite database as table '{self.source_table_name}'.\nError: {e}")
            else:
                logger.info(f"Successfully ingested CSV from '{self.csv_file_path}' "
                    f"into internal pysofa SQLite database as table '{self.source_table_name}'")
        elif self.cur:
            self.cur = ExtendedCursor(self.cur)
            if not self.database_engine_name:
                supported_names = '"' + '", "'.join(name.value for name in DbeName) + '"'
                raise Exception("When supplying a cursor, a database_engine_name must also be supplied. "
                    f"Supported names currently are: {supported_names}")
            else:
                self.dbe_spec = get_dbe_spec(self.database_engine_name)
            if not self.source_table_name:
                raise Exception("When supplying a cursor, a source_table_name must also be supplied")
        elif self.source_table_name:
            if not SQLITE_DB.get('sqlite_default_cur'):
                SQLITE_DB['sqlite_default_con'] = sqlite.connect(INTERNAL_DATABASE_FPATH)
                SQLITE_DB['sqlite_default_cur'] = ExtendedCursor(SQLITE_DB['sqlite_default_con'].cursor())
            self.cur = SQLITE_DB['sqlite_default_cur']  ## not already set if in the third path - will have gone down first
            if self.database_engine_name and self.database_engine_name != DbeName.SQLITE:
                raise Exception("If not supplying a csv_file_path, or a cursor, the only permitted database engine is "
                    "SQLite (the dbe of the internal sofastats SQLite database)")
            self.dbe_spec = get_dbe_spec(DbeName.SQLITE)
        else:
            raise Exception("Either supply a path to a CSV "
                "(optional tbl_name for when ingested into internal sofastats SQLite database), "
                "a cursor (with dbe_name and tbl_name), "
                "or a tbl_name (data assumed to be in internal sofastats SQLite database)")

    def handle_outputs(self):
        ## output file path and title
        nice_name = '_'.join(self.__module__.split('.')[-2:]) + f"_{self.__class__.__name__}"
        if not self.output_file_path:
            now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            self.output_file_path = Path.cwd() / f"{nice_name}_{now}.html"
        if not self.output_title:
            self.output_title = f"{nice_name} Output"
        ## sort orders
        if self.sort_orders:
            if self.sort_orders_yaml_file_path:
                raise Exception("Oops - it looks like you supplied settings for both sort_orders "
                    "and sort_orders_yaml_file_path. Please set one or both of them to None.")
            else:
                pass
        elif self.sort_orders_yaml_file_path:
            yaml = YAML(typ='safe')  ## default, if not specified, is 'rt' (round-trip)
            self.sort_orders = yaml.load(Path(self.sort_orders_yaml_file_path))  ## might be a str or Path so make sure
        else:
            self.sort_orders = {}

    def __post_init__(self):
        self.handle_inputs()
        self.handle_outputs()
        for field in fields(self):
            if self.__getattribute__(field.name) == DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY:
                ## raise a friendly error for when they didn't supply a mandatory field that technically had a default (DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY), but we want to insist they supply a real value
                client_module = self.__module__.split('.')[-1]
                nice_name = f"{client_module}.{self.__class__.__name__}"  ## e.g. anova.AnovaDesign
                raise Exception(f"Oops - you need to supply a value for {field.name} in your {nice_name}")

    def __repr_html__(self):
        return self.__str__

    def make_output(self):
        self.to_html_design().to_file(fpath=self.output_file_path, html_title=self.output_title)
        if self.show_in_web_browser:
            open_new_tab(url=f"file://{self.output_file_path}")


@dataclass(frozen=False)
class CommonBarDesign(CommonDesign):

    metric: ChartMetric = ChartMetric.FREQ
    field_name: str | None = None
    y_axis_title: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.y_axis_title is None:
            if self.metric == ChartMetric.AVG:
                self.y_axis_title = f"Average {self.field_name}"
            elif self.metric == ChartMetric.FREQ:
                self.y_axis_title = 'Frequency'
            elif self.metric == ChartMetric.PCT:
                self.y_axis_title = 'Percent'
            elif self.metric == ChartMetric.SUM:
                self.y_axis_title = f"Summed {self.field_name}"
            else:
                raise ValueError(f'Metric {self.metric} is not supported.')


HTML_AND_SOME_HEAD_TPL = """\
<!DOCTYPE html>
<head>
<title>{{title}}</title>
<style type="text/css">
<!--
{{generic_unstyled_css}}
-->
</style>
"""

CHARTING_LINKS_TPL = """\
<link rel='stylesheet' type='text/css' href="{{sofastats_web_resources_root}}/tundra.css" />
<script src="{{sofastats_web_resources_root}}/dojo.xd.js"></script>
<script src="{{sofastats_web_resources_root}}/sofastatsdojo_minified.js"></script>
<script src="{{sofastats_web_resources_root}}/sofastats_charts.js"></script>            
"""

CHARTING_CSS_TPL = """\
<style type="text/css">
<!--
    .dojoxLegendNode {
        border: 1px solid #ccc;
        margin: 5px 10px 5px 10px;
        padding: 3px
    }
    .dojoxLegendText {
        vertical-align: text-top;
        padding-right: 10px
    }
    @media print {
        .screen-float-only{
        float: none;
        }
    }
    @media screen {
        .screen-float-only{
        float: left;
        }
    }
{{styled_dojo_chart_css}}
-->
</style>
"""

CHARTING_JS_TPL = """\
{{dojo_chart_js}}
"""

SPACEHOLDER_CSS_TPL = """\
<style type="text/css">
<!--
{{styled_placeholder_css_for_main_tbls}}
-->
</style>
"""

STATS_TBL_TPL = """\
<style type="text/css">
<!--
{{styled_stats_tbl_css}}
-->
</style>
"""

HEAD_END_TPL = "</head>"

BODY_START_TPL = "<body class='tundra'>"

BODY_AND_HTML_END_TPL = """\
</body>
</html>
"""

class OutputItemType(StrEnum):
    CHART = 'chart'
    MAIN_TABLE = 'main_table'
    STATS = 'stats'

@dataclass(frozen=True)
class HTMLItemSpec:
    html_item_str: str
    style_name: str
    output_item_type: OutputItemType

    def to_standalone_html(self, title: str) -> str:
        style_spec = get_style_spec(self.style_name)
        tpl_bits = [HTML_AND_SOME_HEAD_TPL, ]
        if self.output_item_type == OutputItemType.CHART:
            tpl_bits.append(CHARTING_LINKS_TPL)
            tpl_bits.append(CHARTING_CSS_TPL)
            tpl_bits.append(CHARTING_JS_TPL)
        if self.output_item_type == OutputItemType.MAIN_TABLE:
            tpl_bits.append(SPACEHOLDER_CSS_TPL)
        if self.output_item_type == OutputItemType.STATS:
            tpl_bits.append(STATS_TBL_TPL)
        tpl_bits.append(HEAD_END_TPL)
        tpl_bits.append(BODY_START_TPL)
        tpl_bits.append(self.html_item_str)  ## <======= the actual item content e.g. chart
        tpl_bits.append(BODY_AND_HTML_END_TPL)
        tpl = '\n'.join(tpl_bits)

        environment = jinja2.Environment()
        template = environment.from_string(tpl)
        context = {
            'generic_unstyled_css': get_generic_unstyled_css(),
            'sofastats_web_resources_root': SOFASTATS_WEB_RESOURCES_ROOT,
            'title': title,
        }
        if self.output_item_type == OutputItemType.CHART:
            context['styled_dojo_chart_css'] = get_styled_dojo_chart_css(style_spec.dojo)
            context['dojo_chart_js'] = DOJO_CHART_JS
        if self.output_item_type == OutputItemType.MAIN_TABLE:
            context['styled_placeholder_css_for_main_tbls'] = get_styled_placeholder_css_for_main_tbls(self.style_name)
        if self.output_item_type == OutputItemType.STATS:
            context['styled_stats_tbl_css'] = get_styled_stats_tbl_css(style_spec)
        html = template.render(context)
        return html

    def to_file(self, *, fpath: Path | str, html_title: str):
        with open(fpath, 'w') as f:
            f.write(self.to_standalone_html(html_title))

    def __repr_html__(self):
        return ''

class HasToHTMLItemSpec(Protocol):
    def to_html_design(self) -> HTMLItemSpec: ...

@dataclass(frozen=True)
class Report:
    html: str  ## include title

    def to_file(self, fpath: Path | str):
        with open(fpath, 'w') as f:
            f.write(self.html)
