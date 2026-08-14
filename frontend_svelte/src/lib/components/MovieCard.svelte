<!--
  A single poster tile.

  Width is NOT set here. The card fills whatever track cell it is placed in, so
  the parent carousel controls how many fit per row. The old card hard-coded
  165x260px, which is why rows never lined up with the page gutters and why
  changing "how many per row" meant editing every carousel.
-->
<script>
  export let movie_id;
  export let poster_path = null;
  export let title = "";
  export let subtitle = "";
  export let rating = null;

  const IMG = "https://image.tmdb.org/t/p/w342";

  $: src = poster_path ? `${IMG}${poster_path}` : null;
  // The link carries the title so screen readers announce the destination
  // rather than reading out a bare URL.
  $: label = title ? `${title}${subtitle ? `, ${subtitle}` : ""}` : "View movie details";
</script>

<a class="card" href={`/components/MovieDetail?movie_id=${movie_id}`} aria-label={label}>
  <div class="poster">
    {#if src}
      <img {src} alt={title || "Movie poster"} loading="lazy" decoding="async" />
    {:else}
      <!-- Poster art is missing for a small share of the catalog; a titled
           placeholder is better than a broken image icon. -->
      <div class="fallback"><span>{title || "No artwork"}</span></div>
    {/if}

    {#if rating}
      <span class="rating">{Number(rating).toFixed(1)}</span>
    {/if}

    <div class="scrim"></div>
  </div>

  {#if title}
    <div class="meta">
      <span class="title">{title}</span>
      {#if subtitle}<span class="subtitle">{subtitle}</span>{/if}
    </div>
  {/if}
</a>

<style>
  .card {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
    text-decoration: none;
    color: inherit;
    /* Same reason as the track rule: without this the nowrap title below sets a
       min-content width that the card cannot shrink under. */
    min-width: 0;
    transition: transform 0.25s var(--ease);
  }

  .card:hover,
  .card:focus-visible {
    transform: translateY(-4px);
  }

  .poster {
    position: relative;
    /* Fixed poster ratio means a missing or oddly sized image can never change
       the row height and shunt the layout around. */
    aspect-ratio: 2 / 3;
    border-radius: var(--radius);
    overflow: hidden;
    background: var(--surface-2);
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.25s var(--ease);
  }

  .card:hover .poster,
  .card:focus-visible .poster {
    box-shadow: var(--shadow-lg);
  }

  .poster img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .fallback {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
    padding: 0.75rem;
    text-align: center;
    background: linear-gradient(160deg, var(--surface-2), var(--surface));
    color: var(--text-faint);
    font-size: 0.75rem;
    line-height: 1.35;
  }

  .rating {
    position: absolute;
    top: 0.4rem;
    right: 0.4rem;
    z-index: 2;
    padding: 0.15rem 0.4rem;
    border-radius: var(--radius-sm);
    background: rgba(10, 10, 13, 0.82);
    color: var(--star);
    font-size: 0.72rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    backdrop-filter: blur(4px);
  }

  /* A faint bottom scrim keeps the rating chip and any overlaid text legible
     against bright poster art. */
  .scrim {
    position: absolute;
    inset: auto 0 0 0;
    height: 45%;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.55), transparent);
    opacity: 0;
    transition: opacity 0.25s var(--ease);
  }

  .card:hover .scrim,
  .card:focus-visible .scrim {
    opacity: 1;
  }

  .meta {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    min-width: 0;
  }

  .title {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text);
    /* Titles vary wildly in length; clamping to one line keeps every card in a
       row exactly the same height. */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .subtitle {
    font-size: 0.72rem;
    color: var(--text-faint);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
