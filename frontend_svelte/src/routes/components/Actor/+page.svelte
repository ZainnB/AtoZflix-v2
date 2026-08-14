<!--
  Actor detail page.

  Layout is a two-column masthead (portrait + identity/stats/bio) over a
  filmography grid and a co-stars row. On narrow screens it collapses to a
  single column with the portrait centred.

  The career stats are computed server-side from our own catalog rather than
  copied from TMDb - films in catalog, average rating, active years, dominant
  genres. That is information TMDb's own page does not show, so it earns its
  place instead of being a bio reprint.
-->
<script>
  import { onMount } from "svelte";
  import Navbar from "../Home/Navbar2.svelte";
  import Footer from "../Register/Footer1.svelte";
  import Line from "../Register/Line.svelte";
  import CarouselRow from "$lib/components/CarouselRow.svelte";
  import PersonCard from "$lib/components/PersonCard.svelte";
  import MovieCard from "$lib/components/MovieCard.svelte";
  import { api } from "../../../lib/api.js";
  import { redirectToRegisterIfNotAuthenticated } from "/src/utils/auth.js";

  const IMG = "https://image.tmdb.org/t/p/h632";

  let actor = null;
  let stats = null;
  let filmography = [];
  let coStars = [];
  let loading = true;
  let coStarsLoading = true;
  let error = null;
  let bioExpanded = false;

  onMount(async () => {
    redirectToRegisterIfNotAuthenticated();
    const actorId = new URLSearchParams(window.location.search).get("actor_id");

    if (!actorId) {
      error = "No actor selected.";
      loading = false;
      return;
    }

    try {
      const data = await api.get(`/api/actor_details?actor_id=${actorId}`);
      actor = data.actor;
      stats = data.stats;
      filmography = data.filmography || [];
    } catch (err) {
      error = err.message || "Could not load this actor.";
    } finally {
      loading = false;
    }

    // Co-stars load separately so the main profile paints without waiting on
    // the slower aggregate query.
    try {
      const related = await api.get(`/api/related_actors?actor_id=${actorId}&limit=20`);
      coStars = related.actors || [];
    } catch (err) {
      console.error("Error fetching co-stars:", err);
    } finally {
      coStarsLoading = false;
    }
  });

  function formatDate(value) {
    if (!value) return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime())
      ? value
      : d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  }

  function ageFrom(birthday, deathday) {
    if (!birthday) return null;
    const born = new Date(birthday);
    if (Number.isNaN(born.getTime())) return null;
    const end = deathday ? new Date(deathday) : new Date();
    let age = end.getFullYear() - born.getFullYear();
    const m = end.getMonth() - born.getMonth();
    if (m < 0 || (m === 0 && end.getDate() < born.getDate())) age--;
    return age;
  }

  $: portrait = actor?.profile_path ? `${IMG}${actor.profile_path}` : null;
  $: age = actor ? ageFrom(actor.birthday, actor.deathday) : null;
  // Biographies run to several hundred words; clamp and let the reader expand.
  $: bioIsLong = (actor?.biography?.length ?? 0) > 480;
  $: initials = (actor?.actor_name || "?")
    .split(" ").filter(Boolean).slice(0, 2).map((p) => p[0]).join("").toUpperCase();
</script>

<svelte:head>
  <title>{actor ? `${actor.actor_name} — AtoZflix` : "Actor — AtoZflix"}</title>
</svelte:head>

<div class="page">
  <div class="navbar-wrapper"><Navbar /></div>

  {#if loading}
    <div class="shell masthead">
      <div class="skeleton portrait-skeleton"></div>
      <div class="identity">
        <div class="skeleton line lg"></div>
        <div class="skeleton line md"></div>
        <div class="skeleton line sm"></div>
        <div class="skeleton block"></div>
      </div>
    </div>
  {:else if error}
    <div class="shell state">
      <h1>Something went wrong</h1>
      <p>{error}</p>
      <a class="btn" href="/components/Actors">Browse actors</a>
    </div>
  {:else if actor}
    <header class="masthead-wrap">
      <div class="shell masthead">
        <div class="portrait">
          {#if portrait}
            <img src={portrait} alt={actor.actor_name} />
          {:else}
            <div class="initials" aria-hidden="true">{initials}</div>
          {/if}
        </div>

        <div class="identity">
          <p class="eyebrow">Actor</p>
          <h1>{actor.actor_name}</h1>

          <ul class="facts">
            {#if actor.birthday}
              <li>
                <span class="k">Born</span>
                <span class="v">
                  {formatDate(actor.birthday)}
                  {#if age !== null}<em>({actor.deathday ? `aged ${age}` : `age ${age}`})</em>{/if}
                </span>
              </li>
            {/if}
            {#if actor.deathday}
              <li><span class="k">Died</span><span class="v">{formatDate(actor.deathday)}</span></li>
            {/if}
            {#if actor.place_of_birth}
              <li><span class="k">From</span><span class="v">{actor.place_of_birth}</span></li>
            {/if}
          </ul>

          {#if stats?.top_genres?.length}
            <div class="chips">
              {#each stats.top_genres as genre}
                <a class="chip" href={`/components/Genre?genre=${encodeURIComponent(genre)}`}>{genre}</a>
              {/each}
            </div>
          {/if}

          {#if stats}
            <dl class="stats">
              <div class="stat">
                <dt>In catalog</dt>
                <dd>{stats.movie_count}</dd>
              </div>
              {#if stats.avg_rating}
                <div class="stat">
                  <dt>Avg rating</dt>
                  <dd class="accent">{stats.avg_rating}</dd>
                </div>
              {/if}
              {#if stats.first_year}
                <div class="stat">
                  <dt>Active</dt>
                  <dd>{stats.first_year}<span class="dash">–</span>{stats.last_year}</dd>
                </div>
              {/if}
            </dl>
          {/if}

          {#if actor.biography}
            <div class="bio" class:clamped={bioIsLong && !bioExpanded}>
              <p>{actor.biography}</p>
            </div>
            {#if bioIsLong}
              <button class="more" on:click={() => (bioExpanded = !bioExpanded)}>
                {bioExpanded ? "Show less" : "Read more"}
              </button>
            {/if}
          {/if}
        </div>
      </div>
    </header>

    {#if coStarsLoading || coStars.length}
      <CarouselRow
        heading="Frequently appears with"
        subtitle="Ranked by shared films in this catalog"
        loading={coStarsLoading}
        count={coStars.length}
        shape="portrait"
        skeletonCount={10}
      >
        {#each coStars as person (person.actor_id)}
          <PersonCard
            actor_id={person.actor_id}
            name={person.actor_name}
            profile_path={person.profile_path}
            role={`${person.shared_movies} shared`}
          />
        {/each}
      </CarouselRow>
    {/if}

    <section class="shell filmography">
      <div class="section-head">
        <h2>Filmography</h2>
        <span class="count">{filmography.length} films</span>
      </div>

      {#if filmography.length}
        <div class="grid">
          {#each filmography as film (film.movie_id)}
            <MovieCard
              movie_id={film.movie_id}
              poster_path={film.poster_path}
              title={film.title}
              subtitle={film.character_name || ""}
              rating={film.rating_avg}
            />
          {/each}
        </div>
      {:else}
        <p class="empty">No films for this actor in the catalog.</p>
      {/if}
    </section>
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

  /* A soft teal wash behind the masthead separates it from the rows below
     without needing a hard rule. */
  .masthead-wrap {
    padding-top: calc(var(--nav-height) + 2.5rem);
    padding-bottom: 2rem;
    background:
      radial-gradient(120% 100% at 15% 0%, rgba(45, 212, 191, 0.10), transparent 60%),
      linear-gradient(to bottom, var(--surface), var(--bg));
    border-bottom: 1px solid var(--border);
  }

  .masthead {
    display: grid;
    grid-template-columns: minmax(180px, 260px) minmax(0, 1fr);
    gap: clamp(1.5rem, 4vw, 3rem);
    align-items: start;
  }

  .portrait {
    aspect-ratio: 2 / 3;
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: var(--surface-2);
    box-shadow: var(--shadow-lg);
  }

  .portrait img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .initials {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
    font-size: 4rem;
    font-weight: 700;
    color: var(--text-faint);
    background: linear-gradient(160deg, var(--surface-3), var(--surface));
  }

  .identity {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    min-width: 0;
  }

  .eyebrow {
    margin: 0;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--accent);
  }

  h1 {
    margin: 0;
    font-size: clamp(1.9rem, 4.5vw, 3rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.05;
    text-wrap: balance;
  }

  .facts {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.9rem;
  }

  .facts li {
    display: flex;
    gap: 0.6rem;
  }

  .facts .k {
    flex: 0 0 3.5rem;
    color: var(--text-faint);
  }

  .facts .v {
    color: var(--text-dim);
  }

  .facts em {
    font-style: normal;
    color: var(--text-faint);
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

  .chip:hover {
    background: var(--accent-strong);
    color: #06201d;
  }

  .stats {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.3rem 0 0;
  }

  .stat {
    flex: 1 1 auto;
    min-width: 7rem;
    padding: 0.65rem 0.9rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
  }

  .stat dt {
    font-size: 0.72rem;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--text-faint);
    margin-bottom: 0.2rem;
  }

  .stat dd {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .stat dd.accent {
    color: var(--accent);
  }

  .dash {
    margin: 0 0.1rem;
    color: var(--text-faint);
  }

  .bio {
    color: var(--text-dim);
    font-size: 0.92rem;
    line-height: 1.65;
    max-width: 68ch;
  }

  .bio p {
    margin: 0;
  }

  .bio.clamped p {
    display: -webkit-box;
    -webkit-line-clamp: 5;
    line-clamp: 5;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .more {
    align-self: flex-start;
    background: none;
    border: none;
    padding: 0;
    color: var(--accent);
    font-size: 0.85rem;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
  }

  .more:hover {
    text-decoration: underline;
  }

  .filmography {
    padding-block: 2rem 3rem;
  }

  .section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .section-head h2 {
    margin: 0;
    font-size: clamp(1.05rem, 1.6vw, 1.4rem);
    font-weight: 700;
  }

  .count {
    font-size: 0.8rem;
    color: var(--text-faint);
  }

  /* auto-fill rather than a fixed column count, so the grid reflows to the same
     card width as the carousels above it. */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1.1rem var(--card-gap);
  }

  .empty {
    color: var(--text-faint);
  }

  .state {
    padding-top: calc(var(--nav-height) + 4rem);
    padding-bottom: 4rem;
    text-align: center;
  }

  .btn {
    display: inline-block;
    margin-top: 1rem;
    padding: 0.6rem 1.2rem;
    border-radius: var(--radius-pill);
    background: var(--accent-strong);
    color: #06201d;
    font-weight: 600;
    text-decoration: none;
  }

  /* loading skeletons */
  .portrait-skeleton { aspect-ratio: 2 / 3; border-radius: var(--radius-lg); }
  .line { height: 1rem; border-radius: var(--radius-sm); }
  .line.lg { height: 2.6rem; width: min(60%, 22rem); }
  .line.md { width: min(40%, 16rem); }
  .line.sm { width: min(30%, 12rem); }
  .block { height: 7rem; border-radius: var(--radius); }
  .identity .skeleton { margin-bottom: 0.75rem; }

  @media (max-width: 780px) {
    .masthead {
      grid-template-columns: 1fr;
      justify-items: center;
      text-align: center;
    }

    .portrait {
      width: min(220px, 60vw);
    }

    .identity {
      align-items: center;
    }

    .facts li {
      justify-content: center;
    }

    .facts .k {
      flex: 0 0 auto;
    }

    .bio {
      text-align: left;
    }

    .more {
      align-self: center;
    }
  }
</style>
