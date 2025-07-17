<script lang="ts">
  import { onMount } from "svelte";
  interface Props {
    logo?: string;
  }

  let { logo = "/assets/img/logo.png" }: Props = $props();

  let searchQuery = $state("");

  let navItems = [
    { name: "Home", link: "../components/Home" },
    { name: "Genre", link: "../components/Genre" },
    { name: "Actors", link: "../components/Actors" },
    { name: "Crew", link: "../components/Crew" },
    { name: "Country", link: "../components/Country" },
    { name: "Favourites", link: "../components/Favourites" },
    { name: "To Watch Later", link: "../components/ToWatchLater" },
  ];

  const handleSearch = async () => {
    console.log("Search query:", searchQuery);
    if (searchQuery.trim()) {
      window.location.href = `/components/movieSearchResult?query=${encodeURIComponent(searchQuery)}`;
    }
  };

  // Handle Enter key press
  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSearch();
    }
  };

  const handleLogout = () => {
    console.log("User logged out");

    // Clear all localStorage data
    localStorage.clear();

    // Optionally clear sessionStorage if you're using it
    sessionStorage.clear();

    // Redirect to login page
    window.location.href = "/";
  };
</script>

<nav>
  <div class="nav-container">
    <div class="navbar-logo">
      <a href="../components/Home"
        ><img src={logo || "/placeholder.svg"} alt="Logo" class="logo" /></a
      >
    </div>

    <div class="navbar-nav">
      {#each navItems as item}
        <a href={item.link} class="nav-link">{item.name}</a>
      {/each}
    </div>

    <div class="navbar-right">
      <input
        type="text"
        class="navbar-search"
        bind:value={searchQuery}
        placeholder="Search Movies..."
        onkeydown={handleKeyDown}
      />
      <button class="logout-btn" onclick={handleLogout}>Logout</button>
    </div>
  </div>
</nav>

<style>
  /* Navbar */
  nav {
    width: 100%;
    height: auto;
    background: linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0.9),
      rgba(0, 0, 0, 0.04)
    );
    padding: 10px 0px;
    position: relative;
    z-index: 10;
  }

  .nav-container {
    max-width: 90vw;
    margin: auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 10px;
    z-index: 10;
  }

  .navbar-logo {
    flex-shrink: 0;
  }

  .logo {
    width: 140px;
    height: auto;
  }

  .navbar-nav {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-left: 2rem;
    flex-grow: 1;
  }

  .nav-link {
    color: rgba(255, 255, 255, 0.9);
    text-decoration: none;
    font-size: 1.1rem;
    font-weight: 500;
    padding: 0.5rem 0.5rem;
    border-radius: 6px;
    transition: all 0.3s ease;
    font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
      "Ubuntu", sans-serif;
    position: relative;
    white-space: nowrap;
  }

  .nav-link:hover {
    color: #098577;
    background-color: rgba(9, 133, 119, 0.1);
    transform: translateY(-1px);
  }

  .nav-link::after {
    content: "";
    position: absolute;
    bottom: -2px;
    left: 50%;
    width: 0;
    height: 2px;
    background-color: #098577;
    transition: all 0.3s ease;
    transform: translateX(-50%);
  }

  .nav-link:hover::after {
    width: 80%;
  }

  /* Right side container */
  .navbar-right {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-shrink: 0;
  }

  .navbar-search {
    padding: 8px 15px;
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    background-color: rgba(15, 16, 20, 0.5);
    color: white;
    outline: none;
    width: 250px;
    transition:
      width 0.3s,
      background-color 0.3s,
      border-color 0.3s;
    font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
      "Ubuntu", sans-serif;
  }

  .navbar-search:focus {
    width: 300px;
    background-color: rgba(15, 16, 20, 0.7);
    border-color: #098577;
  }

  .navbar-search::placeholder {
    color: rgba(255, 255, 255, 0.6);
  }

  .logout-btn {
    background-color: #098577;
    color: #fff;
    border: none;
    padding: 8px 15px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
    transition:
      background-color 0.3s,
      transform 0.2s;
    font-family: "Netflix Sans", "Helvetica Neue", "Segoe UI", "Roboto",
      "Ubuntu", sans-serif;
    white-space: nowrap;
  }

  .logout-btn:hover {
    background-color: #064e45;
    transform: scale(1.05);
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .navbar-nav {
      gap: 1.5rem;
      margin-left: 2rem;
    }

    .nav-link {
      font-size: 0.9rem;
      padding: 0.4rem 0.8rem;
    }
  }

  @media (max-width: 992px) {
    .navbar-nav {
      gap: 1rem;
      margin-left: 1rem;
    }

    .nav-link {
      font-size: 0.85rem;
      padding: 0.3rem 0.6rem;
    }

    .navbar-search {
      width: 150px;
    }

    .navbar-search:focus {
      width: 200px;
    }
  }

  @media (max-width: 768px) {
    .nav-container {
      max-width: 95vw;
      padding: 0 10px;
    }

    .navbar-nav {
      display: none; /* Hide navigation links on mobile - you might want to implement a mobile menu */
    }

    .logo {
      width: 100px;
    }

    .navbar-search {
      width: 120px;
    }

    .navbar-search:focus {
      width: 160px;
    }
  }
</style>
