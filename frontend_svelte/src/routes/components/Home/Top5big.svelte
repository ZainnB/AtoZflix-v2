<script>
    import { onMount } from "svelte";
    import { fly } from "svelte/transition";

    let movies = $state([]);
    let currentIndex = $state(0);
    let interval;
    let user_id = null;
    let isTransitioning = $state(false);
    let slideDirection = $state(1); // 1 for next, -1 for previous

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
            if (!isTransitioning) {
                handleNext();
            }
        }, 9000);
    };

    const stopAutoSlide = () => clearInterval(interval);

    const handleNext = async () => {
        if (isTransitioning) return;
        isTransitioning = true;
        slideDirection = 1;
        currentIndex = (currentIndex + 1) % movies.length;
        setTimeout(() => {
            isTransitioning = false;
        }, 500);
    };

    const handlePrev = async () => {
        if (isTransitioning) return;
        isTransitioning = true;
        slideDirection = -1;
        if (currentIndex === 0) {
            currentIndex = movies.length - 1;
        } else {
            currentIndex = (currentIndex - 1 + movies.length) % movies.length;
        }
        setTimeout(() => {
            isTransitioning = false;
        }, 500);
    };

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
        {#key currentIndex}
            <div
                class="slider-bg"
                style= "background-image: linear-gradient(to bottom, rgba(0, 0, 0, 0) 75%, #000000 100%), 
                    url(https://image.tmdb.org/t/p/original{movies[currentIndex].backdrop_path})"
                in:fly={{ x: 300 * slideDirection, duration: 500, delay: 100 }}
                out:fly={{ x: -300 * slideDirection, duration: 400 }}
            >
                <!-- Gradient Overlay -->
                <div class="slider-overlay"></div>

                <div class="movie-details">
                    <h1>{movies[currentIndex].title}</h1>
                    <div class="movie-meta">
                        <span class="meta-badge hd">HD</span>
                        <span class="meta-badge rating">PG-13</span>
                        <span class="meta-badge star"
                            >⭐ {movies[currentIndex].rating}</span
                        >
                        <span class="meta-badge year"
                            >{movies[currentIndex].release_date}</span
                        >
                        <span class="meta-badge duration"
                            >{movies[currentIndex].duration} min</span
                        >
                        <span class="meta-badge genre">
                            {#each movies[currentIndex].genres as genre}
                                <span>{genre}</span>
                            {/each}</span
                        >
                    </div>
                    <p class="movie-description">
                        {movies[currentIndex].overview}
                    </p>
                    <div class="action-buttons">
                        <button
                            class="favourites-btn"
                            class:is-favourite={movies[currentIndex]
                                .isFavourite}
                            onclick={toggleFavourite}
                        >
                            {movies[currentIndex].isFavourite
                                ? "Remove from Favourites"
                                : "Add to Favourites"}
                        </button>
                        <button
                            class="to-watch-btn"
                            class:is-in-watchlist={movies[currentIndex]
                                .isInWatchlist}
                            onclick={toggleWatchlist}
                        >
                            {movies[currentIndex].isInWatchlist
                                ? "Remove from Watch Later"
                                : "Add to Watch Later"}
                        </button>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="progress-container">
                    <div class="progress-bar">
                        {#each movies as _, index}
                            <div
                                class="progress-segment"
                                class:active={index === currentIndex}
                            ></div>
                        {/each}
                    </div>
                </div>

                <div class="trending-label">
                    <span>🔥 Trending Now 🔥</span>
                </div>
            </div>
        {/key}
        <!-- Navigation Buttons -->
        <div class="nav-btn-group">
            <button
                class="nav-btn"
                onclick={handlePrev}
                onmouseenter={stopAutoSlide}
                onmouseleave={startAutoSlide}
                disabled={isTransitioning}
                aria-label="Previous Movie"
            >
                <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                >
                    <path d="M15 18l-6-6 6-6" />
                </svg>
            </button>
            <button
                class="nav-btn"
                onclick={handleNext}
                onmouseenter={stopAutoSlide}
                onmouseleave={startAutoSlide}
                disabled={isTransitioning}
                aria-label="Next Movie"
            >
                <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                >
                    <path d="M9 18l6-6-6-6" />
                </svg>
            </button>
        </div>
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
        right: 0;
        bottom: 0;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: flex-start;
        padding: 0 4rem;
    }

    .slider-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, #000000 100%);
        z-index: 1;
    }

    .movie-details {
        position: relative;
        z-index: 2;
        max-width: 50%;
        margin-left: 1rem;
        margin-top: 6rem;
    }

    .movie-details h1 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
        letter-spacing: -1px;
    }

    .movie-meta {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }

    .meta-badge {
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 500;
        display: inline-block;
    }

    .meta-badge.hd {
        background: #098577;
        color: black;
        font-weight: 600;
    }

    .meta-badge.rating {
        background: rgba(255, 255, 255, 0.2);
        color: white;
    }

    .meta-badge.star {
        background: rgba(255, 255, 255, 0.2);
        color: white;
    }

    .meta-badge.year,
    .meta-badge.duration,
    .meta-badge.genre {
        background: rgba(255, 255, 255, 0.2);
        color: white;
    }

    .movie-description {
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 1.2rem;
        max-width: 80%;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        color: rgba(255, 255, 255, 0.9);
    }

    .action-buttons {
        margin-top: 20px;
    }

    .action-buttons button {
        padding: 10px 16px;
        border-radius: 5px;
        font-size: 1rem;
        font-weight: 400;
        margin-right: 10px;
        cursor: pointer;
        border: none;
        transition: all 0.3s ease;
        font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
            "Ubuntu", sans-serif;
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

    /* Navigation Buttons */
    .nav-btn-group {
        position: absolute;
        bottom: 8rem;
        right: 2rem;
        display: flex;
        gap: 0.75rem;
        z-index: 3;
    }

    .nav-btn {
        width: 45px;
        height: 45px;
        background: rgba(0, 0, 0, 0.5);
        color: white;
        border: 1.5px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(6px);
    }

    .nav-btn:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.7);
        color: black;
        border-color: white;
        transform: scale(1.1);
    }

    .nav-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    /* Progress Bar */
    .progress-container {
        position: absolute;
        bottom: 5rem;
        left: 50%;
        transform: translateX(-50%);
        z-index: 3;
    }

    .progress-bar {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }

    .progress-segment {
        width: 40px;
        height: 4px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 2px;
        transition: all 0.3s ease;
    }

    .progress-segment.active {
        background: white;
        width: 60px;
    }
    .trending-label {
        position: absolute;          
        bottom: 0;
        left: 0;
        width: 100%;                  
        text-align: center;           
        color: white;
        font-size: 1rem;
        font-weight: 500;
        padding: 30px 0;
        background: linear-gradient(to top, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.01));
        z-index: 3;
        font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
            "Ubuntu", sans-serif;
    }

    @media (max-width: 768px) {
        .movie-details {
            max-width: 80%;
            margin-left: 1rem;
        }

        .movie-details h1 {
            font-size: 2.5rem;
        }

        .action-buttons {
            flex-direction: column;
            align-items: flex-start;
        }

        .action-buttons button {
            width: 100%;
            margin-bottom: 10px;
        }
        .nav-btn-group {
            bottom: 1rem;
            right: 1rem;
        }
        .nav-btn {
            width: 36px;
            height: 36px;
        }
        .progress-container {
            bottom: 6rem;
        }
        .progress-bar {
            gap: 0.25rem;
        }
    }
</style>
