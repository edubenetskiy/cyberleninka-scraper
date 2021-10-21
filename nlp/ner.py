import collections
import logging

from natasha import (
    Doc,
    Segmenter,
    MorphVocab,

    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,

    PER,
    NamesExtractor,
    DatesExtractor,
    MoneyExtractor,
    AddrExtractor,
)

DEFAULT_KEYWORD_NUM_ENTRIES_THRESHOLD = 5

log = logging.getLogger(__name__)

segmenter = Segmenter()

embedding = NewsEmbedding()
morph_tagger = NewsMorphTagger(embedding)
syntax_tagger = NewsSyntaxParser(embedding)
ner_tagger = NewsNERTagger(embedding)

morph_vocab = MorphVocab()
names_extractor = NamesExtractor(morph_vocab)
dates_extractor = DatesExtractor(morph_vocab)
money_extractor = MoneyExtractor(morph_vocab)
address_extractor = AddrExtractor(morph_vocab)


class Document:
    text: str
    doc: Doc

    def extract_keywords(self, keyword_entries_threshold=DEFAULT_KEYWORD_NUM_ENTRIES_THRESHOLD) -> collections.Counter:
        solves = []
        for token in self.doc.tokens:
            if token.pos == "NOUN" and (token.rel == "nsubj:pass" or
                                        token.rel == "amod" or
                                        token.rel == "nmod"):
                token.lemmatize(morph_vocab)
                solves.append(token.lemma)

        return collections.Counter(solves)

    def extract_person_names(self) -> set[str]:
        person_facts = {span.normal: span.fact.as_dict
                        for span in self.doc.spans
                        if span.fact}
        unique_person_names = set(person_facts)
        return unique_person_names


def prepare_document(text: str) -> Document:
    log.info("Preparing document for analysis")
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_tagger)
    doc.tag_ner(ner_tagger)
    for span in doc.spans:
        if span.type == PER:
            span.normalize(morph_vocab)
            span.extract_fact(names_extractor)

    document = Document()
    document.text = text
    document.doc = doc
    return document


def extract_named_entities(text: str) -> (collections.Counter, set[str]):
    document = prepare_document(text)
    return document.extract_keywords(), document.extract_person_names()
