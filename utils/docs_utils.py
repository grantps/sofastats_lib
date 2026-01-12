"""
Note - demo example scripts are changed and run in sofastats_examples but are only versioned
based on what lands in examples, which only occurs when update_examples_folder() is run.

Tasks:

* Run all the demo scripts and, assuming the script completes, visually inspect the output.
* Copy folders and files into projects/sofastats_examples/src/sofastats_examples
  (leave version bumping and git updates etc to manual process)
* Empty examples folder and transfer each script across
  (having added message to the top and removed execution code from the bottom)
"""
from pathlib import Path
from shutil import copy, copytree
from textwrap import dedent


def run_demos():
    from sofastats_examples.scripts import demo_combined
    demo_combined.run()

def update_sofastats_examples_package():
    copytree(
        src='/home/g/projects/sofastats_lib/sofastats_examples',
        dst='/home/g/projects/sofastats_examples/src/sofastats_examples',
        dirs_exist_ok=True)
    ## clean up output folder leaving only empty file "default_location_for_demo_output"
    for output_file_path in Path("/home/g/projects/sofastats_examples/src/sofastats_examples/output").iterdir():
        if output_file_path.name != 'default_location_for_demo_output':
            output_file_path.unlink()
    print("🐔 Bump version of sofastats_examples and update in git and PyPI manually as required 🐔")

def update_examples_folder():
    message = dedent("""\
    ## To run the demo examples, install the sofastats_examples package
    ## and run the functions inside e.g. simple_bar_chart_from_sqlite_db() in demo_charts.py""")
    ## wipe files
    cwd = Path.cwd()
    dest_examples_folder = cwd.parent / 'examples'
    for file_path in dest_examples_folder.iterdir():
        if file_path.is_file():
            file_path.unlink()
    ## copy edited files across
    source_scripts_folder = cwd.parent / 'sofastats_examples' / 'scripts'
    for file_path in source_scripts_folder.iterdir():
        if file_path.name.startswith('demo_'):
            dest_file_path = dest_examples_folder / file_path.name
            copy(src=file_path, dst=dest_file_path)
            orig = dest_file_path.read_text()
            making_output = orig.replace("return design", "design.make_output()")
            new_text = f"{message}\n\n{making_output}"
            dest_file_path.write_text(new_text)

if __name__ == '__main__':
    pass
    run_demos()
    update_sofastats_examples_package()
    update_examples_folder()
