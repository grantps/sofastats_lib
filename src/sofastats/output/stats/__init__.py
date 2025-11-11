"""
Create module in data_extraction with a get_results() function that returns a dc from stats_calc.interfaces.
E.g. data_extraction.get_results() -> stats_calc.interfaces.AnovaResultExt
Typically, a data structure is received from a call to the statistics engine.
That dc is often tightly wrapped around the outputs of the engine function inherited from core stats code.
The goal has been to make minimal changes to the original engine stats code.
Small, innocent changes can break the code so a very conservative approach has been taken.
On top of that we might add additional attributes that are useful for output e.g. variable or value labels.
If needed, we'll have an extended version of the dc e.g. AnovaResult -> AnovaResultExt

Next, we need something to consume the data structure and make the HTML output required.
E.g. output.stats.anova has make_anova_html() which takes the data structure and a style spec.

That module will also supply a simple end-user interface for making the HTML
E.g. AnovaSpec. The key requirement is that this dc has a to_html_spec() method returning an HTMLItemSpec.
This makes it easy to plug into reports. The report code (output.utils.get_report())
knows how to combine multiple HTMLItemSpecs into a single piece of HTML
with all the required CSS (styled and unstyled) and JS.
"""
