<!--
  Movie detail page.

  Order is deliberate: hero (identity + actions), then Cast, then the two
  recommendation shelves. Cast comes first because it is factual information
  about the film you are already looking at; the recommendation rows are about
  leaving this page, so they sit below.
-->
<script>
    import { onMount } from "svelte";
    import { redirectToRegisterIfNotAuthenticated, getCurrentUser } from "/src/utils/auth.js";
    import Navbar from "../Home/Navbar2.svelte";
    import Footer from "../Register/Footer1.svelte";
    import Line from "../Register/Line.svelte";
    import RatingModal from "../RatingModal/RatingModal.svelte";
    import SimilarMovies from "../SimilarMovies/+page.svelte";
    import CastRow from "../CastRow/+page.svelte";
    import { api } from '../../../lib/api.js';

    let isRatingOpen = false;
    let movie_id;
    let movie = null;
    let error = null;
    let loading = true;
    let isFavourite = false;
    let isInWatchlist = false;
    let user_id;
    let busy = { fav: false, watch: false };

    onMount(async () => {
        redirectToRegisterIfNotAuthenticated();
        const user = getCurrentUser();
        user_id = user?.userId;
        movie_id = new URLSearchParams(window.location.search).get("movie_id");

        if (!movie_id) {
            error = "No movie selected.";
            loading = false;
            return;
        }

        try {
            const data = await api.get(`/api/movie_details?movie_id=${movie_id}`);
            movie = data.movie;
        } catch (err) {
            error = err.message || "Could not load this film.";
        } finally {
            loading = false;
        }

        if (user_id && movie) {
            // Fired together rather than in sequence: they are independent, and
            // awaiting them one after the other doubles the time before the
            // buttons show their real state.
            const [fav, watch] = await Promise.allSettled([
                api.get(`/api/check_favourite?movie_id=${movie_id}`),
                api.get(`/api/check_watchlist?movie_id=${movie_id}`),
            ]);
            if (fav.status === "fulfilled") isFavourite = fav.value.is_favourite;
            if (watch.status === "fulfilled") isInWatchlist = watch.value.is_in_watchlist;
        }
    });

    const toggleFavourite = async () => {
        if (busy.fav) return;
        busy.fav = true;
        const previous = isFavourite;
        isFavourite = !isFavourite;          // optimistic
        try {
            await api.post(previous ? "/api/remove_favourite" : "/api/add_favourite", { movie_id });
        } catch (err) {
            isFavourite = previous;          // roll back on failure
            console.error("Failed to update favourite status:", err);
        } finally {
            busy.fav = false;
        }
    };

    const toggleWatchlist = async () => {
        if (busy.watch) return;
        busy.watch = true;
        const previous = isInWatchlist;
        isInWatchlist = !isInWatchlist;
        try {
            await api.post(previous ? "/api/remove_from_watchlist" : "/api/add_to_watchlist", { movie_id });
        } catch (err) {
            isInWatchlist = previous;
            console.error("Failed to update watchlist status:", err);
        } finally {
            busy.watch = false;
        }
    };

    function runtimeLabel(minutes) {
        if (!minutes) return null;
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return h ? `${h}h ${m}m` : `${m}m`;
    }

    function money(value) {
        if (!value) return null;
        if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
        if (value >= 1e6) return `$${Math.round(value / 1e6)}M`;
        return `$${value.toLocaleString()}`;
    }

    $: year = movie?.release_date ? new Date(movie.release_date).getFullYear() : null;
</script>

<svelte:head>
    <title>{movie ? `${movie.title} — AtoZflix` : "AtoZflix"}</title>
</svelte:head>

<RatingModal bind:show={isRatingOpen} {movie_id} />

<div class="page">
    <div class="navbar-wrapper"><Navbar /></div>

    {#if loading}
        <div class="hero-wrap">
            <div class="shell hero">
                <div class="skeleton poster-skeleton"></div>
                <div class="info">
                    <div class="skeleton line lg"></div>
                    <div class="skeleton line md"></div>
                    <div class="skeleton block"></div>
                </div>
            </div>
        </div>
    {:else if error}
        <div class="shell state">
            <h1>Something went wrong</h1>
            <p>{error}</p>
            <a class="btn primary" href="/components/Home">Back home</a>
        </div>
    {:else if movie}
        <header class="hero-wrap">
            {#if movie.backdrop_path}
                <div
                    class="backdrop"
                    style="background-image:url('https://image.tmdb.org/t/p/original{movie.backdrop_path}')"
                ></div>
            {/if}
            <div class="scrim"></div>

            <div class="shell hero">
                <div class="poster">
                    {#if movie.poster_path}
                        <img
                            src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
                            alt={movie.title}
                        />
                    {:else}
                        <div class="poster-fallback">{movie.title}</div>
                    {/if}
                </div>

                <div class="info">
                    <h1>{movie.title}</h1>
                    {#if movie.original_title && movie.original_title !== movie.title}
                        <p class="original">{movie.original_title}</p>
                    {/if}

                    <div class="meta-line">
                        {#if movie.rating_avg}
                            <span class="score">★ {Number(movie.rating_avg).toFixed(1)}</span>
                        {/if}
                        {#if movie.rating_count}
                            <span class="votes">{Number(movie.rating_count).toLocaleString()} votes</span>
                        {/if}
                        {#if year}<span class="dot">·</span><span>{year}</span>{/if}
                        {#if runtimeLabel(movie.runtime)}
                            <span class="dot">·</span><span>{runtimeLabel(movie.runtime)}</span>
                        {/if}
                        {#if movie.adult}<span class="badge-18">18+</span>{/if}
                    </div>

                    {#if movie.genres?.length}
                        <div class="chips">
                            {#each movie.genres as genre}
                                <a class="chip" href={`/components/Genre?genre=${encodeURIComponent(genre)}`}>{genre}</a>
                            {/each}
                        </div>
                    {/if}

                    {#if movie.overview}
                        <p class="overview">{movie.overview}</p>
                    {/if}

                    <div class="actions">
                        <button
                            class="btn"
                            class:active={isFavourite}
                            on:click={toggleFavourite}
                            disabled={busy.fav}
                            aria-pressed={isFavourite}
                        >
                            <span aria-hidden="true">{isFavourite ? "♥" : "♡"}</span>
                            {isFavourite ? "In Favourites" : "Add to Favourites"}
                        </button>

                        <button
                            class="btn"
                            class:active={isInWatchlist}
                            on:click={toggleWatchlist}
                            disabled={busy.watch}
                            aria-pressed={isInWatchlist}
                        >
                            <span aria-hidden="true">{isInWatchlist ? "✓" : "+"}</span>
                            {isInWatchlist ? "In Watch Later" : "Watch Later"}
                        </button>

                        <button class="btn primary" on:click={() => (isRatingOpen = true)}>
                            Rate this film
                        </button>
                    </div>

                    <dl class="facts">
                        {#if movie.production_countries?.length}
                            <div><dt>Country</dt><dd>{movie.production_countries.join(", ")}</dd></div>
                        {/if}
                        {#if movie.production_companies}
                            <div><dt>Studio</dt><dd>{movie.production_companies}</dd></div>
                        {/if}
                        {#if money(movie.budget)}
                            <div><dt>Budget</dt><dd>{money(movie.budget)}</dd></div>
                        {/if}
                        {#if money(movie.revenue)}
                            <div><dt>Revenue</dt><dd>{money(movie.revenue)}</dd></div>
                        {/if}
                    </dl>
                </div>
            </div>
        </header>

        <!-- Keyed on movie_id so navigating between films remounts these and
             refetches, instead of showing the previous film's data. -->
        {#key movie_id}
            <CastRow {movie_id} limit={20} />

            <SimilarMovies
                {movie_id}
                limit={20}
                heading="More Like This"
                subtitle="Blended from what viewers watch together and shared cast, crew and themes"
            />

            <SimilarMovies
                {movie_id}
                limit={20}
                strategy="content"
                heading="Similar in Style"
                subtitle="Matched purely on genre, keywords, cast and crew"
            />
        {/key}
    {/if}

    <Line />
    <Footer />
</div>

<style>
    .page {
        min-height: 100vh;
        background: var(--bg);
        color: var(--text);
        font-family: var(--font);
    }

    .navbar-wrapper {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 10;
    }

    .hero-wrap {
        position: relative;
        padding-top: calc(var(--nav-height) + 2.5rem);
        padding-bottom: 2.5rem;
        overflow: hidden;
        border-bottom: 1px solid var(--border);
    }

    .backdrop {
        position: absolute;
        inset: 0;
        background-size: cover;
        background-position: center 20%;
        /* Blur plus a heavy scrim: the backdrop is atmosphere, and unblurred it
           competes with the text sitting on top of it. */
        filter: blur(1.5px);
        transform: scale(1.06);
        z-index: 0;
    }

    .scrim {
        position: absolute;
        inset: 0;
        z-index: 1;
        background:
            linear-gradient(to right, rgba(10, 10, 13, 0.96) 0%, rgba(10, 10, 13, 0.78) 55%, rgba(10, 10, 13, 0.6) 100%),
            linear-gradient(to bottom, rgba(10, 10, 13, 0.5), var(--bg) 96%);
    }

    .hero {
        position: relative;
        z-index: 2;
        display: grid;
        grid-template-columns: minmax(180px, 300px) minmax(0, 1fr);
        gap: clamp(1.5rem, 4vw, 3rem);
        align-items: start;
    }

    .poster {
        aspect-ratio: 2 / 3;
        border-radius: var(--radius-lg);
        overflow: hidden;
        background: var(--surface-2);
        box-shadow: var(--shadow-lg);
    }

    .poster img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .poster-fallback {
        width: 100%;
        height: 100%;
        display: grid;
        place-items: center;
        padding: 1rem;
        text-align: center;
        color: var(--text-faint);
        background: linear-gradient(160deg, var(--surface-3), var(--surface));
    }

    .info {
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
        min-width: 0;
    }

    h1 {
        margin: 0;
        font-size: clamp(1.9rem, 4.5vw, 3.1rem);
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.05;
        text-wrap: balance;
    }

    .original {
        margin: -0.4rem 0 0;
        font-size: 0.95rem;
        font-style: italic;
        color: var(--text-faint);
    }

    .meta-line {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        color: var(--text-dim);
    }

    .score {
        color: var(--star);
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }

    .votes { color: var(--text-faint); }
    .dot { color: var(--text-faint); }

    .badge-18 {
        padding: 0.1rem 0.4rem;
        border: 1px solid var(--danger);
        border-radius: var(--radius-sm);
        color: var(--danger);
        font-size: 0.72rem;
        font-weight: 700;
    }

    .chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
    }

    .chip {
        padding: 0.28rem 0.75rem;
        border-radius: var(--radius-pill);
        border: 1px solid var(--accent-dim);
        background: var(--accent-wash);
        color: var(--accent);
        font-size: 0.78rem;
        font-weight: 600;
        text-decoration: none;
        transition: background 0.2s var(--ease), color 0.2s var(--ease);
    }

    .chip:hover { background: var(--accent-strong); color: #06201d; }

    .overview {
        margin: 0;
        max-width: 68ch;
        font-size: 0.98rem;
        line-height: 1.65;
        color: var(--text-dim);
    }

    .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-top: 0.3rem;
    }

    .btn {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.65rem 1.15rem;
        border-radius: var(--radius-pill);
        border: 1px solid var(--border-strong);
        background: rgba(255, 255, 255, 0.06);
        color: var(--text);
        font-family: inherit;
        font-size: 0.88rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s var(--ease), border-color 0.2s var(--ease),
            transform 0.15s var(--ease);
    }

    .btn:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.12);
        transform: translateY(-1px);
    }

    .btn:disabled { opacity: 0.55; cursor: progress; }

    /* Active state reads as "this is on" rather than "click to remove" - the
       old version turned the button red, which looks like a warning. */
    .btn.active {
        background: var(--accent-wash);
        border-color: var(--accent);
        color: var(--accent);
    }

    .btn.primary {
        background: var(--accent-strong);
        border-color: var(--accent-strong);
        color: #06201d;
    }

    .btn.primary:hover:not(:disabled) { background: var(--accent); }

    .facts {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
        gap: 0.75rem 1.5rem;
        margin: 0.6rem 0 0;
        padding-top: 0.9rem;
        border-top: 1px solid var(--border);
    }

    .facts dt {
        font-size: 0.72rem;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: var(--text-faint);
        margin-bottom: 0.15rem;
    }

    .facts dd {
        margin: 0;
        font-size: 0.88rem;
        color: var(--text-dim);
    }

    .state {
        padding-top: calc(var(--nav-height) + 4rem);
        padding-bottom: 4rem;
        text-align: center;
    }

    .poster-skeleton { aspect-ratio: 2 / 3; border-radius: var(--radius-lg); }
    .line { height: 1rem; border-radius: var(--radius-sm); margin-bottom: 0.8rem; }
    .line.lg { height: 2.8rem; width: min(60%, 24rem); }
    .line.md { width: min(35%, 14rem); }
    .block { height: 9rem; border-radius: var(--radius); }

    @media (max-width: 780px) {
        .hero {
            grid-template-columns: 1fr;
            justify-items: center;
            text-align: center;
        }

        .poster { width: min(230px, 62vw); }
        .info { align-items: center; }
        .overview { text-align: left; }
        .actions { justify-content: center; }
        .facts { text-align: left; width: 100%; }
    }
</style>
