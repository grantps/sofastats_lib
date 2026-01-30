## cd /home/g/projects/sofastats_proj/sofastatistics && nosetests3 sofastats.tests.test_stats
## cd /home/g/projects/sofastats_proj/sofastatistics && nosetests3 sofastats.tests.test_stats:test_skew

import gettext
gettext.install(domain="sofastats", localedir="./locale")

from nose.tools import assert_equal, assert_almost_equal, assert_raises  #@UnresolvedImport
# assert_equal.im_class.maxDiff = None # http://stackoverflow.com/questions/14493670/how-to-set-self-maxdiff-in-nose-to-get-full-diff-output
# assert_almost_equal.im_class.maxDiff = None
#from nose.plugins.attrib import attr
import pprint
import random
from subprocess import run, PIPE

from sofastats.settings import main_settings as ms
from sofastats.stats.core_stats import (
    ttest_ind, ttest_rel, mannwhitneyu, wilcoxont,
    pearsonr, spearmanr, kruskalwallish, anova, fprob, betai, gammln, betacf,
    chisquare, kurtosis, skew, kurtosistest, skewtest, normaltest,
    obrientransform, sim_variance, get_summary_dics, get_quartiles, get_ci95)

cmd_start = ['python3', '-m', 'sofastats.tests.stats']

def test_ci95():
    """
    get_ci95(sample=None, mymean=None, mysd=None, high=True)
    """
    tests = [((None, 76.1, 11, 10), (69.28, 82.92)),] # p.159 Practical Statistics
    for test in tests:
        res = get_ci95(*test[0])
        assert_almost_equal(res[0], test[1][0], places=2)
        assert_almost_equal(res[1], test[1][1], places=2)

def test_get_quartiles():
    tests = [
        ([1,2,3,4,5,6,7,8,9,10,11,12], (3.5, 9.5)),
        ([2,4,5,6,6,8,10,10,12], (4.5, 10)),
        ([2,5,7,11,12,14], (5, 12)),
        ([3,4,7,8,11,13,21,29], (5.5, 17)),
        ([1,3,4,5,60], (2, 32.5)),
        ([-3,3,4,100,200], (0, 150)),
    ]
    for input_list, results in tests:
        assert_equal(get_quartiles(input_list), results)

def test_get_summary_dics():
    tests = [([[1,2,3,4,5,6,7,8,9,10], [-10.5, 0, 100]], 
          ["A", "B"], 
          True, 
          [{ms.STATS_DIC_LBL: "A", ms.STATS_DIC_N: 10,
            ms.STATS_DIC_MEDIAN: 5.5, 
            ms.STATS_DIC_MIN: 1, ms.STATS_DIC_MAX: 10, 
            ms.STATS_DIC_MEAN: 5.5, 
            ms.STATS_DIC_SD: 3.0276503541},
            {ms.STATS_DIC_LBL: "B", ms.STATS_DIC_N: 3,
            ms.STATS_DIC_MEDIAN: 0, 
            ms.STATS_DIC_MIN: -10.5, ms.STATS_DIC_MAX: 100, 
            ms.STATS_DIC_MEAN: 29.833333333, 
            ms.STATS_DIC_SD: 60.992485876}
           ]),
             ]
    for test in tests:
        samples, labels, quant, sum_dics1 = test
        sum_dics2 = get_summary_dics(samples, labels, quant)
        for i, sum_dic1 in enumerate(sum_dics1):
            sum_dic2 = sum_dics2[i]
            if quant:
                assert_almost_equal(sum_dic1[ms.STATS_DIC_MEAN], 
                                    sum_dic2[ms.STATS_DIC_MEAN])
                sum_dic1.pop(ms.STATS_DIC_MEAN)
                sum_dic2.pop(ms.STATS_DIC_MEAN)
                assert_almost_equal(sum_dic1[ms.STATS_DIC_SD], 
                                    sum_dic2[ms.STATS_DIC_SD])
                sum_dic1.pop(ms.STATS_DIC_SD)
                sum_dic2.pop(ms.STATS_DIC_SD)
            assert_equal(sum_dic1, sum_dic2)

def test_obrien():
    """
    Fails to converge (enough) if large values in samples. 1e-10 is too strict.
    """
    samples = []
    for _i in range(10):
        sample_a = [random.randint(1, 1000)/3.0 for _x in range(100)]
        sample_b = [random.randint(1, 1000)/3.0 for _x in range(100)]
        #sample_b = [x*1.2 for x in sample_a if round(x,0) % 2 == 0]
        samples.append((sample_a, sample_b))
    for sample_a, sample_b in samples:
        print(sample_a)
        print(sample_b)
        _r = obrientransform(sample_a, sample_b)
        assert_equal(True, True) # seeing if error raised

def stats_get_obrien_p(x, y):
    """
    The closest I can get to something raw from stats to test against.
    Taken from lpaired. NB no column extraction needed because not using paired 
        data.
    """
    x_strs = [str(x) for x in x]
    y_strs = [str(y) for y in y]
    ot_res = run(
        cmd_start + [
            '--obrien-transform', '--floats-1', *x_strs, '--floats-2', *y_strs],
        stdout=PIPE)
    r = eval(ot_res.stdout)
    r_0_strs = [str(x) for x in r[0]]
    r_1_strs = [str(x) for x in r[1]]
    fo_cmd = cmd_start + [
        '--f-oneway', '--floats-1', *r_0_strs, '--floats-2', *r_1_strs]
    fo_res = run(fo_cmd, stdout=PIPE)
    fo_res_stdout = fo_res.stdout
    fo_res_str = str(fo_res_stdout, encoding='utf-8')
    f_str_and_p_str, unused = fo_res_str.split('\n')
    unused_f_str, p_str = eval(f_str_and_p_str)
    p = float(p_str)
    p = str(round(p, 4))
    return p

def test_sim_variance():
    """
    Doesn't like samples of length 2 or 1 (t3 will = 0 and result in a
    ZeroDivisionError).
    """
    ok_sample_a = [0, 4, 6, 21, 24, 30, 36, 42, 72, 36, 70, 11, 72, 26, 14, 75,
        96, 119, 54, 171, 140, 168, 198, 92, 216, 25, 104, 108, 196, 116, 210,
        186, 224, 198, 68, 280, 144, 185, 304, 39, 360, 246, 336, 172, 308, 315,
        138, 282, 96, 147, 350, 102, 104, 212, 432, 55, 336, 171, 290, 59, 360,
        61, 62, 315, 384, 325, 594, 536, 408, 414, 140, 284, 288, 219, 370, 75,
        304, 385, 624, 553, 480, 324, 492, 664, 336, 425, 688, 783, 176, 534,
        720, 364, 460, 651, 564, 760, 864, 97, 588, 891]
    ok_sample_b = [0, 3, 2, 3, 32, 40, 18, 49, 8, 54, 70, 22, 108, 13, 126, 15,
        64, 51, 90, 133, 140, 126, 88, 23, 48, 25, 234, 108, 168, 232, 90, 217,
        288, 297, 68, 280, 252, 111, 228, 78, 40, 369, 168, 301, 220, 45, 184,
        94, 144, 147, 350, 306, 104, 477, 324, 330, 504, 171, 406, 472, 240,
        305, 248, 126, 256, 130, 396, 67, 612, 69, 70, 497, 360, 292, 148, 150,
        456, 231, 702, 316, 640, 567, 328, 332, 84, 680, 774, 609, 440, 267,
        810, 273, 276, 372, 470, 760, 384, 873, 392, 396]
    ok_samples = [(ok_sample_a, ok_sample_b), ]
    bad_sample_a = [1, 2]
    bad_sample_b = [26, 12]
    bad_samples = [(bad_sample_a, bad_sample_b), ]
    for unused in range(10):
        sample_a = [random.randint(1, 1000) for x in range(10)]
        sample_b = [x*1.2 for x in sample_a if round(x,0) % 2 == 0]
        if len(sample_a) > 2 and len(sample_b) > 2:
            ok_samples.append((sample_a, sample_b))
        else:
            bad_samples.append((sample_a, sample_b))
    for ok_sample_a, ok_sample_b in ok_samples:
        unused, p1 = sim_variance([ok_sample_a, ok_sample_b])
        p2 = stats_get_obrien_p(ok_sample_a, ok_sample_b)
        assert_equal(float(round(p1, 4)), float(p2))  ## only care about value, not string representation e.g. zero padding on right hand side of dp or not
    for bad_sample_a, bad_sample_b in bad_samples:
        assert_raises(Exception, sim_variance, [bad_sample_a, bad_sample_b])

def test_kurtosis():
    FISHER_ADJUSTMENT = 3.0
    for _i in range(100):
        sample_size = random.randint(20, 1000)
        sample = [random.randint(1, 100000)/3.0 for x in range(sample_size)]
        sample_strs = [str(x) for x in sample]
        res = run(
            cmd_start + ['--kurtosis', '--floats-1', *sample_strs, ],
            stdout=PIPE)
        k1 = eval(res.stdout)
        k2 = kurtosis(sample) + FISHER_ADJUSTMENT
        assert_almost_equal(k1, k2)

def test_skew():
    for _i in range(100):
        sample_size = random.randint(20, 1000)
        sample = [random.randint(1, 100000)/3.0 for x in range(sample_size)]
        sample_strs = [str(x) for x in sample]
        res = run(
            cmd_start + ['--skew', '--floats-1', *sample_strs, ],
            stdout=PIPE)
        s1 = eval(res.stdout)
        s2 = skew(sample)
        assert_almost_equal(s1, s2)

def test_kurtosistest():
    for _i in range(100):
        sample_size = random.randint(20, 1000)
        sample = [random.randint(1, 100000)/3.0 for x in range(sample_size)]
        sample_strs = [str(x) for x in sample]
        res = run(
            cmd_start + ['--kurtosis-test', '--floats-1', *sample_strs, ],
            stdout=PIPE)
        z1, p1 = eval(res.stdout)
        z2, p2, unused = kurtosistest(sample)
        assert_almost_equal(z1, z2)
        assert_almost_equal(p1, p2)

def test_skewtest():
    for _i in range(100):
        sample_size = random.randint(20, 1000)
        sample = [random.randint(1, 100000)/3.0 for x in range(sample_size)]
        sample_strs = [str(x) for x in sample]
        res = run(
            cmd_start + ['--skew-test', '--floats-1', *sample_strs, ],
            stdout=PIPE)
        z1, p1 = eval(res.stdout)
        z2, p2, unused = skewtest(sample)
        assert_almost_equal(z1, z2)
        assert_almost_equal(p1, p2)

def test_normaltest():
    for _i in range(100):
        sample_size = random.randint(20, 1000)
        sample = [random.randint(1, 100000)/3.0 for x in range(sample_size)]
        sample_strs = [str(x) for x in sample]
        res = run(
            cmd_start + ['--normal-test', '--floats-1', *sample_strs, ],
            stdout=PIPE)
        z1, p1 = eval(res.stdout)
        z2, p2, unused, unused, unused, unused = normaltest(sample)
        assert_almost_equal(z1, z2)
        assert_almost_equal(p1, p2)

def _test_ind_t_test(sample_a, sample_b, verbose=False):
    sample_a_strs = [str(x) for x in sample_a]
    sample_b_strs = [str(x) for x in sample_b]
    printit = 1 if verbose else 0
    res = run(
        cmd_start + ['--ttest-ind',
         '--floats-1', *sample_a_strs, '--floats-2', *sample_b_strs,
         '--int-1', f'{printit}',
         '--str-1', 'Male', '--str-2', 'Female', ],
        stdout=PIPE)
    t1, p1 = eval(res.stdout)
    t2, p2, dic_a, dic_b, _df = ttest_ind(
        sample_a, sample_b,
        'Male', 'Female', 
        use_orig_var=True)
    if verbose:
        print("t1: %s t2: %s" % (t1, t2))
        print("p1: %s p2: %s" % (p1, p2))
        pprint.pprint(dic_a)
        pprint.pprint(dic_b)
    assert_almost_equal(t1, t2)
    assert_almost_equal(p1, p2)

def _test_rel_t_test(sample_a, sample_b, verbose=False):
    sample_a_strs = [str(x) for x in sample_a]
    sample_b_strs = [str(x) for x in sample_b]
    printit = 1 if verbose else 0
    res = run(
        cmd_start + ['--ttest-rel',
         '--floats-1', *sample_a_strs, '--floats-2', *sample_b_strs,
         '--int-1', f'{printit}',
         '--str-1', 'Male', '--str-2', 'Female', ],
        stdout=PIPE)
    t1, p1 = eval(res.stdout)
    t2, p2, dic_a, dic_b, *_unused = ttest_rel(
        sample_a, sample_b,
        'Male', 'Female')
    if verbose:
        print("t1: %s t2: %s" % (t1, t2))
        print("p1: %s p2: %s" % (p1, p2))
        pprint.pprint(dic_a)
        pprint.pprint(dic_b)
    assert_almost_equal(t1, t2)
    assert_almost_equal(p1, p2)

def _test_wilcoxon(sample_a, sample_b, verbose=False):
    sample_a_strs = [str(x) for x in sample_a]
    sample_b_strs = [str(x) for x in sample_b]
    res = run(
        cmd_start + ['--wilcoxon',
         '--floats-1', *sample_a_strs, '--floats-2', *sample_b_strs, ],
        stdout=PIPE)
     
    w1, p1 = eval(res.stdout)
    w2, p2, *_unused = wilcoxont(sample_a, sample_b, headless=True)
    if verbose:
        print("w1: %s w2: %s" % (w1, w2))
        print("p1: %s p2: %s" % (p1, p2))
    assert_almost_equal(w1, w2)
    assert_almost_equal(p1, p2)

def _test_pearsonr(sample_a, sample_b, verbose=False):
    sample_a_strs = [str(x) for x in sample_a]
    sample_b_strs = [str(x) for x in sample_b]
    res = run(
        cmd_start + ['--pearsonr',
         '--floats-1', *sample_a_strs, '--floats-2', *sample_b_strs, ],
        stdout=PIPE)
    r1, p1 = eval(res.stdout)
    r2, p2, _df = pearsonr(sample_a, sample_b)
    if verbose:
        print("r1: %s r2: %s" % (r1, r2))
        print("p1: %s p2: %s" % (p1, p2))
    assert_almost_equal(r1, r2)
    assert_almost_equal(p1, p2)

def _test_spearmanr(sample_a, sample_b, verbose=False):
    sample_a_strs = [str(x) for x in sample_a]
    sample_b_strs = [str(x) for x in sample_b]
    res = run(
        cmd_start + ['--spearmanr',
         '--floats-1', *sample_a_strs, '--floats-2', *sample_b_strs, ],
        stdout=PIPE)
    r1, p1 = eval(res.stdout)
    r2, p2, _df = spearmanr(sample_a, sample_b, headless=True)
    if verbose:
        print("r1: %s r2: %s" % (r1, r2))
        print("p1: %s p2: %s" % (p1, p2))
    assert_almost_equal(r1, r2)
    assert_almost_equal(p1, p2)

def _test_mann_whitney(sample_a, sample_b, verbose=False):
    sample_a_strs = [str(x) for x in sample_a]
    sample_b_strs = [str(x) for x in sample_b]
    res = run(
        cmd_start + ['--mann-whitney',
         '--floats-1', *sample_a_strs, '--floats-2', *sample_b_strs, ],
        stdout=PIPE)
    u1, p1 = eval(res.stdout)
    u2, p2, dic_a, dic_b, _z = mannwhitneyu(
        sample_a, sample_b,
        'Male', 'Female',
        headless=True)
    if verbose:
        print("u1: %s u2: %s" % (u1, u2))
        print("p1: %s p2: %s" % (p1, p2))
        pprint.pprint(dic_a)
        pprint.pprint(dic_b)
    assert_almost_equal(u1, u2)
    assert_almost_equal(p1, p2)

def test_paired_tests():
    sample_n = random.randint(20, 1000)
    for _i in range(100):
        sample_a = [random.randint(1, 100000)/3.0 for _x in range(sample_n)]
        sample_b = [random.randint(1, 100000)/3.0 for _x in range(sample_n)]
        _test_ind_t_test(sample_a, sample_b, verbose=False)
        _test_rel_t_test(sample_a, sample_b, verbose=False)
        _test_wilcoxon(sample_a, sample_b, verbose=False)
        _test_pearsonr(sample_a, sample_b, verbose=False)
        _test_spearmanr(sample_a, sample_b, verbose=False)
        _test_mann_whitney(sample_a, sample_b, verbose=False)

def _test_kruskal_wallis_h(sample_lst, verbose=False):
    new_samples_lst = []
    for sample in sample_lst:
        new_sample = [str(x) for x in sample]
        new_samples_lst.append(new_sample)
    cmd = cmd_start + ['--kruskal-wallis', ]
    for n, sample in enumerate(new_samples_lst, 1):
        cmd.append(f'--floats-{n}')
        cmd.extend(sample)
    res = run(cmd, stdout=PIPE)
    h1, p1 = eval(res.stdout)
    labels = [f'label{x}' for x in range(len(sample_lst))]
    h2, p2, *_unused = kruskalwallish(sample_lst, labels)
    if verbose:
        print(f'h1: {h1} h2: {h2}')
        print(f'p1: {p1} p2: {p2}')
    assert_almost_equal(h1, h2)
    assert_almost_equal(p1, p2)

def _test_anova(sample_lst, verbose=False):
    new_samples_lst = []
    for sample in sample_lst:
        new_sample = [str(x) for x in sample]
        new_samples_lst.append(new_sample)
    cmd = cmd_start + ['--anova', ]
    for n, sample in enumerate(new_samples_lst, 1):
        cmd.append(f'--floats-{n}')
        cmd.extend(sample)
    res = run(cmd, stdout=PIPE)
    f1, p1 = eval(res.stdout)
    labels = ["label %s" % x for x in range(len(sample_lst))]
    anova_res = anova(sample_lst, labels, high=True)
    f2 = float(anova_res[1])
    p2 = float(anova_res[0])
    if verbose:
        print(f'f1: {f1} f2: {f2}')
        print(f'p1: {p1} p2: {p2}')
    assert_almost_equal(f1, f2)
    assert_almost_equal(p1, p2)

def test_ind_nway_tests():
    """
    Very important to test cases where there is not much of a difference as well
    as those where there is.
    """
    for _i in range(10): # approx 40/hr
        sample_lst = []
        samples_n = random.randint(3, 10)
        sample_size = random.randint(20, 1000)
        has_little_difference = random.choice([True, False])
        if has_little_difference:
            base_sample = [random.randint(1, 2000)/3.0 for x in \
                           range(sample_size)]
        else:
            has_equal_sizes = random.choice([True, False])
        for _j in range(samples_n):
            if has_little_difference:
                sample_lst.append(
                    [x
                     + random.choice([x/3.0, -x/3.0, 1, -1, 0.001, -0.001])
                     for x in base_sample]
                )
            else:
                if not has_equal_sizes:
                    sample_size += random.randint(1, round(sample_size/2.0, 0))
                sample = [random.randint(1, 10000000)/3.0
                          for x in range(sample_size)]
                sample_lst.append(sample)
        _test_kruskal_wallis_h(sample_lst, verbose=True)
        _test_anova(sample_lst, verbose=True)

def test_fprob():
    for _i in range(100):
        dfnum = random.randint(3, 12)
        dfden = random.randint(100, 20000)
        div = random.randint(2, 100)
        F = random.randint(0, 1000) / float(div)
        res = run(
            cmd_start + ['--fprob',
             '--int-1', str(dfnum), '--int-2', str(dfden), '--float-1', str(F), ],
            stdout=PIPE)
        p1 = eval(res.stdout)
        p2 = float(fprob(dfnum, dfden, F, high=True))
        assert_almost_equal(p1, p2)

def test_betai():
    for _i in range(100):
        x_near_edge = random.choice([True, False])
        a = random.randint(600, 18000) / 3.0 # 218
        b = random.randint(1,5) / 3.0 # 1.5
        if x_near_edge:
            print('Near edge')
            x = random.choice([0.000001234121, 0.99814821929386453580553591])
        else:
            x = random.random()
        res = run(
            cmd_start + ['--betai',
             '--float-1', str(a), '--float-2', str(b), '--float-3', str(x), ],
            stdout=PIPE)
        b1 = eval(res.stdout)
        b2 = float(betai(a, b, x, high=True))
        assert_almost_equal(b1, b2)

def test_gammln():
    for _i in range(100):
        xx = random.randint(1, 10000) / 103.0
        res = run(
            cmd_start + ['--gammln',
             '--float-1', str(xx), ],
            stdout=PIPE)
        g1 = eval(res.stdout)        
        g2 = float(gammln(xx, high=True))
        assert_almost_equal(g1, g2)

def test_betacf():
    for _i in range(100):
        x_near_edge = random.choice([True, False])
        a = random.randint(100, 10000) / 3.0 # 660.333333333
        b = random.randint(1,5) / 3.0 # 0.333333333333
        if x_near_edge:
            print("Near edge")
            x = random.choice([0.000001234121, 0.994394814936])
        else:
            x = random.random()
        print(a, b, x)
        res = run(
            cmd_start + ['--betacf', '--float-1', str(a), '--float-2', str(b),
                '--float-3', str(x), ],
            stdout=PIPE)
        b1 = eval(res.stdout)
        b2 = float(betacf(a, b, x, high=True))
        assert_almost_equal(b1, b2)

def test_chisquare():
    """
    Cannot test with df because assumed to be k-1 in stats.
    So not a complete test.
    """
    make_very_similar = random.choice([True, False])
    for _i in range(100):
        sample_size = random.randint(3, 30)
        f_obs = [random.randint(3, 500) for x in range(sample_size)]
        if make_very_similar:
            f_exp = [x + random.randint(-1, 1) for x in f_obs]
        else:
            f_exp = [random.randint(3, 500) for x in range(sample_size)]
        f_obs_strs = [str(x) for x in f_obs]
        f_exp_strs = [str(x) for x in f_exp]
        res = run(
            cmd_start + ['--chisquare',
             '--ints-1', *f_obs_strs, '--ints-2', *f_exp_strs, ],
            stdout=PIPE)
        c1, p1 = eval(res.stdout)
        c2, p2 = chisquare(f_obs, f_exp)
        c2 = float(c2)
        p2 = float(p2)
        assert_almost_equal(c1, c2)
        assert_almost_equal(p1, p2)
