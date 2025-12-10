def get_pandas_var(variable_name: str) -> str:
    return f"{variable_name}_var"

def get_pandas_val(value_name: str) -> str:
    return f"{value_name}_val"




"""
Labelling is based entirely on YAML:

age:
  var_lbl: Age (at date of study)
agegroup:
  var_lbl: Age Group
  var_comment: Standard age groupings for SOFA
  val_lbls:
    1: "< 20"
    2: "20-29"
    3: "30-39"
    4: "40-64"
    5: "65+"
...

Some variables won't have any settings, and others will be set but lack value labels.
Others will have value labels but not every value will have a label.



There is no auto-labelling apart from converting non-string values into strings if we don't have a mapped value.
The original SOFA used to convert to Title Case when no label was supplied. This is no longer the case.
There are two reasons:

1) it is hard to sort table items in multi-indexes reliably when the sort order is by value
   unless there is a robust mapping from label to value. All we have in the index is labels.
   The option of making table dfs by value and then converting all values to labels (even in deeply nested dimensions)
   in the final step after sorting, was rejected. Also rejected were attempts to work out which values in which contexts
   ('Country' could map to 'country' as a variable but 3 as a music genre in the same table)
   had been mapped to which labels and then reverse from label to value using that mapping.
   Much, much simpler to just convert values into strings if no explicit mapping.
   There is still one downside - in cases where numbers are used as categories,
   and numbers span more than one number of digits, then alphabetical order will be applied not numerical order.
   This is handled by warning users and suggesting explicit label setting where this is an issue.
2) Often title case is not a good translation into a label e.g.
   value 'NZ' might be best labelled 'New Zealand',
   value 'CategoryLabel' should not be changed to 'Categorylabel',
   value 'agegroup' is best labelled 'Age Group' not 'Agegroup'.

WARNING - if values are integers, and they are being used as categories e.g. in a table,
then the sort order of the categories will be by the string version of those values e.g. '1', '11', '12', '2', '3' etc.
If this is not what is desired, then explicit value labels will have to be set in the YAML.
"""
from dataclasses import dataclass, field
from functools import cached_property
from itertools import groupby
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML(typ='safe')  ## default, if not specified, is 'rt' (round-trip)

def var2pandas_var(var: str) -> str:
    return f"{var}_var"

def var2pandas_val(val: str) -> str:
    return f"{val}_val"


@dataclass(kw_only=True)
class VarLabelSpec:
    name: str
    lbl: str | None = None
    comment: str | None = None
    val2lbl: dict[int | str, str] = field(default_factory=dict)  ## OK to have missing mappings (even an empty dict is OK) - in which case the lbl will be the str representation of the value. But no duplicates.

    def __post_init__(self):
        if self.lbl is None:
            self.lbl = str(self.name)
        val_lbls = sorted(val_lbl for val, val_lbl in self.val2lbl.items())
        duplicate_lbls = [k for k, g in groupby(val_lbls) if len(list(g)) > 1]
        if duplicate_lbls:
            raise ValueError("Different values cannot share the same label. "
                f"The following labels are used more than once: {duplicate_lbls}")

    @property
    def pandas_var(self) -> str:
        """
        E.g. agegroup => agegroup_var
        """
        return var2pandas_var(self.name)

    @property
    def pandas_val(self) -> str:
        """
        E.g. agegroup => agegroup_val
        """
        return var2pandas_val(self.name)

    def __str__(self):
        comment_if_any = f"\n  comment: {self.comment}" if self.comment else ''
        val2lbls_if_any = f"\n  value to labels: {self.val2lbl}" if self.val2lbl else ''
        return f"name: {self.name}\n  label: {self.lbl}{val2lbls_if_any}{comment_if_any}"

@dataclass(frozen=True)
class VarLabels:
    """
    The MAIN Act. This is global, and we use it for all variable and value labelling.

    Always use .get() when using dictionary properties like .var2var_label_spec or .var2val2lbl.
    If you haven't added a variable to the YAML, it won't be in any of the dictionaries.
    If a variable has been set it will always have a label, even if it is only the variable name itself.
    There will always be a val2lbl for every variable, but it might just be an empty dictionary.
    """
    var_label_specs: list[VarLabelSpec]

    def validate(self):
        """
        Prevent duplicate labels for variables e.g. you can't have age => Age and agegroup => Age
        If your YAML has duplicates like this, you'll need to specify vars2include
        so you can avoid including conflicting variables in the same use case e.g. in the same Pie Chart or Table.
        """
        var_lbls = sorted(var_label_spec.lbl for var_label_spec in self.var_label_specs)
        duplicate_lbls = [k for k, g in groupby(var_lbls) if len(list(g)) > 1]
        if duplicate_lbls:
            raise ValueError("Variables cannot coexist in the Variable Label Details if they share the same label. "
                f"The following labels are used more than once: {duplicate_lbls}")

    def __post_init__(self):
        self.validate()

    @cached_property
    def var_lbl2var(self) -> dict[str, int | str]:
        var_lbl2var = {}
        for var_label_spec in self.var_label_specs:
            var_lbl2var[var_label_spec.lbl] = var_label_spec.name
        return var_lbl2var

    @cached_property
    def var2var_label_spec(self) -> dict[str, VarLabelSpec]:
        var2var_label_spec = {}
        for var_label_spec in self.var_label_specs:
            var2var_label_spec[var_label_spec.name] = var_label_spec
        return var2var_label_spec

    @cached_property
    def var2var_lbl(self) -> dict[str, str]:
        var2var_lbl = {var: var_label_spec.lbl for var, var_label_spec in self.var2var_label_spec.items()}
        return var2var_lbl

    @cached_property
    def var2val2lbl(self) -> dict[str, dict[int | str, str]]:
        var2val2lbl = {var: var_label_spec.val2lbl for var, var_label_spec in self.var2var_label_spec.items()}
        return var2val2lbl

    def __str__(self) -> str:
        return '\n'.join(str(var_lbl_spec) for var_lbl_spec in self.var_label_specs)

def dict2varlabels(data_label_mappings: dict, *, debug=False) -> VarLabels:
    """
    Always returns a label for each variable, even if only a string representation of the original value
    (possibly a number).
    """
    var_label_specs = []
    for var, var_spec in data_label_mappings.items():
        kwargs = {
            'name': var,
            'lbl': var_spec.get('variable_label', var),
            'val2lbl': var_spec.get('value_labels', {}),
        }
        if var_spec.get('variable_comment'):
            kwargs['comment'] = var_spec.get('variable_comment')
        var_labels_spec = VarLabelSpec(**kwargs)
        var_label_specs.append(var_labels_spec)
    var_labels = VarLabels(var_label_specs)
    if debug:
        print(data_label_mappings)
        print(var_labels)
    return var_labels
