<script>
  import { onMount } from "svelte";
  import { clearAuth } from "../../../lib/api.js";

  let { logo = "/assets/img/logo.png" } = $props();

  let searchQuery = $state("");
  let currentPath = $state("");
  let menuOpen = $state(false);

  const navItems = [
    { name: "Home", link: "/components/Home" },
    { name: "Genre", link: "/components/Genre" },
    { name: "Actors", link: "/components/Actors" },
    { name: "Crew", link: "/components/Crew" },
    { name: "Country", link: "/components/Country" },
    { name: "Favourites", link: "/components/Favourites" },
    { name: "Watch Later", link: "/components/ToWatchLater" },
  ];

  onMount(() => {
    currentPath = window.location.pathname;
  });

  const handleSearch = () => {
    const q = searchQuery.trim();
    if (q) {
      window.location.href = `/components/movieSearchResult?query=${encodeURIComponent(q)}`;
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") handleSearch();
  };

  const handleLogout = () => {
    // Was localStorage.clear() + sessionStorage.clear(), which wipes any
    // unrelated key this origin owns. clearAuth removes exactly the auth keys.
    clearAuth();
    window.location.href = "/";
  };
</script>

<nav>
  <div class="nav-container">
    <a class="navbar-logo" href="/components/Home" aria-label="AtoZflix home">
      <img src={logo} alt="AtoZflix" class="logo" />
    </a>

    <button
      class="menu-toggle"
      onclick={() => (menuOpen = !menuOpen)}
      aria-expanded={menuOpen}
      aria-label="Toggle navigation"
    >
      <span></span><span></span><span></span>
    </button>

    <div class="navbar-nav" class:open={menuOpen}>
      {#each navItems as item}
        <a
          href={item.link}
          class="nav-link"
          class:active={currentPath === item.link}
          aria-current={currentPath === item.link ? "page" : undefined}
        >
          {item.name}
        </a>
      {/each}
    </div>

    <div class="navbar-right" class:open={menuOpen}>
      <div class="search">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" />
        </svg>
        <input
          type="search"
          bind:value={searchQuery}
          onkeydown={handleKeyDown}
          placeholder="Search movies…"
          aria-label="Search movies"
        />
      </div>
      <button class="logout-btn" onclick={handleLogout}>Log out</button>
    </div>
  </div>
</nav>

<style>
  nav {
    width: 100%;
    /* Fades into the page rather than sitting on a hard bar, so it can overlay
       a hero backdrop without cutting it in half. */
    background: linear-gradient(
      to bottom,
      rgba(6, 6, 9, 0.95) 0%,
      rgba(6, 6, 9, 0.7) 55%,
      rgba(6, 6, 9, 0) 100%
    );
    padding-block: 0.75rem 1.5rem;
    z-index: 10;
  }

  /* Same max-width and gutter as .shell, so the logo lines up with the left
     edge of every carousel below it. */
  .nav-container {
    max-width: var(--shell-max);
    margin-inline: auto;
    padding-inline: var(--gutter);
    display: flex;
    align-items: center;
    gap: 1.25rem;
  }

  .navbar-logo {
    flex-shrink: 0;
    display: block;
  }

  .logo {
    width: 130px;
    height: auto;
  }

  .navbar-nav {
    display: flex;
    align-items: center;
    gap: 0.15rem;
    flex-grow: 1;
    min-width: 0;
  }

  .nav-link {
    position: relative;
    padding: 0.45rem 0.7rem;
    border-radius: var(--radius-sm);
    color: var(--text-dim);
    text-decoration: none;
    font-size: 0.88rem;
    font-weight: 500;
    white-space: nowrap;
    transition: color 0.2s var(--ease), background 0.2s var(--ease);
  }

  .nav-link:hover {
    color: var(--text);
    background: rgba(255, 255, 255, 0.06);
  }

  /* The current page is marked, which the old navbar did not do - there was no
     way to tell where you were. */
  .nav-link.active {
    color: var(--text);
    font-weight: 600;
  }

  .nav-link.active::after {
    content: "";
    position: absolute;
    left: 0.7rem;
    right: 0.7rem;
    bottom: 0.1rem;
    height: 2px;
    border-radius: 2px;
    background: var(--accent);
  }

  .navbar-right {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-shrink: 0;
  }

  .search {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.35rem 0.85rem;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-pill);
    background: rgba(0, 0, 0, 0.45);
    transition: border-color 0.2s var(--ease), width 0.2s var(--ease);
  }

  .search:focus-within {
    border-color: var(--accent);
  }

  .search svg {
    flex-shrink: 0;
    width: 0.95rem;
    height: 0.95rem;
    fill: none;
    stroke: var(--text-faint);
    stroke-width: 2;
    stroke-linecap: round;
  }

  .search input {
    width: 11rem;
    border: none;
    background: none;
    color: var(--text);
    font-family: inherit;
    font-size: 0.85rem;
    padding: 0.25rem 0;
    transition: width 0.25s var(--ease);
  }

  .search input:focus {
    outline: none;
    width: 14rem;
  }

  .search input::placeholder {
    color: var(--text-faint);
  }

  .logout-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-pill);
    background: none;
    color: var(--text-dim);
    font-family: inherit;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: color 0.2s var(--ease), border-color 0.2s var(--ease),
      background 0.2s var(--ease);
  }

  .logout-btn:hover {
    color: var(--text);
    border-color: var(--text-dim);
    background: rgba(255, 255, 255, 0.06);
  }

  .menu-toggle {
    display: none;
    flex-direction: column;
    gap: 4px;
    padding: 0.5rem;
    margin-left: auto;
    border: none;
    background: none;
    cursor: pointer;
  }

  .menu-toggle span {
    display: block;
    width: 20px;
    height: 2px;
    border-radius: 2px;
    background: var(--text);
  }

  /* Below this width the seven links cannot fit beside the search box, so they
     collapse behind a toggle instead of wrapping into an unreadable pile. */
  @media (max-width: 1100px) {
    .menu-toggle { display: flex; }

    .nav-container { flex-wrap: wrap; }

    .navbar-nav,
    .navbar-right {
      display: none;
      width: 100%;
    }

    .navbar-nav.open,
    .navbar-right.open {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      padding-top: 0.75rem;
    }

    .search { flex: 1; }
    .search input,
    .search input:focus { width: 100%; }
  }
</style>
