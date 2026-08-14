<!--
  A cast/crew tile: headshot, name, and the role they played.

  Deliberately a different shape from MovieCard - a 1:1 portrait rather than a
  2:3 poster - so a cast row is instantly distinguishable from a movie row when
  scanning the page, without needing to read the heading.
-->
<script>
  export let actor_id;
  export let name;
  export let profile_path = null;
  export let role = "";
  export let href = null;

  const IMG = "https://image.tmdb.org/t/p/w185";

  $: src = profile_path ? `${IMG}${profile_path}` : null;
  $: target = href ?? `/components/Actor?actor_id=${actor_id}`;
  // Initials stand in when TMDb has no headshot, which is common further down
  // a cast list.
  $: initials = (name || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
</script>

<a class="person" href={target} aria-label={role ? `${name} as ${role}` : name}>
  <div class="portrait">
    {#if src}
      <img {src} alt={name} loading="lazy" decoding="async" />
    {:else}
      <div class="initials" aria-hidden="true">{initials}</div>
    {/if}
  </div>

  <div class="meta">
    <span class="name">{name}</span>
    {#if role}<span class="role">{role}</span>{/if}
  </div>
</a>

<style>
  .person {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    text-decoration: none;
    color: inherit;
    text-align: center;
    min-width: 0;
    transition: transform 0.25s var(--ease);
  }

  .person:hover,
  .person:focus-visible {
    transform: translateY(-4px);
  }

  .portrait {
    position: relative;
    aspect-ratio: 1 / 1;
    border-radius: var(--radius-pill);
    overflow: hidden;
    background: var(--surface-2);
    border: 2px solid transparent;
    transition: border-color 0.25s var(--ease), box-shadow 0.25s var(--ease);
  }

  .person:hover .portrait,
  .person:focus-visible .portrait {
    border-color: var(--accent);
    box-shadow: var(--shadow);
  }

  .portrait img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    /* Headshots are framed for the face; pulling the crop upward avoids
       cutting off foreheads in a circular mask. */
    object-position: center 20%;
  }

  .initials {
    width: 100%;
    height: 100%;
    display: grid;
    place-items: center;
    background: linear-gradient(160deg, var(--surface-3), var(--surface));
    color: var(--text-faint);
    font-size: 1.4rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  .meta {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    min-width: 0;
  }

  .name {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .role {
    font-size: 0.72rem;
    color: var(--text-faint);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
