from pathlib import Path

from sofastats.output.utils import image_as_data

root_dir = Path.cwd() / 'images_to_convert_to_data'

line = '🐇' * 75

def run():
    image_file_path = Path('')
    data = image_as_data(image_file_path)
    name = image_file_path.stem.upper().replace('-', '_')
    print(f'{name} = "{data}"')

if __name__ == '__main__':
    run()
