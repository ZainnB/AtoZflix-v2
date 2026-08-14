<!--
  Browse actors.

  Rewritten from a page that rendered a full movie carousel per actor - twelve
  simultaneous carousels, one network request each, and no way to see who the
  actor actually was because there were no photos. It is now a portrait grid
  that links into the actor detail page, which is where the depth belongs.
-->
<script>
  import { onMount } from "svelte";
  import Navbar from "../Home/Navbar2.svelte";
  import Footer from "../Register/Footer1.svelte";
  import Line from "../Register/Line.svelte";
  import PersonCard from "$lib/components/PersonCard.svelte";
  import { api } from "../../../lib/api.js";
  import { redirectToRegisterIfNotAuthenticated } from "/src/utils/auth.js";

  const LIMIT = 60;

  let actors = [];
  let loading = true;
  let searchQuery = "";

  onMount(async () => {
    redirectToRegisterIfNotAuthenticated();
    try {
      const data = await api.get(`/api/top-actors?limit=${LIMIT}`);
      if (data.status === "success") {
        actors = data.data || [];
      }
    } catch (error) {
      console.error("Error fetching top actors:", error);
    } finally {
      loading = false;
    }
  });

  function search() {
    const q = searchQuery.trim();
    if (!q) return;
    window.location.href =
      `/components/searchActorOrCrew?type=actor&query=${encodeURIComponent(q)}`;
  }

  function onKeydown(event) {
    if (event.key === "Enter") search();
  }
</script>

<svelte:head><title>Actors — AtoZflix</title></svelte:head>

<div class="page">
  <div class="navbar-wrapper"><Navbar /></div>

  <header class="hero">
    <div class="shell">
      <p class="eyebrow">Browse</p>
      <h1>Actors</h1>
      <p class="lede">
        The most-featured performers in the catalog, ranked by the combined
        rating of everything they appear in.
      </p>

      <div class="search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" />
        </svg>
        <input
          type="search"
          bind:value={searchQuery}
          on:keydown={onKeydown}
          placeholder="Search for an actor…"
          aria-label="Search for an actor"
        />
        <button on:click={search} disabled={!searchQuery.trim()}>Search</button>
      </div>
    </div>
  </header>

  <section class="shell listing">
    {#if loading}
      <div class="grid">
        {#each Array(18).fill(0) as _}
          <div class="tile">
            <div class="skeleton circle"></div>
            <div class="skeleton bar"></div>
          </div>
        {/each}
      </div>
    {:else if actors.length}
      <div class="grid">
        {#each actors as actor (actor.actor_id)}
          <PersonCard
            actor_id={actor.actor_id}
            name={actor.actor_name}
            profile_path={actor.profile_path}
          />
        {/each}
      </div>
    {:else}
      <p class="empty">No actors found.</p>
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
    padding-bottom: 2rem;
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
    margin: 0 0 0.5rem;
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 800;
    letter-spacing: -0.02em;
  }

  .lede {
    margin: 0 0 1.5rem;
    max-width: 56ch;
    color: var(--text-dim);
    font-size: 0.98rem;
    line-height: 1.6;
  }

  .search {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    max-width: 34rem;
    padding: 0.35rem 0.35rem 0.35rem 0.9rem;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-pill);
    background: rgba(0, 0, 0, 0.35);
    transition: border-color 0.2s var(--ease);
  }

  /* Focus lives on the wrapper so the whole control lights up, rather than an
     outline appearing inside the pill. */
  .search:focus-within {
    border-color: var(--accent);
  }

  .search svg {
    flex-shrink: 0;
    width: 1.05rem;
    height: 1.05rem;
    fill: none;
    stroke: var(--text-faint);
    stroke-width: 2;
    stroke-linecap: round;
  }

  .search input {
    flex: 1;
    min-width: 0;
    border: none;
    background: none;
    color: var(--text);
    font-family: inherit;
    font-size: 0.95rem;
    padding: 0.5rem 0;
  }

  .search input:focus { outline: none; }
  .search input::placeholder { color: var(--text-faint); }

  .search button {
    flex-shrink: 0;
    padding: 0.55rem 1.1rem;
    border: none;
    border-radius: var(--radius-pill);
    background: var(--accent-strong);
    color: #06201d;
    font-family: inherit;
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s var(--ease), opacity 0.2s var(--ease);
  }

  .search button:hover:not(:disabled) { background: var(--accent); }
  .search button:disabled { opacity: 0.4; cursor: not-allowed; }

  .listing {
    padding-block: 2.5rem 3.5rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 1.6rem 1rem;
  }

  .tile {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: center;
  }

  .circle {
    width: 100%;
    aspect-ratio: 1 / 1;
    border-radius: var(--radius-pill);
  }

  .bar {
    width: 70%;
    height: 0.7rem;
    border-radius: var(--radius-sm);
  }

  .empty {
    color: var(--text-faint);
  }
</style>
