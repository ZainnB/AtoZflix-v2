<script>
    import { onMount } from "svelte";
    import { fly } from "svelte/transition";
    import { api } from '../../../lib/api.js';
    import { getCurrentUser } from '../../../utils/auth.js';

    let movies = $state([]);
    let currentIndex = $state(0);
    let interval;
    let user_id = null;
    let isTransitioning = $state(false);
    let slideDirection = $state(1); // 1 for next, -1 for previous

    onMount(async () => {
        try {
            const user = getCurrentUser();
            user_id = user?.userId;
            
            const data = await api.get("/api/trending?limit=5");
            movies = data.movies || [];

            // Check fav/watchlist status for each movie if authenticated
            if (user_id) {
                for (const movie of movies) {
                    const movie_id = movie.movie_id;

                    try {
                        const favData = await api.get(`/api/check_favourite?user_id=${user_id}&movie_id=${movie_id}`);
                        movie.isFavourite = favData.is_favourite;
                    } catch (e) {
                        movie.isFavourite = false;
                    }

                    try {
                        const wlData = await api.get(`/api/check_watchlist?user_id=${user_id}&movie_id=${movie_id}`);
                        movie.isInWatchlist = wlData.is_in_watchlist;
                    } catch (e) {
                        movie.isInWatchlist = false;
                    }
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

        try {
            if (movie.isFavourite) {
                await api.post("/api/remove_favourite", { movie_id });
            } else {
                await api.post("/api/add_favourite", { movie_id });
            }
            movie.isFavourite = !movie.isFavourite;
            movies = [...movies];
        } catch (error) {
            console.error("Failed to update favourite status:", error);
        }
    };

    // The API returns an RFC-1123 date, so the badge was reading
    // "Sun, 15 Mar 2026 00:00:00 GMT" - most of a phone's width for one fact.
    const releaseYear = (value) => {
        if (!value) return "";
        const d = new Date(value);
        return Number.isNaN(d.getTime()) ? String(value).slice(0, 4) : d.getFullYear();
    };

    const toggleWatchlist = async () => {
        const movie = movies[currentIndex];
        const movie_id = movie.movie_id;

        try {
            if (movie.isInWatchlist) {
                await api.post("/api/remove_from_watchlist", { movie_id });
            } else {
                await api.post("/api/add_to_watchlist", { movie_id });
            }
            movie.isInWatchlist = !movie.isInWatchlist;
            movies = [...movies];
        } catch (error) {
            console.error("Failed to update watchlist status:", error);
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
                            >{releaseYear(movies[currentIndex].release_date)}</span
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
        <!-- A bare "Loading movies..." line sat at the top-left of an otherwise
             empty full-height block, colliding with the logo. A shaped skeleton
             holds the hero's real layout instead. -->
        <div class="hero-skeleton" aria-hidden="true">
            <div class="hs-title skeleton"></div>
            <div class="hs-meta skeleton"></div>
            <div class="hs-copy skeleton"></div>
            <div class="hs-actions">
                <div class="hs-btn skeleton"></div>
                <div class="hs-btn skeleton"></div>
            </div>
        </div>
        <span class="visually-hidden">Loading featured movies…</span>
    {/if}
</div>

<style>
    .slider {
        position: relative;
        width: 100%;
        /* Was a flat 100vh. Two problems on a phone: `vh` is measured against
           the viewport WITH the browser chrome hidden, so the hero jumps as the
           URL bar collapses; and a full screen of backdrop with nothing else
           visible means the rest of the page is entirely below the fold.
           `svh` is the stable small-viewport unit, and the cap keeps the hero
           from dominating tall desktop screens. */
        height: min(78svh, 760px);
        overflow: hidden;
        font-family: var(--font);
        color: white;
    }

    .visually-hidden {
        position: absolute;
        width: 1px;
        height: 1px;
        margin: -1px;
        padding: 0;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
        border: 0;
    }

    .hero-skeleton {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.9rem;
        padding-inline: var(--gutter);
        padding-top: 4rem;
        background: linear-gradient(to bottom, var(--surface), var(--bg));
    }

    .hs-title { height: clamp(2rem, 6vw, 3rem); width: min(70%, 22rem); border-radius: 8px; }
    .hs-meta  { height: 1.1rem; width: min(45%, 14rem); border-radius: 6px; }
    .hs-copy  { height: 3.5rem; width: min(80%, 34rem); border-radius: 8px; }
    .hs-actions { display: flex; gap: 0.6rem; flex-wrap: wrap; }
    .hs-btn { height: 2.6rem; width: 8.5rem; border-radius: 999px; }

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
        /* 4rem of fixed padding each side left only ~247px of usable width on a
           375px phone. The shared gutter token scales with the viewport and
           keeps the hero copy aligned with every row below it. */
        padding-inline: var(--gutter);
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
        max-width: min(50%, 44rem);
        margin-top: 6rem;
    }

    .movie-details h1 {
        font-size: clamp(1.75rem, 5.5vw, 3rem);
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
        letter-spacing: -1px;
        line-height: 1.1;
        text-wrap: balance;
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
        .slider {
            /* Shorter still on a phone, so the rows underneath are visible
               without scrolling a whole screen first. */
            height: min(62svh, 520px);
        }

        /* Vertically centring a tall stack inside a fixed-height box makes it
           overflow BOTH ways - the title disappeared behind the navbar while the
           description bled into the next section. Anchoring to the bottom (the
           standard streaming-hero treatment) means overflow can only ever go one
           way, and the clamp below stops it going anywhere at all. */
        .slider-bg {
            justify-content: flex-end;
            /* Clears the progress dots pinned to the bottom edge. */
            padding-bottom: 2.25rem;
        }

        .movie-details {
            max-width: 100%;
            margin-left: 0;
            margin-top: 0;
        }

        .movie-details h1 {
            /* Two lines maximum; a long title otherwise eats the whole hero. */
            display: -webkit-box;
            -webkit-line-clamp: 2;
            line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            margin-bottom: 0.6rem;
        }

        .movie-meta {
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-bottom: 0.6rem;
        }

        /* HD and the certificate are decoration, not information - first to go
           when the row has to wrap. */
        .meta-badge.hd,
        .meta-badge.rating {
            display: none;
        }

        .movie-description {
            display: -webkit-box;
            -webkit-line-clamp: 3;
            line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            max-width: 100%;
            font-size: 0.88rem;
            margin-bottom: 0.9rem;
        }

        /* Decorative, and on a phone it sat directly on top of the Watch Later
           button. The hero is self-evidently the featured slot; the label is
           not carrying information worth a collision. */
        .trending-label {
            display: none;
        }

        /* Two buttons stacked full-width pushed the description off screen.
           Side by side they fit, and each still clears the 44px touch target. */
        .action-buttons {
            flex-direction: row;
            flex-wrap: wrap;
            align-items: stretch;
            gap: 0.5rem;
        }

        .action-buttons button {
            width: auto;
            flex: 1 1 auto;
            min-height: 44px;
            margin-bottom: 0;
        }
        /* Both of these previously sat at the bottom, directly on top of the
           now bottom-anchored copy and action buttons. The arrows move up out
           of the way; the progress dots sit at the very bottom edge. */
        .nav-btn-group {
            top: calc(var(--nav-height) + 0.5rem);
            bottom: auto;
            right: 0.75rem;
        }
        .nav-btn {
            width: 44px;
            height: 44px;
        }
        .progress-container {
            bottom: 0.5rem;
        }
        .progress-bar {
            gap: 0.25rem;
        }
    }
</style>
