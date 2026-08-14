<!--
  Home.

  Row order is by signal strength for a returning user: the trending hero, the
  ranked top-15, then the personalised shelf, then the generic catalog rows.

  Spacing now comes from CarouselRow's own margins rather than a wrapper div per
  row, so the rhythm down the page is uniform and set in one place.
-->
<script>
    import { onMount } from "svelte";
    import { redirectToRegisterIfNotAuthenticated } from "/src/utils/auth.js";
    import Navbar from "./Navbar2.svelte";
    import TrendingMovies from "./Top5big.svelte";
    import Top15Medium from "./Top15medium.svelte";
    import Slider from "../Slider/+page.svelte";
    import Recommendations from "../Recommendations/+page.svelte";
    import GenreSlider from "../GenralSlider/+page.svelte";
    import Footer from "../Register/Footer1.svelte";
    import Line from "../Register/Line.svelte";

    // Each row is one request, so this list is also the page's request budget.
    // Kept to four genres: past that the page is mostly rows nobody scrolls to.
    const genreRows = [
        { value: "Comedy", heading: "Laugh Out Loud" },
        { value: "Science Fiction", heading: "Worlds Elsewhere" },
        { value: "Thriller", heading: "Edge of Your Seat" },
        { value: "Animation", heading: "Animated Favourites" },
    ];

    onMount(() => {
        redirectToRegisterIfNotAuthenticated();
    });
</script>

<svelte:head><title>AtoZflix</title></svelte:head>

<div class="page">
    <div class="navbar-wrapper"><Navbar /></div>

    <TrendingMovies />
    <Top15Medium />

    <!-- Personalised shelf sits above the generic ones: it is the highest
         signal row on the page for a returning user. -->
    <Recommendations limit={30} />

    <Slider heading="Latest Movies" api="latest" limit={30} />
    <Slider heading="Top Rated" api="top_rated" limit={30} />

    {#each genreRows as row (row.value)}
        <GenreSlider type="genre" value={row.value} heading={row.heading} limit={30} />
    {/each}

    <Line />
    <Footer />
</div>

<style>
    .page {
        position: relative;
        min-height: 100vh;
        background: var(--bg);
        color: var(--text);
        font-family: var(--font);
    }

    .navbar-wrapper {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 10;
    }
</style>
