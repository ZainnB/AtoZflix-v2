<!--
  Kept as a thin re-export so the several pages already importing
  "../Slider/movie_card.svelte" keep working unchanged. The implementation lives
  in $lib/components/MovieCard.svelte - having one card definition is the point.
-->
<script>
  import MovieCard from "$lib/components/MovieCard.svelte";

  export let poster_path = null;
  export let movie_id;
  export let title = "";
  export let subtitle = "";
  export let rating = null;
</script>

<MovieCard {poster_path} {movie_id} {title} {subtitle} {rating} />
