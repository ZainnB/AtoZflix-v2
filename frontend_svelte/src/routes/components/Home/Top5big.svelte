<script>
    import { onMount } from "svelte";

    let movies = [];
    let currentIndex = 0;
    let interval;
    let user_id = null;

    onMount(async () => {
        try {
            const response = await fetch(
                "http://127.0.0.1:5000/api/trending?limit=5",
            );
            if (!response.ok) {
                console.error(
                    "Failed to fetch trending movies:",
                    response.status,
                );
                return;
            }

            user_id = JSON.parse(localStorage.getItem("user")).userId;
            const data = await response.json();
            movies = data.movies;

            // Check fav/watchlist status for each movie
            for (const movie of movies) {
                const movie_id = movie.movie_id;

                const favRes = await fetch(
                    `http://127.0.0.1:5000/api/check_favourite?user_id=${user_id}&movie_id=${movie_id}`,
                );
                if (favRes.ok) {
                    const favData = await favRes.json();
                    movie.isFavourite = favData.is_favourite;
                }

                const wlRes = await fetch(
                    `http://127.0.0.1:5000/api/check_watchlist?user_id=${user_id}&movie_id=${movie_id}`,
                );
                if (wlRes.ok) {
                    const wlData = await wlRes.json();
                    movie.isInWatchlist = wlData.is_in_watchlist;
                }
            }

            console.log("Movies enriched with fav/watchlist status:", movies);
        } catch (error) {
            console.error("Error fetching trending movies:", error);
        }

        startAutoSlide();
    });

    const startAutoSlide = () => {
        interval = setInterval(() => {
            currentIndex = (currentIndex + 1) % movies.length;
        }, 7000);
    };

    const stopAutoSlide = () => clearInterval(interval);

    const handleNext = () =>
        (currentIndex = (currentIndex + 1) % movies.length);

    const handlePrev = () =>
        (currentIndex = (currentIndex - 1 + movies.length) % movies.length);

    const toggleFavourite = async () => {
        const movie = movies[currentIndex];
        const movie_id = movie.movie_id;

        const url = movie.isFavourite
            ? `http://127.0.0.1:5000/api/remove_favourite`
            : `http://127.0.0.1:5000/api/add_favourite`;

        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id, movie_id }),
        });

        if (response.ok) {
            movie.isFavourite = !movie.isFavourite;
            movies = [...movies];
        } else {
            console.error("Failed to update favourite status");
        }
    };

    const toggleWatchlist = async () => {
        const movie = movies[currentIndex];
        const movie_id = movie.movie_id;

        const url = movie.isInWatchlist
            ? `http://127.0.0.1:5000/api/remove_from_watchlist`
            : `http://127.0.0.1:5000/api/add_to_watchlist`;

        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id, movie_id }),
        });

        if (response.ok) {
            movie.isInWatchlist = !movie.isInWatchlist;
            movies = [...movies];
        } else {
            console.error("Failed to update watchlist status");
        }
    };
</script>

<div class="slider">
    {#if movies.length > 0}
        <div
            class="slider-bg"
            style="background-image: url(https://image.tmdb.org/t/p/original{movies[
                currentIndex
            ].backdrop_path})"
        >
            <!-- Gradient Overlay -->
            <div class="slider-overlay"></div>

            <div class="movie-details">
                <h1>{movies[currentIndex].title}</h1>
                <div class="movie-meta">
                    <span
                        >{movies[currentIndex].release_date.split("-")[0]}</span
                    >
                    <span>{movies[currentIndex].rating} ⭐</span>
                    <span>{movies[currentIndex].duration} min</span>
                    <span>{movies[currentIndex].genres}</span>
                </div>
                <p>{movies[currentIndex].overview}</p>
                <div class="action-buttons">
                    <button
                        class="favourites-btn"
                        class:is-favourite={movies[currentIndex].isFavourite}
                        on:click={toggleFavourite}
                    >
                        {movies[currentIndex].isFavourite 
                            ? "Remove from Favourites"
                            : "Add to Favourites"}
                    </button>
                    <button
                        class="to-watch-btn"
                        class:is-in-watchlist={movies[currentIndex].isInWatchlist}
                        on:click={toggleWatchlist}
                    >
                        {movies[currentIndex].isInWatchlist
                            ? "Remove from Watch Later"
                            : "Add to Watch Later"}
                    </button>
                </div>
            </div>
            <div class="trending-label">
                <span>🔥 Top Trending 🔥</span>
            </div>
        </div>
        <button
            class="nav-btn prev-btn"
            on:click={handlePrev}
            on:mouseenter={stopAutoSlide}
            on:mouseleave={startAutoSlide}>◀</button
        >
        <button
            class="nav-btn next-btn"
            on:click={handleNext}
            on:mouseenter={stopAutoSlide}
            on:mouseleave={startAutoSlide}>▶</button
        >
    {:else}
        <p>Loading movies...</p>
    {/if}
</div>

<style>
    .slider {
        position: relative;
        width: 100%;
        height: 100vh;
        overflow: hidden;
        font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
            "Ubuntu", sans-serif;
        color: white;
    }

    .slider-bg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        padding: 2rem;
    }

    .slider-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            to bottom,
            rgba(0, 0, 0, 0.5),
            rgba(0, 0, 0, 0.8)
        );
        z-index: 1; /* Keep it above the background image */
    }

    .movie-details {
        position: relative; /* Ensure it sits above the gradient */
        z-index: 2; /* Keep it above the gradient overlay */
        background: rgba(0, 0, 0, 0.237);
        padding: 2rem;
        border-radius: 1rem;
        max-width: 50%;
        font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
            "Ubuntu", sans-serif;
        margin-bottom: 7%;
    }

    .movie-details h1 {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .movie-details p {
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .movie-meta {
        display: flex;
        justify-content: space-around;
        font-size: 0rem;
        margin-bottom: 1rem;
    }

    .nav-btn {
        position: absolute;
        top: 80%; /* Slightly above the middle of the slider */
        right: 0.4rem; /* Align both buttons to the right */
        background: #0985774a;
        color: white;
        border: none;
        font-size: 1rem;
        padding: 1rem;
        cursor: pointer;
        transition: background 0.3s;
        z-index: 3;
    }

    .nav-btn:hover {
        background: #098558b6;
    }

    .prev-btn {
        top: 72.5%; /* Slightly below the next button */
    }

    .action-buttons {
        margin-top: 20px;
    }

    .action-buttons button {
        padding: 12px 20px;
        border-radius: 5px;
        font-size: 1rem;
        margin-right: 10px;
        cursor: pointer;
        border: none;
        transition: all 0.3s ease;
    }

    /* Default button styles */
    .favourites-btn {
        background-color: #333;
        color: white;
        border: 2px solid transparent;
    }

    /* Add-to-Favourites style */
    .favourites-btn:not(.is-favourite) {
        background-color: #098577; /* Green for adding */
    }

    /* Remove-from-Favourites style */
    .favourites-btn.is-favourite {
        background-color: #e50914; /* Netflix red for removing */
        border-color: #b71c1c; /* Red border for distinction */
    }

    /* Hover effects */
    .favourites-btn:hover:not(.is-favourite) {
        background-color: #064e45; /* Darker green */
    }

    .favourites-btn:hover.is-favourite {
        background-color: #b71c1c; /* Darker red */
    }

    /* Default Watch Later button styles */
    .to-watch-btn {
        background-color: #333;
        color: white;
        border: 2px solid transparent;
    }
    
    /* Add-to-Watchlist style */
    .to-watch-btn:not(.is-in-watchlist) {
        background-color: #098577; /* Green for adding */
    }
    
    /* Remove-from-Watchlist style */
    .to-watch-btn.is-in-watchlist {
        background-color: #e50914; /* Netflix red for removing */
        border-color: #b71c1c; /* Red border for distinction */
    }
    
    /* Hover effects */
    .to-watch-btn:hover:not(.is-in-watchlist) {
        background-color: #064e45; /* Darker green */
    }
    
    .to-watch-btn:hover.is-in-watchlist {
        background-color: #b71c1c; /* Darker red */
    }

    .trending-label {
        position: absolute;
        bottom: 5rem; /* Keep it near the bottom */
        left: 50%; /* Center it horizontally */
        transform: translateX(-50%); /* Adjust centering */
        background: rgba(0, 0, 0, 0.6); /* Semi-transparent background */
        color: white;
        font-size: 1.2rem;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem; /* Space between fire icon and text */
        z-index: 3;
    }

    .trending-label span {
        display: inline-block;
        filter: grayscale(1);
    }
</style>
