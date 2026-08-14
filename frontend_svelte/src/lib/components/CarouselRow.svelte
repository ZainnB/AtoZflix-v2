<!--
  The one horizontal shelf used by every row in the app.

  Replaces five near-identical carousels (Slider, GenralSlider, GenralSlider2,
  Recommendations, SimilarMovies) that each carried their own copy of the same
  layout CSS with slightly different numbers - which is why rows did not line up
  with one another or with the page gutters.

  Layout notes:
  * Content sits inside .shell, so every row shares the page's centered column.
  * Cards are sized from --per-view, so "how many fit" is one token in
    theme.css rather than a hard-coded slice() in each component.
  * It pages by a whole screenful rather than one card at a time. Nudging a row
    by a single card is slow and makes it hard to tell what moved.
  * Arrows hide entirely when everything already fits, instead of sitting there
    disabled over the artwork.
-->
<script>
  export let heading = "";
  export let subtitle = "";
  export let loading = false;
  /** Number of skeleton tiles while loading. */
  export let skeletonCount = 10;
  /** "poster" (2:3) or "portrait" (1:1) - only affects skeleton shape. */
  export let shape = "poster";
  /** Optional "View all" destination. */
  export let viewAllHref = null;
  /** Item count, used to decide whether paging controls are needed. */
  export let count = 0;

  let track;
  let atStart = true;
  let atEnd = false;

  function updateEdges() {
    if (!track) return;
    // 2px of slack absorbs sub-pixel rounding at fractional zoom levels, which
    // otherwise leaves the "next" arrow enabled at the true end of the track.
    atStart = track.scrollLeft <= 2;
    atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
  }

  function page(direction) {
    if (!track) return;
    // Leave one card's worth of overlap so the user keeps a visual anchor
    // between pages rather than jumping to a completely new set.
    const step = track.clientWidth * 0.9;
    track.scrollBy({ left: direction * step, behavior: "smooth" });
  }
</script>

<section class="row" class:has-heading={heading}>
  <div class="shell">
    {#if heading}
      <header class="row-header">
        <div class="titles">
          <h2>{heading}</h2>
          {#if subtitle}<p class="subtitle">{subtitle}</p>{/if}
        </div>
        {#if viewAllHref}
          <a class="view-all" href={viewAllHref}>View all</a>
        {/if}
      </header>
    {/if}

    <div class="viewport">
      {#if !loading && count > 0}
        <button
          class="arrow left"
          class:hidden={atStart}
          on:click={() => page(-1)}
          aria-label="Scroll left"
          tabindex={atStart ? -1 : 0}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" /></svg>
        </button>
      {/if}

      <div class="track" bind:this={track} on:scroll={updateEdges}>
        {#if loading}
          {#each Array(skeletonCount).fill(0) as _, i}
            <div class="cell">
              <div class="skeleton" class:portrait={shape === "portrait"}></div>
            </div>
          {/each}
        {:else}
          <slot />
        {/if}
      </div>

      {#if !loading && count > 0}
        <button
          class="arrow right"
          class:hidden={atEnd}
          on:click={() => page(1)}
          aria-label="Scroll right"
          tabindex={atEnd ? -1 : 0}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" /></svg>
        </button>
      {/if}
    </div>
  </div>
</section>

<style>
  .row {
    margin-block: 2.25rem;
  }

  .row-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 0.85rem;
  }

  .titles {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    min-width: 0;
  }

  h2 {
    margin: 0;
    font-size: clamp(1.05rem, 1.6vw, 1.4rem);
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text);
  }

  .subtitle {
    margin: 0;
    font-size: 0.8rem;
    color: var(--text-faint);
  }

  .view-all {
    flex-shrink: 0;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--accent);
    text-decoration: none;
    padding: 0.3rem 0.6rem;
    border-radius: var(--radius-pill);
    transition: background 0.2s var(--ease), color 0.2s var(--ease);
  }

  .view-all:hover {
    background: var(--accent-wash);
    color: var(--text);
  }

  .viewport {
    position: relative;
  }

  .track {
    display: flex;
    gap: var(--card-gap);
    overflow-x: auto;
    scroll-behavior: smooth;
    /* Snap so a paged scroll always lands on a card edge rather than slicing
       one down the middle. */
    scroll-snap-type: x mandatory;
    /* Native scrolling is kept so trackpads and touch work; the arrows are an
       addition for mouse users, not a replacement. */
    scrollbar-width: none;
    -ms-overflow-style: none;
    padding-block: 0.25rem;
  }

  .track::-webkit-scrollbar {
    display: none;
  }

  /* Each direct child becomes an exactly-sized cell, so N cards fill the row
     with no remainder regardless of how many items there are. */
  .track > :global(*) {
    flex: 0 0
      calc((100% - (var(--per-view) - 1) * var(--card-gap)) / var(--per-view));
    /* Flex items default to min-width:auto, meaning they refuse to shrink below
       their content's intrinsic width. A card whose title is a long unbreakable
       string therefore blew past its flex-basis - measured 110px, 127px, 164px
       and 187px in the same row. min-width:0 lets the basis actually hold, and
       the title's own ellipsis takes over. */
    min-width: 0;
    scroll-snap-align: start;
  }

  .cell {
    display: block;
  }

  .skeleton {
    aspect-ratio: 2 / 3;
  }

  .skeleton.portrait {
    aspect-ratio: 1 / 1;
    border-radius: var(--radius-pill);
  }

  .arrow {
    position: absolute;
    top: 0;
    bottom: 0;
    z-index: 3;
    width: clamp(2rem, 3vw, 3rem);
    display: grid;
    place-items: center;
    border: none;
    cursor: pointer;
    color: var(--text);
    background: linear-gradient(to right, rgba(10, 10, 13, 0.92), rgba(10, 10, 13, 0));
    opacity: 0;
    transition: opacity 0.2s var(--ease);
  }

  .arrow.right {
    right: 0;
    background: linear-gradient(to left, rgba(10, 10, 13, 0.92), rgba(10, 10, 13, 0));
  }

  .arrow.left {
    left: 0;
  }

  /* Arrows stay out of the way until the row is actually being used. */
  .viewport:hover .arrow,
  .arrow:focus-visible {
    opacity: 1;
  }

  .arrow.hidden {
    opacity: 0;
    pointer-events: none;
  }

  .arrow svg {
    width: 1.6rem;
    height: 1.6rem;
    fill: none;
    stroke: currentColor;
    stroke-width: 2.2;
    stroke-linecap: round;
    stroke-linejoin: round;
    filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.8));
  }

  /* Touch devices scroll natively; the arrows are redundant and eat space. */
  @media (hover: none) {
    .arrow { display: none; }
  }
</style>
