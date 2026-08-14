<!--
  Movie shelf keyed by a person: actor-movies, crew-movies.
  Used by the Actors and Crew browse pages and by search results.
-->
<script>
  import { onMount } from "svelte";
  import CarouselRow from "$lib/components/CarouselRow.svelte";
  import MovieCard from "$lib/components/MovieCard.svelte";
  import { api } from "../../../lib/api.js";

  export let api_name;
  export let type;
  export let value;
  export let limit = 30;
  export let heading = "";

  let movies = [];
  let loading = true;

  onMount(async () => {
    try {
      const data = await api.get(
        `/api/${api_name}?${type}_id=${encodeURIComponent(value)}&limit=${limit}`
      );
      // These endpoints wrap their payload in `data`, unlike the movie
      // endpoints which use `movies`.
      movies = data.data || data.movies || [];
    } catch (error) {
      console.error("Error fetching movies:", error);
    } finally {
      loading = false;
    }
  });

  $: viewAllHref =
    `/components/searchActorOrCrew?type=${encodeURIComponent(type)}` +
    `&id=${encodeURIComponent(value)}`;
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
