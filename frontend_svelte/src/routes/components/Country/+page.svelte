<script>
  import CountrySlider from "../GenralSlider/+page.svelte";
  import Navbar from "../Home/Navbar2.svelte";
  import Footer from "../Register/Footer1.svelte";
  import Line from "../Register/Line.svelte";
  import { redirectToRegisterIfNotAuthenticated } from "/src/utils/auth.js";
  import { onMount } from "svelte";

  let country_list = $state([]);
  let selectedCountries = $state(new Set());

  // Fetch country list on component mount
  onMount(async () => {
    redirectToRegisterIfNotAuthenticated();
    try {
      const response = await fetch("http://127.0.0.1:5000/api/get_country_names");
      if (!response.ok) {
        console.error("Failed to fetch country list");
        return;
      }
      const data = await response.json();
      country_list = data.countries;
    } catch (error) {
      console.error("Error fetching countries:", error);
    }
  });

  // Function to handle checkbox selection
  function toggleCountry(country) {
    if (selectedCountries.has(country)) {
      selectedCountries.delete(country);
    } else {
      selectedCountries.add(country);
    }
    selectedCountries = new Set(selectedCountries); // Trigger reactivity
  }

  // Check if country is selected
  function isCountrySelected(country) {
    return selectedCountries.has(country);
  }
</script>

<div class="wrapper">
  <div class="navbar-wrapper">
    <Navbar />
  </div>
  
  <div class="content-container">
    <!-- Country Selection Section -->
    <div class="selection-panel">
      <h2 class="panel-title">Select Countries</h2>
      <div class="checkbox-container">
        {#each country_list as country}
          <label class="checkbox-item">
            <input
              type="checkbox"
              checked={isCountrySelected(country)}
              onchange={() => toggleCountry(country)}
              class="checkbox-input"
            />
            <span class="checkbox-custom"></span>
            <span class="checkbox-label">{country}</span>
          </label>
        {/each}
      </div>
    </div>

    <!-- Sliders Section -->
    <div class="sliders-container">
      {#if selectedCountries.size === 0}
        <div class="empty-state">
          <h3>Select countries to view movie collections</h3>
          <p>Choose one or more countries above to see curated movie sliders.</p>
        </div>
      {:else}
        {#each Array.from(selectedCountries) as country}
          <div class="slider-wrapper" key={country}>
            <CountrySlider type="country" value={country} limit={10} heading={country} />
          </div>
        {/each}
      {/if}
    </div>
  </div>
  
  <Line />
  <Footer />
</div>

<style>
  .wrapper {
    min-height: 100vh;
    background-color: #121212;
    font-family: 'Netflix Sans', 'Helvetica Neue', 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
  }

  .navbar-wrapper {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 10;
  }

  .content-container {
    padding-top: 10px;
    min-height: calc(80vh - 50px);
  }

  .selection-panel {
    background-color: #121212;
    padding: 2rem;
    border-bottom: 2px solid #333;
    position: relative;
    top: 50px;
    z-index: 5;
  }

  .panel-title {
    color: #098577;
    font-size: 1.6rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .checkbox-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    justify-content: center;
    max-width: 1500px;
    margin: 0 auto;
  }

  .checkbox-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid transparent;
    min-width: 100px;
    justify-content: flex-start;
  }

  .checkbox-item:hover {
    background-color: rgba(9, 133, 119, 0.1);
    transform: translateY(-2px);
  }

  .checkbox-input {
    display: none;
  }

  .checkbox-custom {
    width: 18px;
    height: 18px;
    border: 2px solid #666;
    border-radius: 4px;
    position: relative;
    transition: all 0.3s ease;
    flex-shrink: 0;
  }

  .checkbox-input:checked + .checkbox-custom {
    background-color: #098577;
    border-color: #098577;
  }

  .checkbox-input:checked + .checkbox-custom::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-size: 13px;
    font-weight: bold;
  }

  .checkbox-item:hover .checkbox-custom {
    border-color: #098577;
    box-shadow: 0 0 0 2px rgba(9, 133, 119, 0.2);
  }

  .checkbox-label {
    color: #fff;
    font-size: 1rem;
    font-weight: 500;
    transition: color 0.3s ease;
  }

  .checkbox-item:hover .checkbox-label {
    color: #098577;
  }

  .sliders-container {
    background-color: #000000;
    padding: 2rem;
    min-height: 60vh;
  }

  .slider-wrapper {
    margin-bottom: 2rem;
    animation: slideIn 0.4s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 65vh;
    text-align: center;
    color: #666;
  }

  .empty-state h3 {
    font-size: 1.5rem;
    margin-bottom: 2rem;
    color: #fff;
  }

  .empty-state p {
    font-size: 1rem;
    max-width: 400px;
    line-height: 1.6;
  }

  @media (max-width: 1024px) {
    .checkbox-container {
      gap: 0.75rem;
    }
    
    .checkbox-item {
      min-width: 100px;
      padding: 0.6rem 0.8rem;
    }
    
    .checkbox-label {
      font-size: 0.85rem;
    }
  }

  @media (max-width: 768px) {
    .selection-panel {
      padding: 1.5rem 1rem;
    }
    
    .panel-title {
      font-size: 1.5rem;
      margin-bottom: 1rem;
    }
    
    .checkbox-container {
      gap: 0.5rem;
    }
    
    .checkbox-item {
      min-width: 90px;
      padding: 0.5rem 0.6rem;
    }
    
    .checkbox-label {
      font-size: 0.8rem;
    }
    
    .sliders-container {
      padding: 1rem;
    }
  }
</style>
