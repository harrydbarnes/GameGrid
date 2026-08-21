"""Reusable quality gates for the generated GameGrid catalogue.

The source can contain tens of thousands of records even when a lookup join
has failed.  These checks deliberately measure metadata that makes a record
playable in a grid, rather than treating a large game count as sufficient.
"""
from datetime import date


METADATA_COVERAGE_THRESHOLDS = {
    'title': 0.995,
    'year': 0.995,
    'platform': 0.95,
    'genre': 0.20,
    'rating': 0.15,
}

# These are intentionally modest floors for specific platform families.  They
# catch an ID/name lookup collapse while leaving the importer room to grow.
PLATFORM_MINIMUMS = {
    'Xbox': 5000,
    'GameCube': 50,
    'Switch': 50,
    'PlayStation 5': 50,
    'Xbox Series': 50,
}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _year(value):
    return isinstance(value, int) and 1970 <= value <= date.today().year + 1


def _platforms(game):
    platforms = game.get('platforms')
    return [platform.strip() for platform in platforms if _text(platform)] if isinstance(platforms, list) else []


def _genres(game):
    genres = game.get('tags')
    return [genre.strip() for genre in genres if _text(genre)] if isinstance(genres, list) else []


def _rating(game):
    rating = game.get('rating')
    return isinstance(rating, (int, float)) and not isinstance(rating, bool) and rating > 0


def metadata_coverage(games):
    total = len(games)
    checks = {
        'title': lambda game: _text(game.get('title')),
        'year': lambda game: _year(game.get('year')),
        'platform': lambda game: bool(_platforms(game)),
        'genre': lambda game: bool(_genres(game)),
        'rating': _rating,
    }
    return {
        key: {'present': sum(bool(check(game)) for game in games), 'total': total,
              'coverage': (sum(bool(check(game)) for game in games) / total if total else 0)}
        for key, check in checks.items()
    }


def platform_counts(games):
    counts = {platform: 0 for platform in PLATFORM_MINIMUMS}
    for game in games:
        platforms = _platforms(game)
        for platform in counts:
            if any(value == platform or (platform == 'Xbox' and value.startswith('Xbox')) for value in platforms):
                counts[platform] += 1
    return counts


def metadata_quality_errors(games, thresholds=METADATA_COVERAGE_THRESHOLDS):
    coverage = metadata_coverage(games)
    return [
        f'{field} coverage is {coverage[field]["coverage"]:.1%}; expected at least {minimum:.1%}'
        for field, minimum in thresholds.items()
        if coverage[field]['coverage'] < minimum
    ]


def platform_coverage_errors(games, minimums=PLATFORM_MINIMUMS):
    counts = platform_counts(games)
    return [
        f'{platform} platform coverage is {counts[platform]:,}; expected at least {minimum:,}'
        for platform, minimum in minimums.items()
        if counts[platform] < minimum
    ]


def _has_platform(game, platform):
    return platform in _platforms(game)


def platform_landmark_errors(games):
    def titled(title):
        return [game for game in games if _text(game.get('title')) and game['title'].casefold() == title.casefold()]

    errors = []
    bioshocks = titled('BioShock')
    if not any(platform.startswith('Xbox') for game in bioshocks for platform in _platforms(game)):
        errors.append('BioShock is not mapped to an Xbox platform')
    for title, platform in (
        ('Resident Evil 4', 'GameCube'),
        ('The Legend of Zelda: Breath of the Wild', 'Switch'),
        ('Astro Bot', 'PlayStation 5'),
        ('Alan Wake 2', 'Xbox Series'),
    ):
        if not any(_has_platform(game, platform) for game in titled(title)):
            errors.append(f'{title} is not mapped to {platform}')
    return errors
