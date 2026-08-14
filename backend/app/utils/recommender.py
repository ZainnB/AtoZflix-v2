"""
Recommendation engine for AtoZflix.

Three strategies live here:

1. Content-based filtering
   Every movie is turned into a sparse TF-IDF style feature vector built from its
   metadata (genres / keywords / cast / crew / country / language / decade).  A
   user is turned into a vector too, using the Rocchio method: the centroid of
   the things they liked, pushed away from the centroid of the things they
   disliked.  Ranking is cosine similarity between the user vector and every
   unseen movie vector.

2. Collaborative filtering
   Item-item neighbourhood CF over the user-item interaction matrix (ratings,
   favourites and watch-later entries folded into a single preference score).
   Similarity is cosine with significance shrinkage so that two movies sharing
   one lonely user do not look like perfect twins.

3. Hybrid
   Min-max normalises both score lists onto a common scale and blends them.  The
   mixing weight is adaptive: a user with almost no history is served mostly
   content-based results (CF has nothing to work with), a user with a dense
   history is served mostly collaborative results.  A user with no history at all
   falls back to a Bayesian-weighted popularity ranking.

Implementation notes
--------------------
Everything is plain Python over dicts.  The catalog is in the thousands-of-rows
range, and both models are built once and cached in-process, so pulling numpy /
scikit-learn into the deployment image was not worth the weight.  The maths
(TF-IDF, L2 normalisation, cosine, shrinkage) is written out explicitly below.

Both models are cached behind a TTL + fingerprint check (see ModelCache) so the
O(N * tokens) content build and the O(sum over users of k^2) CF build happen on a
cold request or after the data changes, not on every call.
"""

import math
import threading
import time
from collections import defaultdict
from datetime import date, datetime

from app import db
from app.models.models import (
    Actor,
    Country,
    Crew,
    Favorite,
    Genre,
    ItemSimilarity,
    Keyword,
    Movie,
    MovieLensRating,
    MoviesActors,
    MoviesCountries,
    MoviesCrew,
    MoviesGenres,
    MoviesKeywords,
    Rating,
    WatchLater,
)

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

# How much each kind of metadata contributes before IDF is applied.  Genres and
# keywords describe *what a film is about*, so they dominate; a shared country or
# language is weak evidence of similar taste.
FEATURE_WEIGHTS = {
    "genre": 1.00,
    "keyword": 0.90,
    "crew": 0.80,
    "actor": 0.55,
    "country": 0.30,
    "lang": 0.30,
    "decade": 0.25,
}

# Explicit ratings are on a 0-10 scale; this is the point above which a rating
# counts as "liked".  Rocchio needs both a positive and a negative centroid.
RATING_MIDPOINT = 5.0

# Implicit signals.  A favourite is a confirmed like; a watch-later is a weaker
# statement of intent, so it gets a smaller weight.
FAVOURITE_WEIGHT = 1.00
WATCHLATER_WEIGHT = 0.40

# Rocchio: how hard to push away from disliked items.  Kept well below the
# positive weight because a low rating is a noisier signal than a high one.
ROCCHIO_BETA = 1.00   # pull toward the liked centroid
ROCCHIO_GAMMA = 0.35  # push away from the disliked centroid

# Cap on how many features a user profile keeps, strongest first.
#
# A user with 400 rated films accumulates a profile spanning ~12,000 features,
# and scoring walks the inverted index for every one. The long tail is a single
# actor from a single film with a near-zero weight: it costs a full postings
# walk and barely moves the ranking. Measured on the MovieLens catalog,
# content-only HitRate@10 by cap was 100 -> 2.3%, 250 -> 2.8%, 600 -> 3.4%,
# 2000 -> 3.9%, uncapped -> 3.9%. 600 keeps most of the quality at a fraction of
# the scoring cost, and the gap closes almost entirely once the popularity prior
# below is applied.
MAX_PROFILE_TOKENS = 600

# How much of the content score comes from a popularity prior rather than pure
# metadata similarity.
#
# This is the single largest quality win on real data. Pure cosine over metadata
# is popularity-blind: it happily ranks an obscure film that shares three
# character actors above an obvious classic, so on the real catalog content-only
# scored 2.8% - WORSE than recommending by raw popularity (9.7%). Mixing in a
# Bayesian popularity prior took it to 11.2%, a 4x improvement that also beats
# the popularity baseline outright.
#
# Measured (content-only HitRate@10): 0.0 -> 2.8%, 0.2 -> 9.5%, 0.4 -> 11.2%,
# 0.6 -> 8.4%. Past ~0.4 it starts drowning out the personalisation it exists to
# deliver, which is exactly the shape you would expect.
#
# This did not show up on synthetic data at all: that generator gave every film
# comparable exposure, so metadata similarity alone was sufficient. It only
# appeared once the catalog had a real long tail.
CONTENT_POPULARITY_PRIOR = 0.40

# Interactions older than this lose half their weight (recency decay).
HALF_LIFE_DAYS = 180.0

# Item-item CF: how many neighbours to keep per item, and the shrinkage constant.
# sim is multiplied by n_ij / (n_ij + SHRINKAGE), so a pair backed by 1 user is
# damped hard while a pair backed by 50 users passes through almost untouched.
CF_NEIGHBOURS = 60
CF_SHRINKAGE = 2.0

# Hybrid blend weight (weight on the content score; CF gets the remainder).
#
# Tuned by sweeping 0.0 to 1.0 on the offline harness against REAL data: 4,986
# TMDb films, 15.6M MovieLens ratings, 1,500 sampled users.
#
#   alpha  0.0 (pure CF) 18.5% | 0.3 19.4% | 0.6 21.0% | 0.8 15.9% | 1.0 8.1%
#
# 0.6 is a genuine optimum, and the hybrid genuinely beats either model alone
# (21.0% vs 18.5% CF-only vs 8.1% content-only). The gain holds across every
# history-length bucket, so it is not an artefact of one user segment.
#
# Two rounds of measurement were needed to get here, and both corrected an
# assumption:
#
#  1. Tuned first on synthetic data, this looked like a content-dominated
#     problem (content 7.0%, CF 5.8%) and the hybrid was at parity with content
#     alone. On real data the ordering INVERTED - CF 18.5%, content 2.8% before
#     the popularity prior. Synthetic data encoded its predictive structure
#     directly in metadata, which flattered the content model. Do not trust a
#     relative ranking measured on generated data.
#  2. An earlier version ramped alpha down as history grew, on the usual
#     assumption that CF earns more trust once it has data. The sweep does not
#     support that, so the ramp now only handles the direction the evidence does
#     support: a user with no history has no CF neighbourhood at all.
DENSE_HISTORY_N = 10
MIN_CONTENT_WEIGHT = 0.60

# Bayesian popularity prior (the classic IMDb weighted-rating formula).
POPULARITY_MIN_VOTES = 500.0

# Rebuild the cached models at most this often.
MODEL_TTL_SECONDS = 900.0


# ---------------------------------------------------------------------------
# Small vector helpers (sparse dict {token: float})
# ---------------------------------------------------------------------------

def _l2_normalise(vec):
    """Scale a sparse vector to unit length so dot product == cosine similarity."""
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0:
        return {}
    return {k: v / norm for k, v in vec.items()}


def _add_scaled(target, vec, scale):
    """target += vec * scale, in place."""
    for k, v in vec.items():
        target[k] += v * scale


def _min_max_normalise(scores):
    """Squash a {key: score} dict onto [0, 1] so two models can be blended."""
    if not scores:
        return {}
    values = scores.values()
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return {k: 1.0 for k in scores}
    span = hi - lo
    return {k: (v - lo) / span for k, v in scores.items()}


def _decay(when):
    """Exponential recency decay. Undated rows (legacy data) are not decayed."""
    if when is None:
        return 1.0
    if isinstance(when, datetime):
        when = when.date()
    if not isinstance(when, date):
        return 1.0
    age_days = (date.today() - when).days
    if age_days <= 0:
        return 1.0
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


# ---------------------------------------------------------------------------
# Content model
# ---------------------------------------------------------------------------

class ContentModel:
    """
    TF-IDF weighted metadata vectors + an inverted index for fast scoring.

    vectors[movie_id]  -> {token: weight}, L2-normalised
    postings[token]    -> [(movie_id, weight), ...]   (inverted index)
    labels[token]      -> human readable name, used to explain recommendations
    """

    def __init__(self, vectors, postings, labels, popularity):
        self.vectors = vectors
        self.postings = postings
        self.labels = labels
        self.popularity = popularity

    @property
    def size(self):
        return len(self.vectors)

    def score(self, query_vec, exclude=frozenset(), candidate_limit=None):
        """
        Cosine similarity of `query_vec` against every movie sharing at least one
        token with it.  Walking the inverted index means we only touch movies
        that can possibly score above zero, instead of all N.
        """
        scores = defaultdict(float)
        for token, q_weight in query_vec.items():
            postings = self.postings.get(token)
            if not postings:
                continue
            # A token present in most of the catalog carries almost no signal and
            # its postings list is long; IDF already shrank its weight, so skip
            # the walk entirely when the contribution cannot matter.
            if abs(q_weight) < 1e-6:
                continue
            for movie_id, m_weight in postings:
                if movie_id in exclude:
                    continue
                scores[movie_id] += q_weight * m_weight

        if candidate_limit and len(scores) > candidate_limit:
            top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:candidate_limit]
            return dict(top)
        return dict(scores)

    def explain(self, query_vec, movie_id, top_n=4):
        """Which shared features drove this recommendation."""
        movie_vec = self.vectors.get(movie_id)
        if not movie_vec:
            return []
        contributions = [
            (token, query_vec[token] * weight)
            for token, weight in movie_vec.items()
            if token in query_vec and query_vec[token] > 0
        ]
        contributions.sort(key=lambda kv: kv[1], reverse=True)
        return [self.labels.get(token, token) for token, _ in contributions[:top_n]]


def build_content_model():
    """
    One pass over the catalog and its join tables, then TF-IDF + L2 normalise.

    Cost is O(total feature rows).  Each join table is pulled in a single query
    rather than per-movie, which is the difference between ~6 queries and ~6N.
    """
    movies = db.session.query(
        Movie.movie_id,
        Movie.original_language,
        Movie.release_date,
        Movie.rating_avg,
        Movie.rating_count,
    ).all()

    if not movies:
        return ContentModel({}, {}, {}, {})

    raw = defaultdict(dict)   # movie_id -> {token: pre-IDF weight}
    labels = {}

    # --- intrinsic attributes (language, decade) ---------------------------
    for movie_id, language, release_date, _avg, _count in movies:
        if language:
            token = f"lang:{language}"
            raw[movie_id][token] = FEATURE_WEIGHTS["lang"]
            labels[token] = f"{language.upper()} language"
        if release_date:
            decade = (release_date.year // 10) * 10
            token = f"decade:{decade}"
            raw[movie_id][token] = FEATURE_WEIGHTS["decade"]
            labels[token] = f"{decade}s"

    # --- related entities, one bulk query each -----------------------------
    entity_queries = (
        (
            "genre",
            db.session.query(MoviesGenres.movie_id, Genre.genre_id, Genre.genre_name)
            .join(Genre, MoviesGenres.genre_id == Genre.genre_id),
        ),
        (
            "keyword",
            db.session.query(MoviesKeywords.movie_id, Keyword.keyword_id, Keyword.keyword_name)
            .join(Keyword, MoviesKeywords.keyword_id == Keyword.keyword_id),
        ),
        (
            "actor",
            db.session.query(MoviesActors.movie_id, Actor.actor_id, Actor.actor_name)
            .join(Actor, MoviesActors.actor_id == Actor.actor_id),
        ),
        (
            "crew",
            db.session.query(MoviesCrew.movie_id, Crew.crew_id, Crew.crew_name)
            .join(Crew, MoviesCrew.crew_id == Crew.crew_id),
        ),
        (
            "country",
            db.session.query(MoviesCountries.movie_id, Country.country_id, Country.country_name)
            .join(Country, MoviesCountries.country_id == Country.country_id),
        ),
    )

    for namespace, query in entity_queries:
        weight = FEATURE_WEIGHTS[namespace]
        for movie_id, entity_id, entity_name in query.all():
            token = f"{namespace}:{entity_id}"
            raw[movie_id][token] = weight
            labels[token] = entity_name

    # --- IDF ---------------------------------------------------------------
    # Rare features (a specific director) should outweigh ubiquitous ones
    # ("Drama").  Smoothed so a token in every movie still gets a positive, tiny
    # weight rather than exactly zero.
    n_docs = len(raw)
    doc_freq = defaultdict(int)
    for tokens in raw.values():
        for token in tokens:
            doc_freq[token] += 1

    idf = {
        token: math.log((n_docs + 1) / (df + 1)) + 1.0
        for token, df in doc_freq.items()
    }

    vectors = {}
    postings = defaultdict(list)
    for movie_id, tokens in raw.items():
        vec = _l2_normalise({t: w * idf[t] for t, w in tokens.items()})
        if not vec:
            continue
        vectors[movie_id] = vec
        for token, weight in vec.items():
            postings[token].append((movie_id, weight))

    # --- popularity prior (IMDb weighted rating) ---------------------------
    # score = (v / (v + m)) * R + (m / (v + m)) * C
    rated = [(a, c) for _id, _l, _d, a, c in movies if a is not None and c is not None]
    mean_rating = (sum(a for a, _ in rated) / len(rated)) if rated else 0.0
    popularity = {}
    for movie_id, _lang, _rd, avg, count in movies:
        avg = avg or 0.0
        count = count or 0
        denom = count + POPULARITY_MIN_VOTES
        popularity[movie_id] = (
            (count / denom) * avg + (POPULARITY_MIN_VOTES / denom) * mean_rating
        )

    return ContentModel(vectors, dict(postings), labels, popularity)


# ---------------------------------------------------------------------------
# Collaborative model
# ---------------------------------------------------------------------------

class CollaborativeModel:
    """
    Item-item neighbourhood CF.

    neighbours[movie_id] -> [(other_movie_id, similarity), ...] truncated to the
    strongest CF_NEIGHBOURS entries.

    Item-item rather than user-user on purpose: the catalog changes far more
    slowly than the user base, so item similarities stay valid between rebuilds
    and can be precomputed, and each item typically has more interactions than
    each user has, which makes the similarities less noisy.
    """

    def __init__(self, neighbours, n_users, n_items):
        self.neighbours = neighbours
        self.n_users = n_users
        self.n_items = n_items

    @property
    def size(self):
        return len(self.neighbours)

    def score(self, user_prefs, exclude=frozenset(), normalise=False):
        """
        Affinity for every movie neighbouring something the user engaged with:

            score(j) = sum_i ( sim(i, j) * pref(i) )          [normalise=False]
            score(j) = sum_i ( sim(i, j) * pref(i) ) / sum_i |sim(i, j)|

        The default is the unnormalised sum, which matters more than it looks.
        Dividing by the summed similarity turns this into a predicted-rating
        estimator: it answers "how much would this user rate j?". But the job
        here is top-N ranking, where the question is "which items should be on
        the shelf?", and for that the *number* of the user's items that vouch for
        j is real evidence, not a bias to divide away. A film neighbouring eight
        things the user liked should outrank one neighbouring a single thing.

        Measured on the offline harness, dropping the normalisation took CF
        HitRate@10 from 1.5% to 5.8% - a ~4x improvement, and the single largest
        win in the whole engine. The option is kept rather than deleted because
        the normalised form is the correct one if this is ever used to *predict a
        rating* rather than to rank a shelf.
        """
        numerator = defaultdict(float)
        denominator = defaultdict(float)

        for movie_id, pref in user_prefs.items():
            for other_id, sim in self.neighbours.get(movie_id, ()):
                if other_id in exclude:
                    continue
                numerator[other_id] += sim * pref
                denominator[other_id] += abs(sim)

        if not normalise:
            return dict(numerator)

        return {
            movie_id: numerator[movie_id] / denominator[movie_id]
            for movie_id in numerator
            if denominator[movie_id] > 1e-12
        }

    def explain(self, user_prefs, movie_id, top_n=3):
        """Which of the user's own items pulled this recommendation in."""
        contributions = []
        for seed_id, pref in user_prefs.items():
            for other_id, sim in self.neighbours.get(seed_id, ()):
                if other_id == movie_id:
                    contributions.append((seed_id, sim * pref))
                    break
        contributions.sort(key=lambda kv: kv[1], reverse=True)
        return [seed_id for seed_id, _ in contributions[:top_n]]


def collect_interactions(include_movielens=False):
    """
    Fold ratings, favourites and watch-later rows into one preference matrix.

    Returns {user_key: {movie_id: preference}} where preference is roughly
    [-1, 1.5]. Explicit ratings are recentred around RATING_MIDPOINT so a 2/10
    becomes a negative signal rather than a weak positive one.

    `user_key` is namespaced: this application's own users are plain ints, while
    MovieLens reference users are ("ml", id) tuples. The two id spaces both start
    at 1 and would otherwise silently merge two different people into one
    profile. Namespacing keeps them distinct in a single matrix, so collaborative
    filtering can learn from 25M reference ratings while `recommend_for_user`
    still looks up a real user by their plain integer id.

    include_movielens is off by default because the personalised path does not
    need the reference rows in memory - CF neighbours are precomputed offline
    (see build_similarity.py). The evaluation harness turns it on.
    """
    interactions = defaultdict(lambda: defaultdict(float))

    for user_id, movie_id, rating, rated_at in db.session.query(
        Rating.user_id, Rating.movie_id, Rating.rating, Rating.rated_at
    ).all():
        if rating is None:
            continue
        signal = (rating - RATING_MIDPOINT) / RATING_MIDPOINT
        interactions[user_id][movie_id] += signal * _decay(rated_at)

    for user_id, movie_id, added_at in db.session.query(
        Favorite.user_id, Favorite.movie_id, Favorite.added_at
    ).all():
        interactions[user_id][movie_id] += FAVOURITE_WEIGHT * _decay(added_at)

    for user_id, movie_id, added_at in db.session.query(
        WatchLater.user_id, WatchLater.movie_id, WatchLater.added_at
    ).all():
        interactions[user_id][movie_id] += WATCHLATER_WEIGHT * _decay(added_at)

    if include_movielens:
        for ml_user_id, movie_id, rating, rated_at in db.session.query(
            MovieLensRating.ml_user_id, MovieLensRating.movie_id,
            MovieLensRating.rating, MovieLensRating.rated_at
        ).all():
            if rating is None:
                continue
            signal = (rating - RATING_MIDPOINT) / RATING_MIDPOINT
            # No recency decay on MovieLens: the dataset ends in Nov 2019, so
            # decaying by wall-clock age would flatten every reference rating to
            # near zero and throw away the entire collaborative signal.
            interactions[("ml", ml_user_id)][movie_id] += signal

    # Clamp so that a user who rated + favourited + watchlisted one film does not
    # get a 2.4x louder vote than everyone else.
    return {
        user_id: {m: max(-1.0, min(1.5, p)) for m, p in prefs.items() if abs(p) > 1e-9}
        for user_id, prefs in interactions.items()
    }


def load_precomputed_neighbours():
    """
    Read the offline-built item-item model from Item_Similarity.

    Returns None when the table is empty, so small/dev datasets fall back to the
    in-process build and `seed_demo_data.py` keeps working unchanged.
    """
    rows = db.session.query(
        ItemSimilarity.movie_id, ItemSimilarity.neighbour_id, ItemSimilarity.similarity
    ).order_by(ItemSimilarity.movie_id, ItemSimilarity.rank).all()

    if not rows:
        return None

    neighbours = defaultdict(list)
    for movie_id, neighbour_id, similarity in rows:
        neighbours[movie_id].append((neighbour_id, similarity))
    return dict(neighbours)


def build_collaborative_model(interactions=None):
    """
    Cosine item-item similarity with significance shrinkage.

    Built by accumulating co-occurrence over each user's own items, which costs
    O(sum over users of k^2) instead of O(items^2) - the interaction matrix is
    extremely sparse, so the pairwise loop only ever touches pairs that actually
    co-occur.
    """
    if interactions is None:
        interactions = collect_interactions()

    if not interactions:
        return CollaborativeModel({}, 0, 0)

    # Similarities are built from POSITIVE interactions only.
    #
    # Cosine over signed preferences multiplies two negatives into a positive,
    # so two films the same user disliked would come out looking similar to each
    # other - and would then be recommended to anyone who liked either one. What
    # we want the matrix to encode is "people who liked i also liked j", so
    # dislikes are excluded here. They are not discarded: the signed preference
    # is still used at scoring time, where a disliked seed correctly pushes its
    # neighbours *down*.
    positive = {
        user_id: {m: p for m, p in prefs.items() if p > 0}
        for user_id, prefs in interactions.items()
    }
    positive = {u: p for u, p in positive.items() if p}

    if not positive:
        return CollaborativeModel({}, 0, 0)

    # Item norms over the whole matrix (needed for the cosine denominator).
    norms = defaultdict(float)
    for prefs in positive.values():
        for movie_id, pref in prefs.items():
            norms[movie_id] += pref * pref
    norms = {m: math.sqrt(v) for m, v in norms.items()}

    dot = defaultdict(float)    # (i, j) -> sum over users of pref_i * pref_j
    co_count = defaultdict(int)  # (i, j) -> how many users back this pair

    for prefs in positive.values():
        items = sorted(prefs.items())
        # A single hyperactive user would otherwise dominate the pair counts.
        if len(items) > 400:
            items = sorted(prefs.items(), key=lambda kv: abs(kv[1]), reverse=True)[:400]
            items.sort()
        for idx, (movie_i, pref_i) in enumerate(items):
            for movie_j, pref_j in items[idx + 1:]:
                key = (movie_i, movie_j)
                dot[key] += pref_i * pref_j
                co_count[key] += 1

    neighbours = defaultdict(list)
    for (movie_i, movie_j), product in dot.items():
        denom = norms.get(movie_i, 0.0) * norms.get(movie_j, 0.0)
        if denom < 1e-12:
            continue
        n_ij = co_count[(movie_i, movie_j)]
        # Shrinkage: a pair supported by few users is pulled toward zero.
        similarity = (product / denom) * (n_ij / (n_ij + CF_SHRINKAGE))
        if abs(similarity) < 1e-6:
            continue
        neighbours[movie_i].append((movie_j, similarity))
        neighbours[movie_j].append((movie_i, similarity))

    trimmed = {}
    for movie_id, entries in neighbours.items():
        entries.sort(key=lambda kv: kv[1], reverse=True)
        trimmed[movie_id] = entries[:CF_NEIGHBOURS]

    return CollaborativeModel(trimmed, len(interactions), len(norms))


# ---------------------------------------------------------------------------
# Model cache
# ---------------------------------------------------------------------------

class ModelCache:
    """
    Keeps the built models in process memory.

    Rebuild triggers: TTL expiry, an explicit invalidate() (called by the admin
    endpoint), or a cheap fingerprint check - counting rows is far cheaper than
    rebuilding, so we compare a fingerprint of the source tables and only pay for
    a rebuild when the data actually moved.
    """

    def __init__(self, ttl=MODEL_TTL_SECONDS):
        self.ttl = ttl
        self._lock = threading.Lock()
        self._content = None
        self._collaborative = None
        self._interactions = None
        self._built_at = 0.0
        self._fingerprint = None
        self._cf_source = None
        self.last_build_seconds = 0.0

    @staticmethod
    def _current_fingerprint():
        return (
            db.session.query(Movie).count(),
            db.session.query(Rating).count(),
            db.session.query(Favorite).count(),
            db.session.query(WatchLater).count(),
            db.session.query(ItemSimilarity).count(),
        )

    def invalidate(self):
        with self._lock:
            self._content = None
            self._collaborative = None
            self._interactions = None
            self._fingerprint = None

    def _is_stale(self):
        if self._content is None or self._collaborative is None:
            return True
        if (time.time() - self._built_at) > self.ttl:
            return True
        return self._current_fingerprint() != self._fingerprint

    def get(self):
        """Returns (content_model, collaborative_model, interactions)."""
        with self._lock:
            if self._is_stale():
                started = time.time()
                self._interactions = collect_interactions()
                self._content = build_content_model()

                # Prefer the offline-built model. Falling back to an in-process
                # build keeps small datasets (and seed_demo_data.py) working, but
                # on a real catalog that path would be prohibitively slow, which
                # is exactly why build_similarity.py exists.
                precomputed = load_precomputed_neighbours()
                if precomputed is not None:
                    n_items = len(precomputed)
                    self._collaborative = CollaborativeModel(precomputed, 0, n_items)
                    self._cf_source = "precomputed"
                else:
                    self._collaborative = build_collaborative_model(self._interactions)
                    self._cf_source = "in-process"

                self._fingerprint = self._current_fingerprint()
                self._built_at = time.time()
                self.last_build_seconds = self._built_at - started
            return self._content, self._collaborative, self._interactions

    def stats(self):
        content, collaborative, interactions = self.get()
        return {
            "movies_indexed": content.size,
            "distinct_features": len(content.postings),
            "items_with_neighbours": collaborative.size,
            "cf_source": self._cf_source,
            "app_users_with_interactions": len(interactions),
            "build_seconds": round(self.last_build_seconds, 4),
            "cached_until": round(self._built_at + self.ttl, 0),
            "total_app_interactions": sum(len(p) for p in interactions.values()),
        }


MODEL_CACHE = ModelCache()


# ---------------------------------------------------------------------------
# User profile + ranking
# ---------------------------------------------------------------------------

def build_user_profile(content_model, user_prefs):
    """
    Rocchio user profile:

        profile = BETA * centroid(liked) - GAMMA * centroid(disliked)

    Subtracting the disliked centroid is what stops the profile from collapsing
    into "this user likes popular things": if they liked one horror film and
    disliked three others, horror gets cancelled out and whatever made the liked
    one different survives.
    """
    liked = defaultdict(float)
    disliked = defaultdict(float)
    n_liked = 0
    n_disliked = 0

    for movie_id, pref in user_prefs.items():
        vec = content_model.vectors.get(movie_id)
        if not vec:
            continue
        if pref > 0:
            _add_scaled(liked, vec, pref)
            n_liked += 1
        elif pref < 0:
            _add_scaled(disliked, vec, -pref)
            n_disliked += 1

    if n_liked:
        for token in liked:
            liked[token] /= n_liked
    if n_disliked:
        for token in disliked:
            disliked[token] /= n_disliked

    profile = defaultdict(float)
    _add_scaled(profile, liked, ROCCHIO_BETA)
    _add_scaled(profile, disliked, -ROCCHIO_GAMMA)

    trimmed = {t: v for t, v in profile.items() if abs(v) > 1e-9}

    # Keep only the strongest features (by magnitude, so a strong negative
    # survives too) before normalising - see MAX_PROFILE_TOKENS.
    if len(trimmed) > MAX_PROFILE_TOKENS:
        top = sorted(trimmed.items(), key=lambda kv: abs(kv[1]), reverse=True)
        trimmed = dict(top[:MAX_PROFILE_TOKENS])

    # Negative components are useful for ranking but must not be allowed to
    # dominate the cosine, so keep them but renormalise the whole thing.
    return _l2_normalise(trimmed)


def apply_popularity_prior(content_scores, popularity, weight=CONTENT_POPULARITY_PRIOR):
    """
    Mix a Bayesian popularity prior into raw content-similarity scores.

    Both sides are min-max normalised first so the blend is between comparable
    quantities rather than between a cosine and a rating average.
    See CONTENT_POPULARITY_PRIOR for the measurements behind the default.
    """
    if not content_scores or weight <= 0:
        return content_scores

    normalised = _min_max_normalise(content_scores)
    # Only candidates the content model actually surfaced are considered; the
    # prior re-ranks that set rather than reintroducing the whole catalog.
    prior = _min_max_normalise({m: popularity.get(m, 0.0) for m in content_scores})

    return {
        movie_id: (1.0 - weight) * normalised[movie_id] + weight * prior.get(movie_id, 0.0)
        for movie_id in normalised
    }


def content_weight_for(n_interactions):
    """
    Adaptive blend weight (see the DENSE_HISTORY_N comment for the tuning data).

    0 interactions   -> 1.00 (pure content; CF has no row for this user at all)
    10+ interactions -> 0.60 (tuned optimum: content-led, CF as a second opinion)
    """
    if n_interactions <= 0:
        return 1.0
    ratio = min(1.0, n_interactions / float(DENSE_HISTORY_N))
    return max(MIN_CONTENT_WEIGHT, 1.0 - ratio * (1.0 - MIN_CONTENT_WEIGHT))


def popularity_fallback(content_model, exclude, limit):
    """Cold start: nothing is known about this user, so rank by Bayesian popularity."""
    ranked = sorted(
        (
            (movie_id, score)
            for movie_id, score in content_model.popularity.items()
            if movie_id not in exclude
        ),
        key=lambda kv: kv[1],
        reverse=True,
    )
    return [
        {"movie_id": movie_id, "score": round(score, 6), "source": "popularity"}
        for movie_id, score in ranked[:limit]
    ]


def recommend_for_user(user_id, limit=20, explain=False):
    """
    Hybrid recommendations for one user.

    Returns a list of {movie_id, score, source, ...} dicts, best first.
    """
    content_model, cf_model, interactions = MODEL_CACHE.get()
    user_prefs = interactions.get(user_id, {})
    seen = set(user_prefs.keys())

    if not user_prefs:
        return {
            "strategy": "popularity",
            "content_weight": 1.0,
            "interaction_count": 0,
            "results": popularity_fallback(content_model, seen, limit),
        }

    profile = build_user_profile(content_model, user_prefs)
    content_scores = content_model.score(profile, exclude=seen) if profile else {}
    content_scores = apply_popularity_prior(content_scores, content_model.popularity)
    cf_scores = cf_model.score(user_prefs, exclude=seen)

    alpha = content_weight_for(len(user_prefs))

    norm_content = _min_max_normalise(content_scores)
    norm_cf = _min_max_normalise(cf_scores)

    blended = {}
    for movie_id in set(norm_content) | set(norm_cf):
        c = norm_content.get(movie_id, 0.0)
        f = norm_cf.get(movie_id, 0.0)
        blended[movie_id] = alpha * c + (1.0 - alpha) * f

    ranked = sorted(blended.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    # If both models came up short (a brand new catalog, say), top the list up
    # with popularity so the shelf is never half empty.
    if len(ranked) < limit:
        already = seen | {m for m, _ in ranked}
        filler = popularity_fallback(content_model, already, limit - len(ranked))
    else:
        filler = []

    results = []
    for movie_id, score in ranked:
        entry = {
            "movie_id": movie_id,
            "score": round(score, 6),
            "content_score": round(norm_content.get(movie_id, 0.0), 6),
            "cf_score": round(norm_cf.get(movie_id, 0.0), 6),
            "source": _source_label(norm_content.get(movie_id), norm_cf.get(movie_id)),
        }
        if explain:
            entry["because_of_features"] = content_model.explain(profile, movie_id)
            entry["because_you_liked"] = cf_model.explain(user_prefs, movie_id)
        results.append(entry)

    results.extend(filler)

    return {
        "strategy": "hybrid",
        "content_weight": round(alpha, 3),
        "interaction_count": len(user_prefs),
        "results": results,
    }


def _source_label(content_score, cf_score):
    if content_score and cf_score:
        return "hybrid"
    if cf_score:
        return "collaborative"
    return "content"


def similar_movies(movie_id, limit=12, strategy="hybrid"):
    """
    "More like this" for a single film - no user needed.

    strategy: "content" (metadata cosine), "collaborative" (item-item CF
    neighbours) or "hybrid" (both, normalised and blended evenly).
    """
    content_model, cf_model, _ = MODEL_CACHE.get()
    exclude = {movie_id}

    content_scores = {}
    if strategy in ("content", "hybrid"):
        vec = content_model.vectors.get(movie_id)
        if vec:
            content_scores = content_model.score(vec, exclude=exclude)

    cf_scores = {}
    if strategy in ("collaborative", "hybrid"):
        cf_scores = {
            other: sim
            for other, sim in cf_model.neighbours.get(movie_id, ())
            if other not in exclude
        }

    if strategy == "content":
        blended = content_scores
    elif strategy == "collaborative":
        blended = cf_scores
    else:
        norm_content = _min_max_normalise(content_scores)
        norm_cf = _min_max_normalise(cf_scores)
        # Even split here: unlike the personalised feed there is no history to
        # tell us which signal deserves more trust for this particular item.
        blended = {
            m: 0.5 * norm_content.get(m, 0.0) + 0.5 * norm_cf.get(m, 0.0)
            for m in set(norm_content) | set(norm_cf)
        }

    ranked = sorted(blended.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"movie_id": m, "score": round(s, 6)} for m, s in ranked]


def hydrate(entries):
    """
    Attach the poster/title fields the UI needs, in one query, preserving order.
    """
    if not entries:
        return []
    movie_ids = [e["movie_id"] for e in entries]
    rows = (
        db.session.query(
            Movie.movie_id, Movie.title, Movie.poster_path, Movie.rating_avg, Movie.release_date
        )
        .filter(Movie.movie_id.in_(movie_ids))
        .all()
    )
    by_id = {r.movie_id: r for r in rows}

    hydrated = []
    for entry in entries:
        row = by_id.get(entry["movie_id"])
        if not row:
            continue
        hydrated.append({
            **entry,
            "title": row.title,
            "poster_path": row.poster_path,
            "rating_avg": row.rating_avg,
            "release_date": row.release_date,
        })
    return hydrated
