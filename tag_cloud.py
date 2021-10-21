import logging
from collections import Counter
from pathlib import Path

from wordcloud import WordCloud

log = logging.getLogger(__name__)


def save_tag_cloud(file_path: Path, tags: Counter):
    log.info(f"Generating tag cloud")
    cloud_factory = WordCloud(width=2000,
                              height=1500,
                              background_color='black',
                              margin=20,
                              colormap='Pastel1')
    log.info(f"Saving tag cloud to file <{file_path}>")
    cloud = cloud_factory.generate_from_frequencies(tags)
    cloud.to_file(file_path)
