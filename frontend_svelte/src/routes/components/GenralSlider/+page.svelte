<!--
  Movie shelf filtered by a facet: genre or country.
  Example: <GenreSlider type="genre" value="Comedy" heading="Laugh out Loud" />
-->
<script>
  import { onMount } from "svelte";
  import CarouselRow from "$lib/components/CarouselRow.svelte";
  import MovieCard from "$lib/components/MovieCard.svelte";
  import { api } from "../../../lib/api.js";

  export let type;
  export let value;
  export let limit = 30;
  export let heading;

  let movies = [];
  let loading = true;

  onMount(async () => {
    try {
      const data = await api.get(
        `/api/${type}?${type}=${encodeURIComponent(value)}&limit=${limit}`
      );
      movies = data.movies || [];
    } catch (error) {
      console.error(`Error fetching ${type} movies:`, error);
    } finally {
      loading = false;
    }
  });

  // The previous version built this link from the imported `api` module object
  // rather than the facet, producing "?type=[object Object]".
  $: viewAllHref =
    `/components/ViewAll?type=${encodeURIComponent(type)}` +
    `&value=${encodeURIComponent(value)}` +
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
