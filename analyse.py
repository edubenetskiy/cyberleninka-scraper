import argparse
import collections
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

import cyberleninka
from nlp.ner import prepare_document
from pdf import extract_text_from_pdf
from tag_cloud import save_tag_cloud

log = logging.getLogger(__name__)


def parse_command_line_arguments():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-l", "--log-level",
                                 help="log level",
                                 choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                                 default='INFO')
    argument_parser.add_argument("-d", "--output-dir",
                                 help="output directory",
                                 default=Path(".") / "output" / datetime.now().strftime('%m.%d.%y %H-%M-%S'))
    argument_parser.add_argument("-m", "--max-articles",
                                 help="max number of articles",
                                 default=25)
    argument_parser.add_argument("keywords", metavar="KEYWORD", nargs="+",
                                 help="search query keywords")
    args = argument_parser.parse_args()
    return args


def configure_logging(args):
    log_level = args.log_level
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)-15s - %(levelname)-5s - %(message)s')
    logging.getLogger(__name__).setLevel(log_level)
    logging.getLogger("cyberleninka").setLevel(log_level)


def save_persons(file_path: Path, persons):
    log.info(f"Saving list of persons to file <{file_path}>")
    try:
        with file_path.open(mode='w', encoding='utf-8') as json_file:
            json.dump(persons, json_file, indent=4, ensure_ascii=False)
    except Exception as e:
        raise Exception(f"Failed to save JSON file {file_path} with persons {persons}", e)


def work(search_query_keywords, output_dir: Path, max_num_articles=100):
    search_results = cyberleninka.search_articles(search_query_keywords)

    pdfs_dir = Path("pdfs")
    pdfs_dir.mkdir(parents=True, exist_ok=True)

    index = 0
    all_tags = collections.Counter()
    all_persons = set()
    for article in search_results:
        if index >= max_num_articles:
            log.info(f"Reached limit of {max_num_articles} articles, stopping")
            break

        log.info(f"Working on article {index + 1} of {max_num_articles}...")
        try:
            pdf_file_path = pdfs_dir / f"{article.slug}.pdf"
            with open(pdf_file_path, mode='wb+') as pdf_file:
                log.info(f"Downloading article from <{article.download_url}>")
                pdf_response = requests.get(article.download_url)
                log.info(f"Saving article to file <{pdf_file.name}>")
                pdf_file.write(pdf_response.content)
            log.info(f"Extracting text from file")
            text = extract_text_from_pdf(pdf_file.name)
            text = article.full_text_body

            log.info(f"Extracting tags and persons...")
            document = prepare_document(text)
            keywords = document.extract_keywords()
            persons = document.extract_person_names()
            all_tags.update(keywords)
            all_persons.update(persons)
        except Exception as exception:
            log.error(f"Failed to process article <{article.url}>, skipping", exc_info=exception)
            continue
        finally:
            index += 1
    output_dir.mkdir(parents=True, exist_ok=True)
    save_tag_cloud(output_dir / "tag-cloud.png", all_tags)
    save_persons(output_dir / "persons.json", list(all_persons))
    log.info("Program complete")


def main():
    args = parse_command_line_arguments()
    configure_logging(args)
    search_query = ' '.join(args.keywords)
    work(search_query, Path(args.output_dir), max_num_articles=int(args.max_articles))


if __name__ == '__main__':
    main()
