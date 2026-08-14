<!--
  Root layout. Its only job is to load the design tokens once for every route,
  so components never have to import the stylesheet themselves and the palette
  cannot drift between pages.
-->
<script>
  import "$lib/styles/theme.css";
</script>

<slot />
