<!--
  Billed cast for a film, in billing order, linking through to each actor.

  Public endpoint - the cast of a film is catalog data, not user data.
-->
<script>
  import { onMount } from "svelte";
  import CarouselRow from "$lib/components/CarouselRow.svelte";
  import PersonCard from "$lib/components/PersonCard.svelte";
  import { api } from "../../../lib/api.js";

  export let movie_id;
  export let limit = 20;
  export let heading = "Cast";

  let cast = [];
  let loading = true;
  let failed = false;

  onMount(async () => {
    if (!movie_id) {
      loading = false;
      failed = true;
      return;
    }
    try {
      const data = await api.get(
        `/api/movie_cast?movie_id=${movie_id}&limit=${limit}`
      );
      cast = data.cast || [];
    } catch (error) {
      console.error("Error fetching cast:", error);
      failed = true;
    } finally {
      loading = false;
    }
  });
</script>

{#if !failed && (loading || cast.length)}
  <CarouselRow
    {heading}
    {loading}
    count={cast.length}
    shape="portrait"
    subtitle={cast.length ? `${cast.length} billed` : ""}
  >
    {#each cast as person (person.actor_id)}
      <PersonCard
        actor_id={person.actor_id}
        name={person.actor_name}
        profile_path={person.profile_path}
        role={person.character_name}
      />
    {/each}
  </CarouselRow>
{/if}
