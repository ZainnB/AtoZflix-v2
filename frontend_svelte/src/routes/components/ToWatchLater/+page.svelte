<!--
  The signed-in user's watch-later list.

  Same contract as Favourites: the caller comes from the JWT, never the URL.
-->
<script>
    import { onMount } from "svelte";
    import { redirectToRegisterIfNotAuthenticated } from "/src/utils/auth.js";
    import Navbar from "../Home/Navbar2.svelte";
    import Footer from "../Register/Footer1.svelte";
    import Line from "../Register/Line.svelte";
    import MovieCard from "$lib/components/MovieCard.svelte";
    import MovieGrid from "$lib/components/MovieGrid.svelte";
    import { api } from "../../../lib/api.js";

    let watchlist = [];
    let isLoading = true;
    let error = "";
    let removing = new Set();

    onMount(async () => {
        redirectToRegisterIfNotAuthenticated();
        await fetchWatchlist();
    });

    async function fetchWatchlist() {
        try {
            const data = await api.get("/api/get_watchlist");
            watchlist = data.watchlist || [];
            error = "";
        } catch (err) {
            error = err.message || "Failed to load your watch list.";
        } finally {
            isLoading = false;
        }
    }

    async function removeFromWatchlist(movieId) {
        if (removing.has(movieId)) return;
        removing = new Set(removing).add(movieId);

        const snapshot = watchlist;
        watchlist = watchlist.filter((m) => m.movie_id !== movieId);

        try {
            await api.post("/api/remove_from_watchlist", { movie_id: movieId });
        } catch (e) {
            watchlist = snapshot;
            error = e.message || "Could not remove that film.";
        } finally {
            const next = new Set(removing);
            next.delete(movieId);
            removing = next;
        }
    }

    function formatDate(value) {
        if (!value) return null;
        const d = new Date(value);
        return Number.isNaN(d.getTime())
            ? null
            : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
    }
</script>

<svelte:head><title>Watch Later — AtoZflix</title></svelte:head>

<div class="page">
    <div class="navbar-wrapper"><Navbar /></div>

    <header class="hero">
        <div class="shell">
            <p class="eyebrow">Your library</p>
            <h1>Watch Later</h1>
            {#if !isLoading && watchlist.length}
                <p class="lede">
                    {watchlist.length} {watchlist.length === 1 ? "film" : "films"} queued up.
                </p>
            {/if}
        </div>
    </header>

    <section class="shell listing">
        {#if error && !watchlist.length}
            <p class="error">{error}</p>
        {/if}

        <MovieGrid
            loading={isLoading}
            empty={!isLoading && watchlist.length === 0}
            emptyTitle="Nothing queued yet"
            emptyBody="Save anything you want to get to later and it will wait for you here."
            emptyActionHref="/components/Home"
            emptyActionLabel="Browse the catalog"
        >
            {#each watchlist as movie (movie.movie_id)}
                <div class="item">
                    <MovieCard
                        movie_id={movie.movie_id}
                        poster_path={movie.poster_path}
                        title={movie.title}
                        rating={movie.rating_avg}
                    />
                    <div class="item-foot">
                        {#if formatDate(movie.added_at)}
                            <span class="added">Saved {formatDate(movie.added_at)}</span>
                        {/if}
                        <button
                            class="remove"
                            on:click={() => removeFromWatchlist(movie.movie_id)}
                            disabled={removing.has(movie.movie_id)}
                            aria-label={`Remove ${movie.title ?? "this film"} from watch later`}
                        >
                            Remove
                        </button>
                    </div>
                </div>
            {/each}
        </MovieGrid>
    </section>

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

    .hero {
        padding-top: calc(var(--nav-height) + 2.5rem);
        padding-bottom: 1.75rem;
        background:
            radial-gradient(120% 100% at 20% 0%, rgba(45, 212, 191, 0.10), transparent 60%),
            linear-gradient(to bottom, var(--surface), var(--bg));
        border-bottom: 1px solid var(--border);
    }

    .eyebrow {
        margin: 0 0 0.3rem;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--accent);
    }

    h1 {
        margin: 0 0 0.4rem;
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    .lede {
        margin: 0;
        color: var(--text-dim);
        font-size: 0.95rem;
    }

    .listing { padding-block: 2.25rem 3.5rem; }

    .error {
        margin-bottom: 1rem;
        padding: 0.75rem 1rem;
        border-radius: var(--radius);
        border: 1px solid var(--danger-dim);
        background: rgba(248, 113, 113, 0.1);
        color: var(--danger);
        font-size: 0.9rem;
    }

    .item { display: flex; flex-direction: column; gap: 0.45rem; }

    .item-foot {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
    }

    .added { font-size: 0.7rem; color: var(--text-faint); }

    .remove {
        padding: 0.2rem 0.55rem;
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-pill);
        background: none;
        color: var(--text-faint);
        font-family: inherit;
        font-size: 0.7rem;
        font-weight: 600;
        cursor: pointer;
        transition: color 0.2s var(--ease), border-color 0.2s var(--ease),
            background 0.2s var(--ease);
    }

    .remove:hover:not(:disabled) {
        color: var(--danger);
        border-color: var(--danger);
        background: rgba(248, 113, 113, 0.1);
    }

    .remove:disabled { opacity: 0.4; cursor: progress; }
</style>
