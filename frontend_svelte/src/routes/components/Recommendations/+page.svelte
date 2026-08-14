<!--
  Personalised "Recommended for You" shelf.

  Backed by GET /api/recommendations, which returns the hybrid content-based +
  collaborative ranking for whoever owns the JWT. The user is never passed in the
  URL - the backend reads it from the token - so this component cannot be pointed
  at somebody else's feed.

  The shelf hides itself entirely if the API errors, rather than leaving a broken
  empty row on the home page.
-->
<script>
  import { onMount } from "svelte";
  import CarouselRow from "$lib/components/CarouselRow.svelte";
  import MovieCard from "$lib/components/MovieCard.svelte";
  import { api as apiClient } from "../../../lib/api.js";

  export let limit = 24;
  export let heading = "Recommended for You";
  export let explain = false;

  let movies = [];
  let strategy = null;
  let interactionCount = 0;
  let loading = true;
  let failed = false;

  onMount(async () => {
    try {
      const data = await apiClient.get(
        `/api/recommendations?limit=${limit}&explain=${explain}`
      );
      movies = data.movies || [];
      strategy = data.strategy;
      interactionCount = data.interaction_count ?? 0;
    } catch (error) {
      console.error("Error fetching recommendations:", error);
      failed = true;
    } finally {
      loading = false;
    }
  });

  // Cold-start users get popularity-ranked results; saying so is more honest
  // than implying the picks are personalised when there is no history yet.
  $: subtitle =
    strategy === "popularity"
      ? "Popular right now — rate or favourite a few films to personalise this"
      : interactionCount
        ? `Based on ${interactionCount} ${interactionCount === 1 ? "title" : "titles"} in your history`
        : "";
</script>

{#if !failed && (loading || movies.length)}
  <CarouselRow {heading} {subtitle} {loading} count={movies.length}>
    {#each movies as movie (movie.movie_id)}
      <MovieCard
        movie_id={movie.movie_id}
        poster_path={movie.poster_path}
        title={movie.title}
        rating={movie.rating_avg}
      />
    {/each}
  </CarouselRow>
{/if}
