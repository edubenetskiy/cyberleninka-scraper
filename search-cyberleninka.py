#!/usr/bin/env python3

import argparse
import logging
import sqlite3

import cyberleninka

logger = logging.getLogger(__name__)


def parse_command_line_arguments():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-l", "--log-level",
                                 help="log level",
                                 choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                                 default='INFO')
    argument_parser.add_argument("-o", "--output-file",
                                 help="output file",
                                 default="articles.sqlite")
    argument_parser.add_argument("keywords", metavar="KEYWORD", nargs="+",
                                 help="search query keywords")
    args = argument_parser.parse_args()
    return args


def configure_logging(args):
    log_level = args.log_level
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)-15s - %(levelname)-5s - %(message)s')
    logging.getLogger(__name__).setLevel(log_level)
    logging.getLogger("cyberleninka").setLevel(log_level)


def main():
    args = parse_command_line_arguments()
    configure_logging(args)

    logger.debug(f"Creating database file {args.output_file}")
    db = sqlite3.connect(args.output_file)
    try:
        logger.debug("Creating DB table for articles")
        db.execute("""create table if not exists article
            (
                url                  text not null,
                slug                 text,
                title                text,
                abstract_description text,
                full_text_body       text,
                download_url         text
            )
        """)
        search_query = ' '.join(args.keywords)
        search_results = cyberleninka.search_articles(search_query)
        for article in search_results:
            logger.debug(f"Saving article <{article.url}> into database")
            try:
                db.execute(
                    "insert into article(slug, url, title, abstract_description, full_text_body, download_url)" +
                    "values (?, ?, ?, ?, ?, ?)",
                    (article.slug,
                     article.url,
                     article.title,
                     article.abstract_description,
                     article.full_text_body,
                     article.download_url)
                )
            except Exception as e:
                logger.warning(f"Could not save article <{article.url}> into database", exc_info=e)
            db.commit()
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    main()
