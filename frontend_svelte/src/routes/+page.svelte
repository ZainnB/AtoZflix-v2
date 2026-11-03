<!--
  The app has no content of its own at "/" - it is an entry point that sends
  the visitor to the auth page. `goto` is used rather than assigning to
  window.location.href so this is a client-side navigation: no second
  document request, no white flash, and the SvelteKit router keeps its state.
  replaceState keeps "/" out of the history, so Back does not bounce the user
  straight back here.
-->
<script>
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";

  onMount(() => {
    goto("/components/Register", { replaceState: true });
  });
</script>
