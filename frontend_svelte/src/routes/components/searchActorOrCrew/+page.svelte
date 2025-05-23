<script>
    import { onMount } from "svelte";
    import { redirectToRegisterIfNotAuthenticated } from "../../../utils/auth.js";
    import MovieCard from "../Slider/movie_card.svelte";
    import Navbar from "../Home/Navbar2.svelte";
    import SideBar from "../Home/SideBar.svelte";
    import Footer from "../Register/Footer1.svelte";
    import Line from "../Register/Line.svelte";
  
    let type = "";
    let query = "";
    let movies = [];
    let id= "";
    let error = "";
    let sidebar = false;
  
    // Extract query parameter on mount
    onMount(async () => {
        redirectToRegisterIfNotAuthenticated();
        const urlParams = new URLSearchParams(window.location.search);
        query = urlParams.get("query"); // Assign to existing `let query`
        type = urlParams.get("type");  // Assign to existing `let type`
        id = urlParams.get("id");      // Assign to the new `let id`
        try {
            let response;
            if (query) {
                // Name-based search
                response = await fetch(`http://localhost:5000/api/search_${type}?query=${encodeURIComponent(query)}&limit=10`);
            } else if (id) {
                // ID-based search
                response = await fetch(`http://localhost:5000/api/search_${type}?${type}_id=${encodeURIComponent(id)}&limit=10`);
            } else {
                error = "No valid search parameters provided.";
                return;
            }

            if (!response.ok) {
                error = "Failed to fetch movies.";
                return;
            }

            const data = await response.json();
            movies = data.movies || [];
            } catch (err) {
              console.error("Error fetching movies:", err);
              error = "An error occurred while fetching movies.";
            } 
    });
  </script>
  
  <div class="wrapper">
    <div class="navbar-wrapper">
      <Navbar />
    </div>
  
    <div class="sidebar-wrapper">
      <SideBar bind:open={sidebar} />
    </div>
  
    <div class="search-results-container">
      <div class="content">
        <h1>Search Results for "{query}"</h1>
        {#if error}
          <p class="error">{error}</p>
        {:else if movies.length === 0}
          <p>No results found.</p>
        {:else}
          <div class="movies-grid">
            {#each movies.slice(0, 8) as { poster_path, movie_id }}
              <MovieCard poster_path={poster_path} movie_id={movie_id} />
            {/each}
          </div>
        {/if}
      </div>
    </div>
  
    <Line />
    <Footer />
  </div>
  
  <style>
    .wrapper {
      position: relative;
      min-height: 100vh;
      overflow: hidden;
      background-color: #121212;
      font-family: 'Netflix Sans', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
    }
  
    .navbar-wrapper {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      z-index: 10;
    }
  
    .sidebar-wrapper {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
    }
  
    .search-results-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem;
      margin-top: 80px;
    }
  
    .content {
      max-width: 1200px;
      width: 100%;
      background-color: #141414;
      color: #fff;
      padding: 2rem;
      border-radius: 10px;
      box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
    }
  
    h1 {
      text-align: center;
      font-size: 2rem;
      margin-bottom: 2rem;
    }
  
    .error {
      color: red;
      text-align: center;
      margin-bottom: 1rem;
    }
  
    .movies-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
      justify-content: center;
    }
  
    .movies-grid::-webkit-scrollbar {
      width: 8px;
    }
  
    .movies-grid::-webkit-scrollbar-thumb {
      background-color: #064E45;
      border-radius: 10px;
    }
  
    .movies-grid::-webkit-scrollbar-track {
      background-color: #121212;
    }
  
    @media (max-width: 768px) {
      .search-results-container {
        padding: 1rem;
      }
    }
  </style>
  