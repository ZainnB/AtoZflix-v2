<script>
    import { onMount } from "svelte";

    let movies = [];
    let currentIndex = 0;

    import { api } from '../../../lib/api.js';
    
    onMount(async () => {
        try {
            const data = await api.get("/api/trending?limit=20");
            movies = data.movies ? data.movies.slice(5) : [];
            console.log("Movies fetched successfully:", movies);

            // Start the slider functionality
            startAutoSlide();
        } catch (error) {
            console.error("Error fetching trending movies:", error);
        }
    });

    function slideNext() {
        currentIndex = (currentIndex + 1) % Math.ceil(movies.length / 4); // Move to the next set of 4 movies
    }

    function slidePrev() {
        currentIndex =
            (currentIndex - 1 + Math.ceil(movies.length / 4)) %
            Math.ceil(movies.length / 4); // Move to the previous set
    }

    function startAutoSlide() {
        setInterval(() => {
            slideNext();
        }, 9000);
    }
</script>

<div class="top15-medium">
    <!-- Slider Container -->
    <div class="slider" style="transform: translateX(-{currentIndex * 100}%);">
        {#each Array(Math.ceil(movies.length / 4)) as _, slideIndex}
            <div class="slide">
                {#each movies.slice(slideIndex * 4, slideIndex * 4 + 4) as movie}
                    <a
                        href={`/components/MovieDetail?movie_id=${movie.movie_id}`}
                        class="movie-link"
                    >
                        <div class="movie-card">
                            <div
                                class="movie-poster"
                                style="background-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.8)), url(https://image.tmdb.org/t/p/w500{movie.backdrop_path})"
                            >
                                <div class="movie-info">
                                    <h3>{movie.title}</h3>
                                    <div class="genres">
                                        {#each movie.genres as genre}
                                            <span>{genre}</span>
                                        {/each}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </a>
                {/each}
            </div>
        {/each}
    </div>

    <!-- Slider Navigation Buttons -->
    <div class="slider-buttons">
        <button class="prev-button" on:click={slidePrev}>❮</button>
        <button class="next-button" on:click={slideNext}>❯</button>
    </div>
</div>

<style>
    /* Main Container */
    .top15-medium {
        position: relative;
        overflow: hidden;
        background-color: #000000;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
    }

    /* Slider */
    .slider {
        display: flex;
        transition: transform 0.5s ease-in-out;
        gap: 1rem;
    }

    .slide {
        display: flex;
        flex: 0 0 100%;
        gap: 1rem; /* Spacing between movie cards */
        /* Align with the shared page column instead of sitting flush to the
           window edge, so this row lines up with the carousels below it. */
        padding-inline: var(--gutter);
        box-sizing: border-box;
    }

    .movie-link {
    text-decoration: none;
    display: block;
    height: 100%;
    /* Was width:100%, which made every link fill the slide and left the card's
       own flex-basis with nothing to divide. The link now sizes to its card. */
    flex: 0 0 calc(25% - 0.75rem);
    min-width: 0;
    color: inherit; /* so text color stays white */
    }


    /* Movie Card Styling */
    .movie-card {
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
        background: transparent;
        display: flex;
        flex-direction: column;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
        transition:
            transform 0.3s ease,
            box-shadow 0.3s ease;
        height: 200px;
    }

    .movie-card:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.515);
    }

    /* Poster with Gradient Overlay */
    .movie-poster {
        height: 100%;
        background-size: cover;
        background-position: center;
        position: relative;
        /* Column flex so the caption below can sit at the foot of the card at
           any card height, instead of relying on a fixed margin. */
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        overflow: hidden;
    }

    /* Transparent Movie Info */
    .movie-info {
        padding: 0.5rem;
        /* Pushes the caption to the foot of the 200px card. A fixed 130px
           margin broke the moment the card got shorter on mobile - the caption
           was shoved out of its own card. `margin-top: auto` in this column
           flex container does the same job at any height. */
        margin-top: auto;
        color: rgb(255, 255, 255);
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
            "Ubuntu", sans-serif;
        background: linear-gradient(
            to bottom,
            rgba(0, 0, 0, 0.05),
            rgba(0, 0, 0, 0.4)
        );
    }

    .movie-info h3 {
        font-size: 1.4rem;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
    }

    .movie-info .genres {
        display: flex;
        flex-wrap: nowrap;
        gap: 0.25rem;
        /* Genre lists are longer than the card is wide; clip rather than let
           them spill past the card edge. */
        overflow: hidden;
        white-space: nowrap;
    }

    .movie-info .genres span {
        font-size: 0.9rem;
        color: #098577;
    }

    /* Slider Navigation Buttons */
    .slider-buttons {
        position: absolute;
        top: 50%;
        right: 0.2rem;
        display: flex;
        flex-direction: column;
        transform: translateY(-50%);
    }

    .slider-buttons button {
        background: rgba(0, 0, 0, 0.7);
        color: white;
        border: none;
        width: 47px;
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: background 0.3s ease;
    }

    .slider-buttons button:hover {
        background: rgba(255, 255, 255, 0.7);
        color: black;
    }

    /*
      Four cards across a 375px screen is ~90px each - the poster is a smear and
      the 1.4rem title cannot fit. The JS still chunks the list in fours, so
      rather than change the paging logic the slide wraps into a 2x2 grid: same
      four films per page, twice the width each.
    */
    @media (max-width: 900px) {
        .slide {
            flex-wrap: wrap;
            gap: 0.75rem;
            /* Reserve the strip the prev/next buttons occupy, otherwise the
               right-hand card sits underneath them. */
            padding-right: calc(var(--gutter) + 2.5rem);
        }

        .slider-buttons button {
            width: 34px;
            height: 64px;
        }

        .movie-link {
            flex: 0 0 calc(50% - 0.375rem);
        }

        .movie-card {
            height: 150px;
        }

        .movie-info h3 {
            font-size: 1rem;
        }

        .genres {
            font-size: 0.72rem;
        }
    }

    @media (max-width: 480px) {
        .movie-card {
            height: 128px;
        }

        .movie-info h3 {
            font-size: 0.9rem;
        }

        /* Genre chips are the first thing to go when space is tight - the
           title and artwork carry the card on their own. Selector matches the
           base rule's specificity, which a bare `.genres` did not. */
        .movie-info .genres {
            display: none;
        }
    }
</style>
