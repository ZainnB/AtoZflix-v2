 <!-- GenralSlider2 used in Actors/Cres view all and searches for displaying a slider of movies or based on the provided API name, type, and value. -->
<script>
    import { onMount } from "svelte";
    import MovieCard from "../Slider/movie_card.svelte";
  
    export let api_name;            
    export let type;            
    export let value;
    export let limit;
    let movies = [];      
    let currentIndex = 0; 
    
    // On component mount, fetch movies from the API
    onMount(async () => {
      try {
        const response = await fetch(`http://127.0.0.1:5000/api/${api_name}?${type}_id=${value}&limit=${limit}`);
        if (!response.ok) {
          console.error("Failed to fetch actor movies:", response.status);
          return;
        }
        const data = await response.json();
        movies = data.data || [];
      } catch (error) {
        console.error("Error fetching actor movies:", error);
      }
    });
    
    // Calculate the maximum index for the slider range
    const maxIndex = () => Math.max(0, movies.length - 8);
    
    // Handlers for navigation (next and previous)
    function nextSlide() {
      if (currentIndex < maxIndex()) {
        currentIndex += 1;
      }
    }
  
    function prevSlide() {
      if (currentIndex > 0) {
        currentIndex -= 1;
      }
    }

    function handleViewAll() {
        window.location.href = `/components/searchActorOrCrew?type=${encodeURIComponent(type)}&id=${encodeURIComponent(value)}`;
    }
  </script>
  
  <div class="latest-movies">
    <button class="view-all-btn" on:click={handleViewAll}>View All</button>
  
    <div class="slider-wrapper">
      <button class="slider-btn left" on:click={prevSlide}>&lt;</button>
  
      <div class="slider">
        {#each movies.slice(currentIndex, currentIndex + 8) as movie}
          <MovieCard poster_path={movie.poster_path} movie_id={movie.movie_id} />
        {/each}
      </div>
  
      <button class="slider-btn right" on:click={nextSlide}>&gt;</button>
    </div>
  </div>
  
  <style>
    .latest-movies {
      width: 100%;
      max-width: 1400px;
      color: #000000;
      border-radius: 7px;
      display: flex;
      flex-direction: column;
    }
  
    .view-all-btn {
      background-color: transparent;
      color: #098577;
      border: none;
      font-size: 0.9rem;
      cursor: pointer;
      transition: color 0.3s ease;
      margin-left: auto;
    }
  
    .view-all-btn:hover {
      color: #06eE45; /* Brighter green on hover */
    }
  
    .slider-wrapper {
      display: flex;
      align-items: center;
      position: relative;
    }
  
    .slider {
      display: flex;
      overflow: hidden;
      gap: 0.5rem; /* Reduced gap between movies */
      width: 100%;
    }
  
    .slider-btn {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 3rem; /* Thin horizontal buttons */
      background-color: transparent;
      color: #fff;
      border: none;
      cursor: pointer;
      z-index: 1;
      transition: background-color 0.3s ease;
    }
  
    .slider-btn.left {
      left: 0;
    }
  
    .slider-btn.right {
      right: 0;
    }
  
    .slider-btn:hover {
      background-color: rgba(0, 0, 0, 0.6); /* Darker on hover */
    }
  
    .slider-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  </style>
  