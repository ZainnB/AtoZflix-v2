from app.models.models import Actor,Movie,MoviesActors,Genre,MoviesGenres
from app import db
from flask import Blueprint,request,jsonify
from sqlalchemy import func
actor_bp=Blueprint('actor',__name__)


@actor_bp.route('/api/movie_cast', methods=['GET'])
def get_movie_cast():
    """
    Billed cast for one film, in billing order.

    Character name and billing live on the join table, so an actor can play a
    different role in every film they appear in.
    """
    movie_id = request.args.get('movie_id', type=int)
    limit = request.args.get('limit', default=20, type=int)

    if not movie_id:
        return jsonify({"status": "error", "message": "movie_id is required"}), 400

    try:
        rows = (
            db.session.query(
                Actor.actor_id,
                Actor.actor_name,
                Actor.profile_path,
                MoviesActors.character_name,
                MoviesActors.billing_order,
            )
            .join(MoviesActors, Actor.actor_id == MoviesActors.actor_id)
            .filter(MoviesActors.movie_id == movie_id)
            # NULLs sort last so uncredited entries do not lead the cast list.
            .order_by(MoviesActors.billing_order.is_(None),
                      MoviesActors.billing_order.asc())
            .limit(limit)
            .all()
        )

        cast = [
            {
                "actor_id": r.actor_id,
                "actor_name": r.actor_name,
                "profile_path": r.profile_path,
                "character_name": r.character_name,
                "billing_order": r.billing_order,
            }
            for r in rows
        ]
        return jsonify({"status": "success", "cast": cast}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@actor_bp.route('/api/actor_details', methods=['GET'])
def get_actor_details():
    """
    Profile for one actor: biography, computed career stats, and filmography.

    The biography comes from TMDb's per-person endpoint, which is one request per
    actor - impractical for 45,000 of them up front. So it is fetched the first
    time someone opens this actor and then cached on the row. `details_fetched`
    marks the lookup as done so an actor with a genuinely blank biography is not
    re-requested on every view.
    """
    actor_id = request.args.get('actor_id', type=int)
    if not actor_id:
        return jsonify({"status": "error", "message": "actor_id is required"}), 400

    try:
        actor = db.session.get(Actor, actor_id)
        if not actor:
            return jsonify({"status": "error", "message": "Actor not found"}), 404

        if not actor.details_fetched:
            try:
                from app.utils.tmdb_importer import fetch_person
                person = fetch_person(actor_id)
                actor.biography = person.get("biography") or None
                actor.birthday = person.get("birthday") or None
                actor.deathday = person.get("deathday") or None
                actor.place_of_birth = person.get("place_of_birth") or None
                if person.get("profile_path"):
                    actor.profile_path = person["profile_path"]
                if person.get("popularity") is not None:
                    actor.popularity = person["popularity"]
                actor.details_fetched = True
                db.session.commit()
            except Exception:
                # A TMDb outage must not take the page down - the filmography
                # below is local data and is the substance of the page anyway.
                db.session.rollback()

        filmography = (
            db.session.query(
                Movie.movie_id, Movie.title, Movie.poster_path, Movie.release_date,
                Movie.rating_avg, MoviesActors.character_name,
            )
            .join(MoviesActors, Movie.movie_id == MoviesActors.movie_id)
            .filter(MoviesActors.actor_id == actor_id)
            .order_by(Movie.rating_avg.desc())
            .all()
        )

        # Career stats, computed from the local catalog rather than fetched.
        years = [f.release_date.year for f in filmography if f.release_date]
        ratings = [f.rating_avg for f in filmography if f.rating_avg]

        top_genres = (
            db.session.query(Genre.genre_name, func.count().label("n"))
            .join(MoviesGenres, Genre.genre_id == MoviesGenres.genre_id)
            .join(MoviesActors, MoviesGenres.movie_id == MoviesActors.movie_id)
            .filter(MoviesActors.actor_id == actor_id)
            .group_by(Genre.genre_name)
            .order_by(func.count().desc())
            .limit(4)
            .all()
        )

        return jsonify({
            "status": "success",
            "actor": {
                "actor_id": actor.actor_id,
                "actor_name": actor.actor_name,
                "profile_path": actor.profile_path,
                "biography": actor.biography,
                "birthday": actor.birthday,
                "deathday": actor.deathday,
                "place_of_birth": actor.place_of_birth,
            },
            "stats": {
                "movie_count": len(filmography),
                "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
                "first_year": min(years) if years else None,
                "last_year": max(years) if years else None,
                "top_genres": [g.genre_name for g in top_genres],
            },
            "filmography": [
                {
                    "movie_id": f.movie_id,
                    "title": f.title,
                    "poster_path": f.poster_path,
                    "release_date": f.release_date,
                    "rating_avg": f.rating_avg,
                    "character_name": f.character_name,
                }
                for f in filmography
            ],
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@actor_bp.route('/api/related_actors', methods=['GET'])
def get_related_actors():
    """
    Actors who most often share a cast list with this one.

    Pure co-occurrence over the join table - the same "appears together"
    intuition behind item-item collaborative filtering, applied to people.
    """
    actor_id = request.args.get('actor_id', type=int)
    limit = request.args.get('limit', default=12, type=int)

    if not actor_id:
        return jsonify({"status": "error", "message": "actor_id is required"}), 400

    try:
        # Films this actor is in, then everyone else who appears in them.
        their_movies = (
            db.session.query(MoviesActors.movie_id)
            .filter(MoviesActors.actor_id == actor_id)
            .subquery()
        )

        rows = (
            db.session.query(
                Actor.actor_id, Actor.actor_name, Actor.profile_path,
                func.count().label("shared"),
            )
            .join(MoviesActors, Actor.actor_id == MoviesActors.actor_id)
            .filter(MoviesActors.movie_id.in_(db.session.query(their_movies.c.movie_id)))
            .filter(Actor.actor_id != actor_id)
            .group_by(Actor.actor_id)
            .order_by(func.count().desc())
            .limit(limit)
            .all()
        )

        return jsonify({
            "status": "success",
            "actors": [
                {
                    "actor_id": r.actor_id,
                    "actor_name": r.actor_name,
                    "profile_path": r.profile_path,
                    "shared_movies": r.shared,
                }
                for r in rows
            ],
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@actor_bp.route('/api/top-actors', methods=['GET'])
def get_top_actors():
    """
    Most-featured actors, ranked by the summed rating of everything they are in.

    Summed rather than averaged on purpose: an average would put an unknown with
    one well-reviewed credit above an actor with twenty strong films, which is
    not what "top actors" means to someone browsing.
    """
    limit = request.args.get('limit', default=20, type=int)
    limit = max(1, min(200, limit))

    try:
        # The previous version opened with `Actor.query.all()` and printed it -
        # loading all 45,009 actor rows into memory on every request, for a
        # result that was then thrown away.
        results = (
            db.session.query(
                Actor.actor_id,
                Actor.actor_name,
                Actor.profile_path,
                func.sum(Movie.rating_avg).label("total_rating"),
                func.count(MoviesActors.movie_id).label("movie_count"),
            )
            .join(MoviesActors, Actor.actor_id == MoviesActors.actor_id)
            .join(Movie, MoviesActors.movie_id == Movie.movie_id)
            .group_by(Actor.actor_id)
            # Two or more credits, so a single-appearance blockbuster extra does
            # not outrank a working actor.
            .having(func.count(MoviesActors.movie_id) >= 2)
            .order_by(func.sum(Movie.rating_avg).desc())
            .limit(limit)
            .all()
        )

        actors = [
            {
                "actor_id": r.actor_id,
                "actor_name": r.actor_name,
                "profile_path": r.profile_path,
                "movie_count": r.movie_count,
            }
            for r in results
        ]
        return jsonify({"status": "success", "data": actors}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Search a movie given an actor
@actor_bp.route("/api/search_actor", methods=["GET"])
def search_movie_by_actor():
    actor_id = request.args.get("actor_id", type=int)
    search_query = request.args.get("query", type=str)
    limit = request.args.get("limit", default=10, type=int)

    try:
        if actor_id:
            actor = db.session.query(Actor).filter_by(actor_id=actor_id).first()
            if not actor:
                return jsonify({"movies": [], "message": "Actor not found"}), 404
            search_query = actor.actor_name

        if not search_query:
            return jsonify({"error": "No search query or actor_id provided"}), 400
        matching_actors = (
            db.session.query(Actor.actor_id)
            .filter(Actor.actor_name.ilike(f"%{search_query}%"))
            .limit(limit)
            .all()
        )
        if not matching_actors:
            return jsonify({"movies": [], "message": "No actors found"}), 404

        actor_ids = [actor_id for (actor_id,) in matching_actors]
        movies = (
            db.session.query(Movie.poster_path, Movie.movie_id, Movie.title, Movie.rating_avg)
            .join(MoviesActors, MoviesActors.movie_id == Movie.movie_id)
            .filter(MoviesActors.actor_id.in_(actor_ids))
            .distinct()
            .all()
        )

        formatted_movies = [
            {"poster_path": r.poster_path, "movie_id": r.movie_id,
             "title": r.title, "rating_avg": r.rating_avg}
            for r in movies
        ]

        return jsonify({"movies": formatted_movies}), 200

    except Exception as e:
        print(f"Error fetching actor movies: {e}")
        return jsonify({"error": "Failed to fetch actor movies"}), 500

# Getting movies by actor
@actor_bp.route('/api/actor-movies', methods=['GET'])
def get_actor_movies():
    try:
        # Get actor_id and limit from request args
        actor_id = request.args.get('actor_id', type=int)
        limit = request.args.get('limit', default=5, type=int)

        if not actor_id:
            return jsonify({"status": "error", "message": "actor_id parameter is required"}), 400

        # Fetch movies associated with the actor, ordered by rating
        movies = (
            db.session.query(Movie.movie_id, Movie.poster_path, Movie.title, Movie.rating_avg)
            .join(MoviesActors, MoviesActors.movie_id == Movie.movie_id)
            .filter(MoviesActors.actor_id == actor_id)
            .order_by(Movie.rating_avg.desc())
            .limit(limit)
            .all()
        )

        result = [
            {"poster_path": r.poster_path, "movie_id": r.movie_id,
             "title": r.title, "rating_avg": r.rating_avg}
            for r in movies
        ]

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
