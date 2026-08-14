<!--
  Responsive grid for the "browse a full list" pages (Favourites, Watch Later,
  View All, filmographies).

  auto-fill with a minmax track rather than a fixed column count, so cards keep
  the same width as the carousel rows and the page reflows without breakpoints.
-->
<script>
  /** Minimum card width before the grid drops a column. */
  export let min = "150px";
  export let loading = false;
  export let skeletonCount = 20;
  export let empty = false;
  export let emptyTitle = "Nothing here yet";
  export let emptyBody = "";
  export let emptyActionHref = null;
  export let emptyActionLabel = "Browse movies";
</script>

{#if loading}
  <div class="grid" style={`--min:${min}`}>
    {#each Array(skeletonCount).fill(0) as _}
      <div class="skeleton tile"></div>
    {/each}
  </div>
{:else if empty}
  <div class="empty">
    <h3>{emptyTitle}</h3>
    {#if emptyBody}<p>{emptyBody}</p>{/if}
    {#if emptyActionHref}
      <a class="cta" href={emptyActionHref}>{emptyActionLabel}</a>
    {/if}
  </div>
{:else}
  <div class="grid" style={`--min:${min}`}>
    <slot />
  </div>
{/if}

<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(var(--min, 150px), 1fr));
    gap: 1.25rem var(--card-gap);
  }

  .tile {
    aspect-ratio: 2 / 3;
  }

  /* An empty state should say what to do next, not just that the list is
     empty - otherwise a new account looks broken. */
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;
    padding: clamp(2.5rem, 8vw, 5rem) 1rem;
    text-align: center;
    border: 1px dashed var(--border-strong);
    border-radius: var(--radius-lg);
    background: var(--surface);
  }

  .empty h3 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
  }

  .empty p {
    margin: 0;
    max-width: 46ch;
    color: var(--text-dim);
    font-size: 0.92rem;
    line-height: 1.6;
  }

  .cta {
    margin-top: 0.5rem;
    padding: 0.6rem 1.3rem;
    border-radius: var(--radius-pill);
    background: var(--accent-strong);
    color: #06201d;
    font-weight: 600;
    font-size: 0.88rem;
    text-decoration: none;
    transition: background 0.2s var(--ease);
  }

  .cta:hover {
    background: var(--accent);
  }
</style>
