from process_designs import run as run_process_designs

def run():
    run_process_designs(do_charts=True, do_stats=True, do_tables=True,
        make_separate_output=True, make_combined_output=True)

if __name__ == '__main__':
    run()
