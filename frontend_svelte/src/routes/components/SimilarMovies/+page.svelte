<!--
  "More Like This" shelf for a single film.

  Backed by GET /api/similar_movies, which is deliberately a PUBLIC endpoint: it
  is item-to-item, so it needs no user history and still works for a brand new
  account or a logged-out visitor. That is the cold-start half of the recommender
  and the only thing that can rank a film released after the interaction data
  ends.
-->
<script>
  import { onMount } from "svelte";
  import CarouselRow from "$lib/components/CarouselRow.svelte";
  import MovieCard from "$lib/components/MovieCard.svelte";
  import { api as apiClient } from "../../../lib/api.js";

  export let movie_id;
  export let limit = 20;
  export let heading = "More Like This";
  export let subtitle = "";
  export let strategy = "hybrid"; // content | collaborative | hybrid

  let movies = [];
  let loading = true;
  let failed = false;

  onMount(async () => {
    if (!movie_id) {
      loading = false;
      failed = true;
      return;
    }
    try {
      const data = await apiClient.get(
        `/api/similar_movies?movie_id=${movie_id}&limit=${limit}&strategy=${strategy}`
      );
      movies = data.movies || [];
    } catch (error) {
      console.error("Error fetching similar movies:", error);
      failed = true;
    } finally {
      loading = false;
    }
  });
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
