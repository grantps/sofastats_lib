CI_EXPLAIN = ('There is a 95% chance the population mean is within the '
    "confidence interval calculated for this sample. Don't forget, of course, "
    'that the population mean could lie well outside the interval bounds. Note'
    ' - many statisticians argue about the best wording for this conclusion.')

KURTOSIS_EXPLAIN = ('Kurtosis measures the peakedness or flatness of values. '
    ' Between -2 and 2 means kurtosis is unlikely to be a problem. Between -1 '
    'and 1 means kurtosis is quite unlikely to be a problem.')

NORMALITY_MEASURE_EXPLAIN = ('This provides a single measure of normality. If p'
    ' is small, e.g. less than 0.01, or 0.001, you can assume the distribution'
    ' is not strictly normal. Note - it may be normal enough though.')

OBRIEN_EXPLAIN = ('If the value is small, e.g. less than 0.01, or 0.001, you '
    'can assume there is a difference in variance.')

ONE_TAIL_EXPLAIN = (
    'This is a one-tailed result i.e. based on the likelihood of a difference '
    "in one particular direction")

ONE_TAILED_EXPLANATION = (
    "This is a one-tailed result i.e. based on the likelihood of a difference in one particular direction")

P_EXPLAIN_MULTIPLE_GROUPS = (
    'If p is small, e.g. less than 0.01, or 0.001, you can assume the result '
    'is statistically significant i.e. there is a difference between at least '
    'two groups. Note: a statistically significant difference may not '
    'necessarily be of any practical significance.')

P_EXPLAIN_TWO_GROUPS = (
    "If p is small, e.g. less than 0.01, or 0.001, you can assume the result "
    "is statistically significant i.e. there is a difference between the two groups. "
    "Note: a statistically significant difference may not necessarily be of any practical significance.")

P_EXPLANATION_WHEN_MULTIPLE_GROUPS = (
    "If p is small, e.g. less than 0.01, or 0.001, you can assume the result is statistically significant "
    "i.e. there is a difference between at least two groups. "
    "Note: a statistically significant difference may not necessarily be of any practical significance.")

SKEW_EXPLAIN = ('Skew measures the lopsidedness of values. '
    ' Between -2 and 2 means skew is unlikely to be a problem. Between -1 '
    'and 1 means skew is quite unlikely to be a problem.')

STD_DEV_EXPLAIN = 'Standard Deviation measures the spread of values.'

TWO_TAILED_EXPLANATION = (
    "This is a two-tailed result i.e. based on the likelihood of a difference where the direction doesn't matter.")

WILCOXON_VARIANCE_BY_APP_EXPLAIN = ("Different statistics applications will show different results here "
    "depending on the reporting approach taken.")
