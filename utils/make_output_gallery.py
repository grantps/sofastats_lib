from process_designs import run as run_process_designs

def run():
    run_process_designs(do_charts=True, do_stats=True, show_stats_results=False, do_tables=True,
        make_separate_output=False, make_combined_output=True,
        combined_output_report_name='output_gallery', combined_output_report_title='Output Gallery',
        is_gallery=True)

if __name__ == '__main__':
    pass
    run()
