from importlib import import_module
from pathlib import Path

# Internal library packages and modules
if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))


from json_model import Articles


def main(files, module):

    extract_module = import_module(f'extract.extract.{module}')
    export_dir = EXPORT_DIR / 'EXTRACT_FILES'
    export_dir.mkdir(exist_ok=True)

    extracted = []

    for file in files[:23]:

        with open(file, 'r', encoding='utf-8') as f:
            try:
                # GET ARTICLE SOUP
                article = extract_module.ArticleSoup(f.read())
                extracted.append(article.extract())
            except UnicodeDecodeError:
                pass

    articles_json = Articles(extracted)
    articles_json.save(filename=module, filepath=export_dir)

    return articles_json


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(prog='ps_automation_filescrape')
    parser.add_argument('module')
    parser.add_argument('htmldir')
    parser.add_argument('exportdir')

    args = parser.parse_args()

    HTML_DIR = Path(args.htmldir)
    EXPORT_DIR = Path(args.exportdir)

    html_files = filter(lambda f: f.name.endswith('.html'), HTML_DIR.iterdir())
    sorted_html_files = sorted(html_files, key=lambda x: x.stat().st_mtime, reverse=True)

    main(sorted_html_files, args.module)
