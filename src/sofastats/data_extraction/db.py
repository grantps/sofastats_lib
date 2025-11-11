"""
Either pass in a CSV or a cursor. If the cursor is not for SQLite, must also pass in a DBSpec.
The DbSpec enables db-specific quoting e.g. to make a frequency table of a variable containing strings
we would need to be able to quote and escape the content.

Only internal SQLite (for CSV ingestion) requires us to close off cursors and connections.
Otherwise, that is an external responsibility.
"""
from textwrap import dedent

from ruamel.yaml import YAML

from sofastats.conf.main import CUSTOM_DBS_FOLDER, DbeName, DbeSpec

yaml = YAML(typ='safe')  ## default, if not specified, is 'rt' (round-trip)

class ExtendedCursor:

    def __init__(self, cur):
        self.cur = cur

    def exe(self, sql):
        try:
            self.cur.execute(sql)
        except Exception as e:
            raise Exception(dedent(f"""
Error: {e}

Original SQL:
{sql}"""))

    def __getattr__(self, method_name):  ## delegate everything to real cursor
        method = getattr(self.cur, method_name)
        return method

def _yaml_to_dbe_spec(*, dbe_name: str, yaml_dict: dict[str, str]) -> DbeSpec:
    y = yaml_dict
    return DbeSpec(
        dbe_name=dbe_name,
        if_clause=y['if_clause'],
        placeholder=y['placeholder'],
        left_entity_quote=y['left_entity_quote'],
        right_entity_quote=y['right_entity_quote'],
        gte_not_equals=y['gte_not_equals'],
        cartesian_joiner=y['cartesian_joiner'],
        str_value_quote=y['str_value_quote'],
        str_value_quote_escaped=y['str_value_quote_escaped'],
        summable=y['summable'],
    )

std_dbe_name2spec = {
    DbeName.SQLITE: DbeSpec(
        dbe_name=DbeName.SQLITE,
        if_clause='CASE WHEN %s THEN %s ELSE %s END',
        placeholder='?',
        left_entity_quote='`',
        right_entity_quote='`',
        gte_not_equals='!=',
        cartesian_joiner=' JOIN ',
        str_value_quote="'",
        str_value_quote_escaped="''",
        summable='',
    )
}

def _get_std_dbe_spec(dbe_name: DbeName | str) -> DbeSpec:
    return std_dbe_name2spec.get(dbe_name)

def get_dbe_spec(dbe_name: str, *, debug=False) -> DbeSpec:
    if not dbe_name:
        raise ValueError(f"No dbe_name supplied to get_dbe_spec")
    dbe_spec = _get_std_dbe_spec(dbe_name)
    if not dbe_spec:
        ## look for custom YAML file
        yaml_fpath = CUSTOM_DBS_FOLDER / f"{dbe_name}.yaml"
        if not yaml_fpath.exists():
            raise ValueError(f"Unable to find YAML config for {dbe_name} in {CUSTOM_DBS_FOLDER}")
        try:
            yaml_dict = yaml.load(yaml_fpath)
        except FileNotFoundError as e:
            e.add_note(f"Unable to open {yaml_fpath} to extract database engine specification for '{dbe_name}'")
            raise
        except Exception as e:
            e.add_note(f"Experienced a problem extracting database engine information from '{yaml_fpath}'")
            raise
        else:
            if debug: print(yaml_dict)
            try:
                dbe_spec = _yaml_to_dbe_spec(dbe_name=dbe_name, yaml_dict=yaml_dict)
            except KeyError as e:
                e.add_note(f"Unable to create database engine spec from '{yaml_fpath}'")
                raise
    return dbe_spec
