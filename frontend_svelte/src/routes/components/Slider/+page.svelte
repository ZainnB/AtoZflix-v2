<!--
  Generic movie shelf driven by an endpoint name: latest, top_rated, etc.

  All layout now comes from CarouselRow, so this file is only data fetching.
-->
<script>
  import { onMount } from "svelte";
  import CarouselRow from "$lib/components/CarouselRow.svelte";
  import MovieCard from "$lib/components/MovieCard.svelte";
  import { api as apiClient } from "../../../lib/api.js";

  export let api;
  export let limit = 30;
  export let heading;

  let movies = [];
  let loading = true;

  onMount(async () => {
    try {
      const data = await apiClient.get(`/api/${api}?limit=${limit}`);
      movies = data.movies || [];
    } catch (error) {
      console.error(`Error fetching ${api} movies:`, error);
    } finally {
      loading = false;
    }
  });

  $: viewAllHref =
    `/components/ViewAll?type=${encodeURIComponent(api)}` +
    `&heading=${encodeURIComponent(heading)}`;
</script>

<CarouselRow {heading} {loading} count={movies.length} {viewAllHref}>
  {#each movies as movie (movie.movie_id)}
    <MovieCard
      movie_id={movie.movie_id}
      poster_path={movie.poster_path}
      title={movie.title}
      rating={movie.rating_avg}
    />
  {/each}
</CarouselRow>
