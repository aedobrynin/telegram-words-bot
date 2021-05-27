import json
from typing import List, Tuple
from sqlalchemy import Column, Integer, String, Boolean, text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import NONE_VARIANT, NONE_VARIANT_TEXT
from config import SPACE_VARIANT, SPACE_VARIANT_TEXT
from config import TOGETHER_VARIANT, TOGETHER_VARIANT_TEXT
from config import HYPHEN_VARIANT, HYPHEN_VARIANT_TEXT


engine = create_engine('sqlite:///db.sqlite', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True)
    word = Column(String, nullable=False)
    #  First variant must always be correct
    variants = Column(String, nullable=False)
    success_count = Column(Integer, server_default=text('0'), nullable=False)
    total_count = Column(Integer, server_default=text('0'), nullable=False)

    def __repr__(self) -> str:
        return f'<Word with id {self.id}>'

    def get_variants(self) -> List[Tuple[str, str]]:
        '''Returns list (variant, callback_data)
        NONE_VARIANT, SPACE_VARIANT, TOGETHER_VARIANT, HYPHEN_VARIANT
        are replaced with config.NONE_VARIANT_TEXT, config.SPACE_VARIANT_TEXT,
        config.TOGETHER_VARIANT_TEXT, config.HYPHEN_VARIANT_TEXT.'''
        ret_val = []
        for variant in self.variants:
            if variant == NONE_VARIANT:
                ret_val.append((NONE_VARIANT_TEXT, variant))
            elif variant == SPACE_VARIANT:
                ret_val.append((SPACE_VARIANT_TEXT, variant))
            elif variant == TOGETHER_VARIANT:
                ret_val.append((TOGETHER_VARIANT_TEXT, variant))
            elif variant == HYPHEN_VARIANT:
                ret_val.append((HYPHEN_VARIANT_TEXT, variant))
            else:
                ret_val.append((variant, variant))
        return ret_val

    def get_correct_variant(self) -> str:
        return self.variants[0]

    def get_correct_word(self) -> str:
        '''Returns word with correct variant applied'''
        if self.variants[0] == NONE_VARIANT:
            return self.word.replace('...', '')
        if self.variants[0] == SPACE_VARIANT:
            return self.word.replace('...', ' ')
        if self.variants[0] == TOGETHER_VARIANT:
            return self.word.replace('...', '')
        if self.variants[0] == HYPHEN_VARIANT:
            return self.word.replace('...', '-')
        return self.word.replace('...', self.variants[0].upper())

    def update_stats(self, is_successful: bool) -> None:
        self.total_count += 1
        if is_successful:
            self.success_count += 1


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    total_games = Column(Integer, server_default=text('0'), nullable=False)
    best_score = Column(Integer, server_default=text('0'), nullable=False)
    stats_by_word_id_json =\
        Column(String, server_default=text("'{}'"), nullable=False)

    daily_notification =\
        Column(Boolean, server_default=text('1'), nullable=False)

    show_in_rating =\
        Column(Boolean, server_default=text('1'), nullable=False)

    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name
        self.total_games = 0
        self.best_score = 0
        self.stats_by_word_id_json = json.dumps(dict())
        self.daily_notification = True
        self.show_in_rating = True

    def __repr__(self) -> str:
        return f'<User with id {self.id}>'

    def update_best_score(self, score: int) -> None:
        self.best_score = max(self.best_score, score)

    def get_stats(self) -> dict:
        return json.loads(self.stats_by_word_id_json)

    def update_stats(self, word_id: int, is_successful: bool) -> None:
        stats = self.get_stats()

        word_id = str(word_id)
        if word_id not in stats:
            stats[word_id] = [0, 0]

        stats[word_id][1] += 1
        if is_successful:
            stats[word_id][0] += 1
        self.stats_by_word_id_json = json.dumps(stats)


Base.metadata.create_all(engine)
