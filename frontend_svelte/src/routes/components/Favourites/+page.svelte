<script>
    import { onMount } from "svelte";
    import { redirectToRegisterIfNotAuthenticated, getCurrentUser } from "/src/utils/auth.js";
    import Navbar from "../Home/Navbar2.svelte";
    import Footer from "../Register/Footer1.svelte";
    import Line from "../Register/Line.svelte";
    import MovieCard from "../Slider/movie_card.svelte";
    import { api } from '../../../lib/api.js';

    let user_id = null;
    let favourites = [];
    let isLoading = true;
    let error = "";

    // Check if the user is authenticated and redirect if not
    onMount(async () => {
        redirectToRegisterIfNotAuthenticated();
        const user = getCurrentUser();
        user_id = user?.userId;

        // Fetch movie details
        try {
            const data = await api.get(`/api/get_favourites?user_id=${user_id}`);
            favourites = data.favourites || [];
        } catch (err) {
            error = err.message || "Failed to fetch favourites";
        } finally {
            isLoading = false;
        }
    });

    async function fetchFavourites() {
        try {
            const data = await api.get(`/api/get_favourites?user_id=${user_id}`);
            favourites = data.favourites || [];
        } catch (err) {
            error = err.message || "Failed to fetch favourites";
        } finally {
            isLoading = false;
        }
    }

    // Remove a favourite movie
    async function removeFavourite(movieId) {
        try {
            await api.post("/api/remove_favourite", { movie_id: movieId });
            await fetchFavourites();
        } catch (e) {
            alert(e.message || "An error occurred while removing the movie.");
        }
    }
</script>

<div class="wrapper">
    <div class="navbar-wrapper">
        <Navbar />
    </div>

    <div class="favourites-wrapper">
        {#if isLoading}
            <p>Loading your favourites...</p>
        {:else if error}
            <p>{error}</p>
        {:else if favourites.length === 0}
            <p>You have no favourites yet.</p>
        {:else}
            {#each favourites as movie}
                <div class="movie-card">
                    <MovieCard
                        poster_path={movie.poster_path}
                        movie_id={movie.movie_id}
                    />
                    <p class="added-at">
                        Added on: {new Date(
                            movie.added_at,
                        ).toLocaleDateString()}
                    </p>
                    <button
                        class="remove-button"
                        on:click={() => removeFavourite(movie.movie_id)}
                    >
                        Remove from Favourites
                    </button>
                </div>
            {/each}
        {/if}
    </div>
    <Line />
    <Footer />
</div>

<style>
    .wrapper {
        position: relative;
        min-height: 100vh;
        background-color: #121212;
        font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
            "Ubuntu", sans-serif;
        overflow: hidden;
    }

    .navbar-wrapper {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 10;
    }

    .favourites-wrapper {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        padding: 1rem;
        margin-top: 80px;
    }

    .favourites-wrapper p {
        margin-top: 1rem;
        color: #ffffff;
        text-align: center;
    }

    .movie-card {
        margin-bottom: 1rem;
        width: 100%;
        max-width: 300px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .added-at {
        font-size: 0.8rem;
        color: #888;
    }

    .remove-button {
        margin-top: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: #ff4d4f;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }

    .remove-button:hover {
        background-color: #ff1a1d;
    }
</style>
