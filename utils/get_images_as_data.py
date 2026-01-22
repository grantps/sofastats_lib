from pathlib import Path

from sofastats.output.utils import image_as_data

def run():
    image_file_path = Path('/home/g/projects/sofastats_lib/store/black_pastel_table_place_holder_background_image.png')
    data = image_as_data(image_file_path)
    name = image_file_path.stem.upper().replace('-', '_')
    print(f'{name} = "{data}"')

if __name__ == '__main__':
    run()
