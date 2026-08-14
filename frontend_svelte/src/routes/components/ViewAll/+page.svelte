<!--
  "View all" listing behind every carousel's View all link.

  Handles two shapes of source:
    * paged endpoints  (latest, top_rated) - support limit + offset
    * facet endpoints  (genre, country)    - take a value and no offset

  The previous version computed pagination from `data.total_movies`, which no
  endpoint has ever returned, so totalPages was always 0 and the next-page
  button could never fire. Replaced with an offset-based "Load more" that stops
  when a page comes back short - which needs no total from the server.
-->
<script>
    import { onMount } from "svelte";
    import Navbar from "../Home/Navbar2.svelte";
    import Footer from "../Register/Footer1.svelte";
    import Line from "../Register/Line.svelte";
    import MovieCard from "$lib/components/MovieCard.svelte";
    import MovieGrid from "$lib/components/MovieGrid.svelte";
    import { api } from "../../../lib/api.js";
    import { redirectToRegisterIfNotAuthenticated } from "/src/utils/auth.js";

    const PAGE_SIZE = 60;
    const FACET_TYPES = new Set(["genre", "country"]);

    let movies = [];
    let type = "";
    let value = "";
    let heading = "";
    let offset = 0;
    let loading = true;
    let loadingMore = false;
    let exhausted = false;
    let error = "";

    onMount(async () => {
        redirectToRegisterIfNotAuthenticated();
        const params = new URLSearchParams(window.location.search);
        type = params.get("type") || "latest";
        value = params.get("value") || "";
        heading = params.get("heading") || "Browse";
        await load();
    });

    function buildUrl() {
        if (FACET_TYPES.has(type)) {
            // Facet endpoints have no offset, so everything is fetched in one go.
            return `/api/${type}?${type}=${encodeURIComponent(value)}&limit=${PAGE_SIZE * 4}`;
        }
        return `/api/${type}?limit=${PAGE_SIZE}&offset=${offset}`;
    }

    async function load() {
        try {
            const data = await api.get(buildUrl());
            const batch = data.movies || [];
            movies = batch;
            // A short page means there is nothing after it.
            exhausted = FACET_TYPES.has(type) || batch.length < PAGE_SIZE;
            error = "";
        } catch (err) {
            error = err.message || "Could not load these films.";
        } finally {
            loading = false;
        }
    }

    async function loadMore() {
        if (loadingMore || exhausted) return;
        loadingMore = true;
        offset += PAGE_SIZE;
        try {
            const data = await api.get(buildUrl());
            const batch = data.movies || [];
            // De-duplicate: overlapping offsets would otherwise repeat cards and
            // break the keyed each block.
            const seen = new Set(movies.map((m) => m.movie_id));
            movies = [...movies, ...batch.filter((m) => !seen.has(m.movie_id))];
            if (batch.length < PAGE_SIZE) exhausted = true;
        } catch (err) {
            offset -= PAGE_SIZE;
            error = err.message || "Could not load more.";
        } finally {
            loadingMore = false;
        }
    }
</script>

<svelte:head><title>{heading} — AtoZflix</title></svelte:head>

<div class="page">
    <div class="navbar-wrapper"><Navbar /></div>

    <header class="hero">
        <div class="shell">
            <p class="eyebrow">Browse</p>
            <h1>{heading}</h1>
            {#if !loading && movies.length}
                <p class="lede">
                    Showing {movies.length}{exhausted ? "" : "+"} films
                </p>
            {/if}
        </div>
    </header>

    <section class="shell listing">
        {#if error && !movies.length}
            <p class="error">{error}</p>
        {/if}

        <MovieGrid
            {loading}
            empty={!loading && movies.length === 0}
            emptyTitle="Nothing to show"
            emptyBody="We could not find any films for this selection."
            emptyActionHref="/components/Home"
            emptyActionLabel="Back home"
        >
            {#each movies as movie (movie.movie_id)}
                <MovieCard
                    movie_id={movie.movie_id}
                    poster_path={movie.poster_path}
                    title={movie.title}
                    rating={movie.rating_avg}
                />
            {/each}
        </MovieGrid>

        {#if !loading && movies.length && !exhausted}
            <div class="more-wrap">
                <button class="more" on:click={loadMore} disabled={loadingMore}>
                    {loadingMore ? "Loading…" : "Load more"}
                </button>
            </div>
        {/if}
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

    .more-wrap {
        display: flex;
        justify-content: center;
        margin-top: 2.5rem;
    }

    .more {
        padding: 0.75rem 2rem;
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-pill);
        background: none;
        color: var(--text);
        font-family: inherit;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s var(--ease), border-color 0.2s var(--ease);
    }

    .more:hover:not(:disabled) {
        background: var(--accent-wash);
        border-color: var(--accent);
        color: var(--accent);
    }

    .more:disabled { opacity: 0.5; cursor: progress; }
</style>
